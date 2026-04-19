from dataclasses import dataclass

# This is util data classes for holding configs for a part (aka a stl file)
# between different py modules 

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