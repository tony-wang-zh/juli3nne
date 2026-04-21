import os
from configs import *

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

    def __init__(self, configs):
        self.CONFIGS = configs
        self.TEMP_DIR = "./temp"
        self.OUTPUT_DIR = "./output"
        self.TOOL_DIR = "./toolchange/generatedTCgcode"
        self.END_STRING = "G01 Z60.4 F5000\nG01 X0.0 Y200.00 Z80.00 F2000.00" # return to default?

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

    def process_paste_part_gcode(self, config, file, is_last_file):
        print(f"processing gcode from file {file}")
        print(config)

        initial_extruder_depth = config.initial_u_offset
        current_tool_index = config.tool_index
        # next_tool_index = config[4]

        new_str = "" 
        x_move = 0
        cmd_store = ""

        total_dist_moved = 0.0
        do_extrude = 0
        add_extruder_init = True

        new_str += f';;;;;;;;;;;\n; STARTING PART {config.stl_file_name} \n;;;;;;;;;;;\n'
        if self.should_pick_up_tool[config.stl_file_name]:
            new_str += self.get_tool_gcode(current_tool_index, True)

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
                
                # print("debugging")
                # print(initial_extruder_depth)
                # print(total_dist_moved)
                # print(type(initial_extruder_depth))
                # print(type(total_dist_moved))

                if initial_extruder_depth+total_dist_moved > self.U_AXIS_LIMIT:
                    raise ValueError("Tool "+ str(current_tool_index)+ " exceeded maximum extrustion distance")


        end_string = 'G92 E0;\n'

        # retract extrusion 
        end_string += 'G1 E-' + str(round((total_dist_moved + initial_extruder_depth), 3))
        end_string += ' F2000; retract to 0\nG92 E0;\n'

        if self.should_drop_off_tool[config.stl_file_name]:
            drop_tool_gcode = self.get_tool_gcode(current_tool_index, False)
            end_string += drop_tool_gcode

        if is_last_file:
            end_string += self.END_STRING
        else:
            end_string += 'G1 Z75 F1000;\n'+'G28 E0 F1000;;\n'

        end_string += f';;;;;;;;;;;\n; ENDING PART {config.stl_file_name} \n;;;;;;;;;;;\n'

        return new_str + end_string

    def process_liquid_part_gcode(self, config, file, is_last_file):
        pass

    def process_powder_part_gcode(self, config, file, is_last_file):
        pass

    def process_solid_part_gcode(self, config, file, is_last_file):
        pass

    def process_gcode(self, config, gcode_file, last):
        tool_type_for_file = get_config_tool_type(config)
        match tool_type_for_file:
            case ToolType.LIQUID:
                return self.process_liquid_part_gcode(config, gcode_file, last)
            case ToolType.POWDER:
                return self.process_powder_part_gcode(config, gcode_file, last)
            case ToolType.SOLID:
                return self.process_solid_part_gcode(config, gcode_file, last)
            case  _:
                return self.process_paste_part_gcode(config, gcode_file, last)


    def clean_and_concatenate(self):
        gcodes = []
        for i in range(len(self.CONFIGS)):
            config = self.CONFIGS[i]
            last = i == len(self.CONFIGS) - 1
            gcode_file = self.get_gcode_file(config)
            processed_gcode = self.process_gcode(config, gcode_file, last)
            gcodes.append(processed_gcode)
        self.write_output_file(gcodes)
