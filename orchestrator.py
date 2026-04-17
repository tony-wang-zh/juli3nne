import os
import re
# from generate_gcode import GcodeGenerator
from generate_gcode_prusa import GcodeGenerator
from fix_depths import GcodeDepthFixer
# from process_gcode import GcodeProcessor
from process_gcode_prusa import GcodeProcessor
from dataclasses import dataclass


def layer_config_regex(search):
    return re.search("^[0-9][0-9]?\.[Ss][Tt][lL],\s?[0-9][0-9]?,\s?.*,\s?[0-9][0-9]?[0-9]?,?\s?$", search.rstrip())


def offset_regex(search):
    return re.search("^offset\=.*$", search)


class Orchestrator:
    def __init__(self):
        self.INPUT_DIR = './input'
        self.TEMP_DIR = './temp'
        self.OUTPUT_DIR = './output'
        self.flush_dirs()
        self.CONFIGS, self.OFFSET = self.generate_config_and_offset()
        self.CONFIGS, self.OFFSET = self.generate_config_and_offset_tools_compatible()

    def generate_config_and_offset(self):
        f = open(self.INPUT_DIR + "/config.txt", "r")
        layers = [line.rstrip() for line in f if layer_config_regex(line)]
        configs = [[part.rstrip().upper() for part in layer.split(',')] for layer in layers]
        f.close()
        print(configs)
        f = open(self.INPUT_DIR + "/config.txt", "r")
        offset = [line.rstrip() for line in f if offset_regex(line)]
        offset = offset[0].replace('offset=', '')
        return configs, offset

    # to accomendate new tools 
    # is backward compatible with old format (with no tools specification)
    def generate_config_and_offset_tools_compatible(self):
        f = open(self.INPUT_DIR + "/config.txt", "r")

        z_offset = -1
        configs = [] # a list of tuples, backward compatible

        for line in f:
            line_data = line.split("#")[0] # to allow for comments 
            tokens = line_data.strip().lower().split(',')

            if 'stl' in tokens[0]: # stl file lines
                file_name = tokens[0].strip().upper()
                match tokens[1].strip(): # written with match 
                    case 'liquid' | 'powder': 
                        # liquid and powder only has 1 arg, 
                        # off set of print head when spraying 
                        tool_index = int(tokens[2])
                        offset = float(tokens[3])
                        configs.append((file_name, tool_index, offset))
                    case 'solid': 
                        # solid has 2 args 
                        # first is height of block 
                        # second is inital position for U axis based on amount of tube filled
                        tool_index = int(tokens[2])
                        block_height = float(tokens[3])
                        initial_offset = float(tokens[4])
                        configs.append((file_name, tool_index, block_height, initial_offset))
                    case _: # standard aka syringe 
                        tool_index = int(tokens[1])
                        extrusion_multiplier = float(tokens[2])
                        initial_offset = float(tokens[3])
                        configs.append((file_name, tool_index, extrusion_multiplier, initial_offset))
            elif 'offset' in tokens[0]: # global offset line
                z_offset = float(tokens[0].split("=")[-1].strip())
            else:
                raise ValueError(f"unexpected config line: {line.strip()}")

        if z_offset == -1:
            raise ValueError("missing z_offset line")
        
        print(f"config file processed:")
        print(configs)

        return configs, z_offset
            

    def flush_dirs(self):
        if not os.path.exists(self.TEMP_DIR):
            os.makedirs(self.TEMP_DIR)
        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)
        for f in os.listdir(self.TEMP_DIR):
            os.remove(os.path.join(self.TEMP_DIR, f))
        for f in os.listdir(self.OUTPUT_DIR):
            os.remove(os.path.join(self.OUTPUT_DIR, f))

    def run(self):
        step_1 = GcodeGenerator(self.CONFIGS, self.OFFSET)
        step_1.generate_gcode()
        step_2 = GcodeDepthFixer(self.CONFIGS)
        self.CONFIGS = step_2.fix_depths()
        step_3 = GcodeProcessor(self.CONFIGS)
        step_3.clean_and_concatenate()
