from __future__ import annotations

from os import listdir
from os.path import isfile, join
from stl import mesh
import stl
import subprocess
import math
import shutil

import numpy as np

from pathlib import Path
from typing import Union

@staticmethod
def find_min_max(obj):
    min_x = max_x = min_y = max_y = min_z = max_z = None
    for p in obj.points:
        if min_x is None:
            min_x = p[stl.Dimension.X]
            max_x = p[stl.Dimension.X]
            min_y = p[stl.Dimension.Y]
            max_y = p[stl.Dimension.Y]
            min_z = p[stl.Dimension.Z]
            max_z = p[stl.Dimension.Z]
        else:
            max_x = max(p[stl.Dimension.X], max_x)
            min_x = min(p[stl.Dimension.X], min_x)
            max_y = max(p[stl.Dimension.Y], max_y)
            min_y = min(p[stl.Dimension.Y], min_y)
            max_z = max(p[stl.Dimension.Z], max_z)
            min_z = min(p[stl.Dimension.Z], min_z)
    return float(min_x), float(max_x), float(min_y), float(max_y), float(min_z), float(max_z)


Z_OFFSET = "z_offset" # also used as key in ini file
X_CENTER = "x_center"
Y_CENTER = "y_center"
EXTRUSION_MULTIPLIER = "extrusion_multiplier"  # also used as key in ini file
STL_PATH = "stl_path"

PRUSA_CMD = "prusa-slicer"
INI_FILE_TEMPLATE = "./prusa_config_file/default_config.ini"
TEMP_INI_FILE_NAME = "temp_config.ini"

class GcodeGenerator:
    BED_CENTER_X = 185
    BED_CENTER_Y = 208

    

    def __init__(self, configs, base_offset):
        self.CONFIGS = configs
        self.ext_multipliers = self.generate_extrusion_multiplier_dict()
        # self.SLIC3R_PATH = '../Slic3r/slic3r.pl'
        self.SLIC3R_PATH = '../opt/Slic3r/slic3r.pl'
        self.BASE_OFFSET = float(base_offset)
        self.INPUT_DIR = './input'
        self.TEMP_DIR = './temp'

    def generate_extrusion_multiplier_dict(self):
        extrusion_multipliers = {}
        for config in self.CONFIGS:
            extrusion_multipliers[config[0]] = config[2]
        return extrusion_multipliers

    def generate_gcode_metadata(self, stl_files):
        first = True
        delta_x = 0
        delta_y = 0
        delta_z = 0
        metadata = []
        for f in stl_files:
            ext_multiplier = self.ext_multipliers[f]
            mesh_ = mesh.Mesh.from_file(self.INPUT_DIR + '/' + f)
            #mesh_.rotate(np.array([1, 1, -1]), np.deg2rad(90))
            #mesh_.save(self.INPUT_DIR + '/' + str(2)+'.stl')
            min_x, max_x, min_y, max_y, min_z, max_z = find_min_max(mesh_)
            center_x = min_x + ((max_x - min_x) / 2)
            center_y = min_y + ((max_y - min_y) / 2)
            if first:
                delta_x = self.BED_CENTER_X - center_x
                delta_y = self.BED_CENTER_Y - center_y
                delta_z = self.BASE_OFFSET - min_z
                first = False
            x_coord = round(center_x + delta_x, 2)
            y_coord = round(center_y + delta_y, 2)
            z_offset = round(min_z + delta_z, 2)
            # metadata.append([f, str(x_coord), str(y_coord), str(z_offset), str(ext_multiplier)])
            metadata.append(
                {
                    STL_PATH: f,
                    X_CENTER: str(x_coord),
                    Y_CENTER: str(y_coord),
                    Z_OFFSET: str(z_offset),
                    EXTRUSION_MULTIPLIER: str(ext_multiplier),
                }
            )
        return metadata

    """
        write the keys and values into a ini file 
        each line in ini file is "<key> = <value>"

        - Matches lines like: key = something  (leading/trailing spaces allowed)
        - Preserves comments/blank/other lines.
        - Replaces the first occurrence of `key`.
        - If `key` is not found, appends it at the end.

        Returns True if an existing line was updated, False if appended.
    """
    @staticmethod
    def write_ini_file(path: Path, keys_and_values: dict[str, str]) -> bool:
        sep = " = "
        p = Path(path)
        lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

        updated = False
        out = []

        for line in lines:
            stripped = line.lstrip()
            # skips lines that are comments
            if stripped.startswith(("#", ";")) or "=" not in line:
                out.append(line)
                continue

            left, right = line.split("=", 1)
            k = left.strip()
            if k in keys_and_values:
                # Preserve newline style (line already includes it if present)
                newline = "\n" if not line.endswith(("\n", "\r\n")) else ""
                line_ending = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                out.append(f"{k}{sep}{keys_and_values[k]}{line_ending or newline}")
                updated = True
            else:
                out.append(line)

        p.write_text("".join(out), encoding="utf-8")
        return updated


    # create a temporary ini file
    # update ini file with z-offset and extrusion offset
    def invoke_slicer(self, meta):
        # create a copy of ini file
        temp_ini_file_path = Path(self.TEMP_DIR, TEMP_INI_FILE_NAME)
        shutil.copy2(INI_FILE_TEMPLATE, temp_ini_file_path)
        # write configs into temp 
        self.write_ini_file(
            temp_ini_file_path, 
            {
                Z_OFFSET: meta[Z_OFFSET],
                EXTRUSION_MULTIPLIER: meta[EXTRUSION_MULTIPLIER]
            }    
        )

        # invoke prusa slicer 
        # prusa-slicer --load test_config.ini --center 185,208 --export-gcode --output test.gcode 1.STL
        # TODO: this need to be configed by user 
        prusa_path = "/Applications/Prusa/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"
        input_path = str(Path(self.INPUT_DIR , meta[STL_PATH]))
        cmd = [
            prusa_path,
            "--load", temp_ini_file_path,
            "--center", f"{meta[X_CENTER]},{meta[Y_CENTER]}",
            "--export-gcode",
            "--output", self.TEMP_DIR, # the output can either be file path or dir, if is dir, gcode name same as stil
            input_path,
        ]
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)

        print("ran prusa-slicer with output:")
        print(res.stdout)       
        print(res.stderr)

        # clean up and remove temp ini file 
        temp_ini_file_path.unlink(missing_ok=True)
    
    def generate_gcode(self):
        stl_files = [f for f in listdir(self.INPUT_DIR) if isfile(join(self.INPUT_DIR, f)) and f[-4:].upper() == ".STL"]

        def numeric_key(x):
            return int(x.split('.')[0])
        stl_files = sorted(stl_files, key=numeric_key)
        metadata = self.generate_gcode_metadata(stl_files)
        print("----- Gcode Metadata -----")
        print(metadata)
        for meta in metadata:
            self.invoke_slicer(meta)

