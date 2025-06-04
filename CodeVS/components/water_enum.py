from enum import Enum

class WaterBody(Enum):
    SEA = "SEA"
    RIVER = "RIVER"
    
# Convert string to enum using value
def str_to_enum(value: str):
    try:
        return WaterBody(value)
    except ValueError:
        return None  # Handle invalid values