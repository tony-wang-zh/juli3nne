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
    tool_type = ToolType.PASTE

@dataclass
class PowderPartConfig(PartConfig):
    tool_type = ToolType.POWDER

@dataclass
class LiquidPartConfig(PartConfig):
    tool_type = ToolType.LIQUID

@dataclass
class SolidPartConfig(PartConfig):
    block_height: float
    initial_u_offset: float
    tool_type = ToolType.SOLID