"""A module with some helper functions.

Copyright 2025, Andrew Clark

This program is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by 
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version.

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License 
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
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