from dataclasses import dataclass
from enum import Enum

# This is util data classes for holding configs for a part (aka a stl file)
# between different py modules 

class ToolType(Enum):
    PASTE = 1
    LIQUID = 2
    POWDER = 3
    SOLID = 4

@dataclass
class PartConfig:
    stl_file_name: str
    tool_index: int

@dataclass
class PastePartConfig(PartConfig):
    extrusion_multiplier: float
    initial_u_offset: float

@dataclass
class PowderPartConfig(PartConfig):
    dispense_z_offset: float

@dataclass
class LiquidPartConfig(PartConfig):
    dispense_z_offset: float

@dataclass
class SolidPartConfig(PartConfig):
    block_height: float
    initial_u_offset: float

@staticmethod
def get_config_tool_type(config: PartConfig):
    match config:
        case PowderPartConfig():
            return ToolType.POWDER
        case LiquidPartConfig():
            return ToolType.LIQUID
        case SolidPartConfig():
            return ToolType.SOLID
        case _:
            return ToolType.PASTE