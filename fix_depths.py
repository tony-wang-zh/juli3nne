import re
from process_gcode import GcodeProcessor
from configs import *

class GcodeDepthFixer:
	def __init__(self, configs):
		self.CONFIGS = configs
		self.TEMP_DIR = './temp'
		self.NA = 'not+found'

	def reset_e_home_regex(self, search):
		if re.search("^G92 E-?[0-9\.]*.*$", search.rstrip()):
			p = re.compile("G92 E(-?[0-9\.]*).*")
			result = p.search(search)
			return result.group(1)
		else:
			return self.NA

	def move_e_regex(self, search):
		if re.search("^G1.*E-?[0-9\.]*.*$", search.rstrip()):
			p = re.compile("G1.*E(-?[0-9\.]*).*")
			result = p.search(search)
			return result.group(1)
		else:
			return self.NA

	def get_extruder_depth(self, gcode):
		current = 0.0
		home = 0.0
		max_ = 0.0
		for line in gcode:
			reset = self.reset_e_home_regex(line)
			if reset != self.NA:
				home = current - float(reset)
			move = self.move_e_regex(line)
			if move != self.NA:
				current = home + float(move)
			max_ = max(max_, current)
		max_ = round(max_, 5)
		print('Max Extrusion (from init): ' + str(max_))
		return max_

	def write_config(self, configs, i):
		self.CONFIGS[i].initial_u_offset = configs[i].initial_u_offset

	def fix_depths(self):
		configs = self.CONFIGS
		depth_map = {}
		for i in range(0, len(configs)):
			print('------------------------------------------------')
			config = configs[i]
			if get_config_tool_type(config) != ToolType.PASTE:
				print('discrete tool, skipping depth fixing')
				continue

			file_initial = config.stl_file_name.split('.')[0]
			tool = config.tool_index
			initial_depth = config.initial_u_offset
			if tool not in depth_map:
				depth_map[tool] = float(initial_depth)
			else:
				config.initial_u_offset = float(depth_map[tool])
				print('Updating config corresponding to file: ' + str(config.stl_file_name))
				self.write_config(configs, i)
			gcode = open(self.TEMP_DIR + '/' + file_initial + '.gcode', "r")
			depth = self.get_extruder_depth(gcode)
			depth_map[tool] = round((depth_map[tool] + depth), 3)
			print('Updated depth of tool [' + str(tool) + '] = ' + str(depth_map[tool]))
		return self.CONFIGS
