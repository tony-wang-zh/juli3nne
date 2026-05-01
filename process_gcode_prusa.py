import os
import typing
import typing
from configs import *
import re

class GcodeProcessor:
    """
    var 'configs' is of the format list of lists
    each 'config' object in 'configs' is a list containing the following elements:
    1. File Name (of the layer to be printed)
    2. Tool Index* (of the material that the layer is expected to be printed with)
    3. Extrusion Multiplier
    4. Initial Extruder Axis Depth
    * Tool indices start from 0
    """
    U_AXIS_LIMIT = 95
    # the offset needed to add to move commands 
    # to cancel the offset of discrete tool center from syringe center 
    # the positive / negative direciton follows direction of machine 
    # which are: 
    # X positive to the right (homed is at MIN x = 0)
    # Y negative to outward (away from wall) (homed is at MAX y = 313)
    # Z negative downward (homed is at MAX z = 175)
    # tuple in (X, Y, Z) order 
    DISCRETE_TOOL_OFFSETS = {
        ToolType.LIQUID: (0, 0, 0),
        ToolType.POWDER: (0, 50, 20),
        ToolType.SOLID: (0, 0, 50), # this is so that the solid tool does not move on the previously printed layer
    }
    # this is how much higher the cutting surface of solid tool is from syringe tip
    # this is written into the DISCRETE_TOOL_OFFSETS for other tools because they already dispense from above the surface
    SOLID_TOOL_TIP_Z_OFFSET = 19 
    SOLID_TOOL_U_LIMIT = 115 # solid tool also has higher u limit than paste

    def __init__(self, configs):
        self.CONFIGS = configs
        self.TEMP_DIR = "./temp"
        self.OUTPUT_DIR = "./output"
        self.TOOL_DIR = "./toolchange/generatedTCgcode"
        self.DISCRETE_TOOL_GCODE_DIR = "./discrete_tool_gcode_files"
        # self.END_STRING = "G01 Z60.4 F5000\nG01 X0.0 Y200.00 Z80.00 F2000.00" # return to default?
        self.END_STRING = "G01 Z160 F1800\nG01 X0.0 Y300.00 Z175.00 F2000.00" # return to default?
        self.FIRST_LAYER_HEIGHT = 0.35

        # re-implemented adaptive tool pick up/drop
        # if two consecutive parts are printed with same tool 
        # no tool change occur 
        self.should_pick_up_tool = {}
        self.should_drop_off_tool = {}
        for i in range(len(configs)):
            should_pick_up_tool = configs[i - 1].tool_index != configs[i].tool_index if i - 1 >= 0 else True
            should_drop_off_tool = configs[i + 1].tool_index != configs[i].tool_index if i + 1 < len(configs) else True

            file_name = configs[i].stl_file_name
            self.should_pick_up_tool[file_name] = should_pick_up_tool
            self.should_drop_off_tool[file_name] = should_drop_off_tool

    def write_output_file(self, gcodes):
        f = open(self.OUTPUT_DIR + '/combined.gcode', "w+")
        for gcode in gcodes:
            gcode_e_is_now_u = gcode.replace("E", "U")
            f.write(gcode_e_is_now_u)
        f.close()

    def get_gcode_file(self, config):
        files = os.listdir(self.TEMP_DIR)
        file = None
        prefix = str(config.stl_file_name[:-4])
        for f_name in files:
            if f_name[-6:].lower() != ".gcode":
                continue
            if f_name[:-6] == prefix:
                file = os.path.join(self.TEMP_DIR, f_name)
                break
        if not file:
            raise FileNotFoundError
        return file

    def get_tool_gcode(self, index, pickup):
        if pickup:
            file = os.path.join(self.TOOL_DIR, "tool_pick_" + str(index) + ".gcode")
        else:
            file = os.path.join(self.TOOL_DIR, "tool_drop_" + str(index) + ".gcode")
        return open(file, "r").read()

    def process_paste_part_gcode(self, config, file):
        initial_extruder_depth = config.initial_u_offset
        current_tool_index = config.tool_index

        new_str = "" 
        x_move = 0
        cmd_store = ""

        total_dist_moved = 0.0
        do_extrude = 0
        add_extruder_init = True

        f = open(file, "r")

        # logic for calculating total extrusion
        # layer always starts at 2 by config 
        # because at end of previous layer 
        # e is moved backed by 2 and that is set as new 0
        LAYER_START_E_VALUE = 2 
        current_layer_last_e_value = LAYER_START_E_VALUE

        for line in f:           
            if len(line) == 0:
                continue
            start = line[0].upper()
            if start == ";" or start == "M":
                continue
            if 'lift nozzle' in line or 'home X axis' in line:
                continue
            if 'G28' in line or 'G21' in line or 'G90' in line: 
                # set unit (inch/cm) and set absolute positioning
                # not needed for our machines
                continue
            if '; lift' in line and 'lift nozzle' not in line:
                continue
          
            # moving to next layer
            # prusa adds a lift line which we skip
            if x_move == 0 and 'G1 Z' in line and 'layer' in line:
                cmd_store = line
                continue

            if x_move == 0 and 'G1 X' in line: # regular move lines 
                new_str = new_str + line + cmd_store
                x_move = 1
                continue

            new_str += line

            # reset extrusion distance lines 
            if 'G92' in line and do_extrude == 0:
                new_str += 'G4 P4000; sleep extra 4s\n'
                do_extrude = 1

            if '; unretract' in line and add_extruder_init:
                to_add = 'M83;\nG01 E' + str(initial_extruder_depth-5) + ';\nG01 E' + str(initial_extruder_depth)
                to_add += ' F50;\nG92 E0;\n'
                new_str += to_add
                add_extruder_init = False
            
            if ';' in line:
                command = line.split(";")[0] # skipping comment 
                if 'E' in command and 'G92' not in command: # regular extrusion line
                    temp = command.split('E')[1] 
                    current_layer_last_e_value = float(temp.split(" ")[0])
            
            # calculate total travel of a layer 
            # and total travel of the pring 
            # end of layer, extrusion reset 
            if '; reset extrusion distance' in line:
                total_extrusion_in_layer = current_layer_last_e_value - LAYER_START_E_VALUE
                total_dist_moved += total_extrusion_in_layer
                current_layer_last_e_value = LAYER_START_E_VALUE
                
                if initial_extruder_depth+total_dist_moved > self.U_AXIS_LIMIT:
                    raise ValueError("Tool "+ str(current_tool_index)+ " exceeded maximum extrustion distance")

        end_string = 'G92 E0;\n'
        # retract extrusion 
        end_string += 'G1 E-' + str(round((total_dist_moved + initial_extruder_depth), 3))
        end_string += ' F2000; retract to 0\nG92 E0;\n'

        return new_str + end_string


    # generate a single solid tool dispense control block 
    # beware that the tool starts at 20 above (z offset) target position 
    # and that the puck is where the final block will be 
    def generate_solid_tool_control_gcode(self, config):
        config = typing.cast(SolidPartConfig, config)
        initial_u_offset = config.initial_u_offset
        block_height = config.block_height
        inital_z_offset = self.DISCRETE_TOOL_OFFSETS[ToolType.SOLID][2]
        # because the solid tool is "shorter" aka the cutting surface is higher than where the synringe tips is 
        # need to move a bit extra to reach the target block surface 
        total_z_move_distance = inital_z_offset - block_height + self.SOLID_TOOL_TIP_Z_OFFSET 

        # slow down when approaching cut position 
        approach_z_move_distance = 10
        fast_z_move_distance = total_z_move_distance  - approach_z_move_distance

        # check if there is enough material 
        if initial_u_offset + block_height >= self.SOLID_TOOL_U_LIMIT:
            raise ValueError(f"exceeding extrusion limit with solid tool at part {config.stl_file_name}")

        file_name = "solid.gcode"
        file = os.path.join(self.DISCRETE_TOOL_GCODE_DIR, file_name)
        gcode = open(file, "r").read()

        gcode = (gcode.replace("{initial_u_offset}", f"{initial_u_offset:.3f}")
                .replace("{block_height}", f"{block_height:.3f}")
                .replace("{total_z_move_distance}", f"{total_z_move_distance:.3f}")
                .replace("{fast_z_move_distance}", f"{fast_z_move_distance:.3f}")
                .replace("{approach_z_move_distance}", f"{approach_z_move_distance:.3f}"))

        # initial u offset need to be increased after each cut 
        config.initial_u_offset += block_height

        return gcode


    # get gcode block to control discrete tools to be spliced in
    def get_discrete_tool_gcode(self, config):
        tool_type = config.tool_type
        if tool_type in  [ToolType.LIQUID, ToolType.POWDER]:
            # liquid and powder control block are static 
            # so just read from file and return
            tool_name = {
                ToolType.LIQUID: "liquid",
                ToolType.POWDER: "powder",
            }[tool_type]
            file_name = tool_name + ".gcode"
            file = os.path.join(self.DISCRETE_TOOL_GCODE_DIR, file_name)
            return open(file, "r").read()
        elif tool_type == ToolType.SOLID:
            # solid tool control gcode are parameterized 
            return self.generate_solid_tool_control_gcode(config)
        else:
            raise NotImplementedError("unexpected else block reached for tool type match case")


    # get gcode from prusa for a discerte 
    # example see discrete_tool_control_stl_files/two_dots_h035_d12.gcode
    # retrive positions from that gcode 
    # then splice in control gcode blocks for tool, depending on which tool it is
    # note that the global Z offset is already taken into consideration when generating the gcode 
    def process_discrete_part_gcode(self, config, file):
        # start of proceed gcode 
        new_gcode = "" 
        f = open(file, "r")

        min_x = float('inf') 
        max_x = float('inf') 
        min_y = float('inf') 
        max_y = float('inf') 
        z = float('inf')

        for line in f:
            # find next dispense position 
            if line[0] == ';':
                continue
            elif 'G1 Z' in line and 'lift' not in line: # find z from move line
                z = float(line.split('Z')[1].split(' ')[0]) - self.FIRST_LAYER_HEIGHT
            elif 'G1 F600.000' in line or 'G1 F600' in line: 
                # this line always appear before layer print start 
                # use as signal to reset xy values
                min_x = float('inf') 
                max_x = float('inf') 
                min_y = float('inf') 
                max_y = float('inf') 
                # z value do not reset because there might be more than one dispense at this z 
            elif 'G1' in line and 'X' in line and 'Y' in line and 'E' in line: # find x y range from extrusion lines
                line_x = float(line.split('X')[1].split(' ')[0])
                line_y = float(line.split('Y')[1].split(' ')[0])
                min_x = line_x if min_x == float('inf') else min(min_x, line_x)
                max_x = line_x if max_x == float('inf') else max(max_x, line_x)
                min_y = line_y if min_y == float('inf') else min(min_y, line_y)
                max_y = line_y if max_y == float('inf') else max(max_y, line_y)
            elif ('; retract' in line 
                and float('inf') not in [min_x, max_x, min_y, max_y, z]): # end of layer, now find xy
                x = round((min_x + max_x) / 2.0, 3)
                y = round((min_y + max_y) / 2.0, 3)
                if abs(x) == float('inf') or abs(y) == float('inf'):
                    raise ValueError('unexpected error found, inf min x or min y for discrete tool')

                print(f"recovered x, y, z = {(x, y, z)}")
                # copy these value when creating offset 
                # because they might need to be used again for another dispense 
                # e.g. ther won't be another z move line in gcode and z shouldn't change 

                x_offset, y_offset, z_offset = self.DISCRETE_TOOL_OFFSETS[config.tool_type]
                move_x = x + x_offset
                move_y = y + y_offset
                move_z = z + z_offset

                # construct new gcode 
                new_gcode += f"G1 X{move_x} Y{move_y} ; move to dispense point\n"
                new_gcode += f"G1 Z{move_z} ; move to dispense point\n"
                new_gcode += self.get_discrete_tool_gcode(config) # config might update between different dispenses for solid tool
                new_gcode += "\n"                
            elif '; disable motors' in line:
                break

        return new_gcode

    # process gcode for a stl file 
    # the start and end for each file is same regardless of tool type
    def process_gcode(self, config, gcode_file, is_last_file):
        print(f"processing gcode from file {gcode_file}")
        print(config)
        
        tool_type_for_file = config.tool_type

         # start and tool pickup  
        gcode = f'\n;;;;;;;;;;;\n; STARTING PART {config.stl_file_name} \n;;;;;;;;;;;\n'
        if self.should_pick_up_tool[config.stl_file_name]:
            gcode += self.get_tool_gcode(config.tool_index, True)
       
        functional_gcode = ""
        match tool_type_for_file:
            case ToolType.LIQUID | ToolType.POWDER | ToolType.SOLID:
                functional_gcode =  self.process_discrete_part_gcode(config, gcode_file)
            case  ToolType.PASTE:
                functional_gcode =  self.process_paste_part_gcode(config, gcode_file)
            case _:
                raise NotImplementedError() 
        gcode += functional_gcode

        # tool drop and ending 
        if self.should_drop_off_tool[config.stl_file_name]:
            gcode += self.get_tool_gcode(config.tool_index, False)

        if is_last_file:
            gcode += self.END_STRING
        else:
            # gcode += 'G1 Z75 F1000;\n'+'G28 E0 F1000;;\n'; # this G1 Z75 line is for right machine, which is not in use rn
            gcode += 'G28 E0 F1000;;\n'
        gcode += f'\n;;;;;;;;;;;\n; ENDING PART {config.stl_file_name} \n;;;;;;;;;;;\n'

        return gcode

    def clean_and_concatenate(self):
        gcodes = []
        for i in range(len(self.CONFIGS)):
            config = self.CONFIGS[i]
            last = i == len(self.CONFIGS) - 1
            gcode_file = self.get_gcode_file(config)
            processed_gcode = self.process_gcode(config, gcode_file, last)
            gcodes.append(processed_gcode)
        self.write_output_file(gcodes)
