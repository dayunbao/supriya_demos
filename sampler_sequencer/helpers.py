def scale(value: int, target_min: int, target_max: int) -> int:
        """
        Linearly scale a value from one range to another.

        Args:
            source_value (int): The value to be scaled.

        Returns:
            int: The scaled value in the target range.
        """
        source_min = 0
        source_max = 127
        
        scaled_value = (value - source_min) * (target_max - target_min) / (source_max - source_min) + target_min
        return round(number=scaled_value)
    
def scale_float(value: int, target_min: float, target_max: float):
    """
    Linearly scale a value from one range to another.

    Args:
        source_value (float): The value to be scaled.

    Returns:
        float: The scaled value in the target range.
    """
    source_min = 0
    source_max = 127
    
    scaled_value = (value - source_min) * (target_max - target_min) / (source_max - source_min) + target_min
    return round(number=scaled_value, ndigits=2)