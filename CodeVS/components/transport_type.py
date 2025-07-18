from enum import Enum

class TransportType(Enum):
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    
# Convert string to enum using value
def str_to_enum(value: str):
    try:
        return TransportType(value.upper())
    except ValueError:
        return None  # Handle invalid values