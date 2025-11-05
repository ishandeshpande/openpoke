"""Habit loader service for loading default habits from JSON config."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from ...logging_config import logger
from ...config import DATA_DIR


class HabitLoader:
    """Loads habit definitions from JSON configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the habit loader.
        
        Args:
            config_path: Path to the JSON config file. If None, uses default path.
        """
        if config_path is None:
            config_path = DATA_DIR / "default_habits.json"
        
        self._config_path = config_path

    def load_default_habits(self) -> List[Dict[str, Any]]:
        """
        Load default habits from the JSON config file.
        
        Returns:
            List of habit dictionaries with format:
                {
                    "name": str,
                    "target_frequency": int,
                    "check_in_time": str,
                    "description": str,
                    "follow_up_delay_minutes": int (optional),
                }
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            ValueError: If config format is invalid
        """
        try:
            with open(self._config_path, 'r') as f:
                config = json.load(f)
            
            if "habits" not in config:
                raise ValueError("Config file must contain a 'habits' key")
            
            habits = config["habits"]
            
            if not isinstance(habits, list):
                raise ValueError("'habits' must be a list")
            
            # Validate each habit
            for i, habit in enumerate(habits):
                self._validate_habit(habit, i)
            
            logger.info(
                f"Loaded {len(habits)} default habits from {self._config_path}"
            )
            
            return habits
        
        except FileNotFoundError:
            logger.error(f"Habit config file not found: {self._config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in habit config file: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid habit config format: {e}")
            raise

    def _validate_habit(self, habit: Dict[str, Any], index: int) -> None:
        """
        Validate a single habit definition.
        
        Args:
            habit: Habit dictionary to validate
            index: Index of the habit in the list (for error messages)
        
        Raises:
            ValueError: If habit format is invalid
        """
        required_fields = ["name", "target_frequency", "check_in_time"]
        
        for field in required_fields:
            if field not in habit:
                raise ValueError(
                    f"Habit at index {index} missing required field: {field}"
                )
        
        # Validate name
        if not isinstance(habit["name"], str) or not habit["name"].strip():
            raise ValueError(f"Habit at index {index} has invalid name")
        
        # Validate target_frequency
        if not isinstance(habit["target_frequency"], int):
            raise ValueError(
                f"Habit at index {index} has invalid target_frequency (must be integer)"
            )
        
        if not 1 <= habit["target_frequency"] <= 7:
            raise ValueError(
                f"Habit at index {index} has invalid target_frequency "
                f"(must be between 1 and 7)"
            )
        
        # Validate check_in_time
        if not isinstance(habit["check_in_time"], str):
            raise ValueError(
                f"Habit at index {index} has invalid check_in_time (must be string)"
            )
        
        check_in_time = habit["check_in_time"]
        if check_in_time != "anytime":
            # Validate HH:MM format
            try:
                parts = check_in_time.split(":")
                if len(parts) != 2:
                    raise ValueError("Must be HH:MM format")
                
                hour, minute = int(parts[0]), int(parts[1])
                
                if not (0 <= hour <= 23):
                    raise ValueError("Hour must be 0-23")
                if not (0 <= minute <= 59):
                    raise ValueError("Minute must be 0-59")
            
            except Exception as e:
                raise ValueError(
                    f"Habit at index {index} has invalid check_in_time format: {e}"
                )
        
        # Validate optional fields
        if "description" in habit and not isinstance(habit["description"], str):
            raise ValueError(
                f"Habit at index {index} has invalid description (must be string)"
            )
        
        if "follow_up_delay_minutes" in habit:
            if not isinstance(habit["follow_up_delay_minutes"], int):
                raise ValueError(
                    f"Habit at index {index} has invalid follow_up_delay_minutes "
                    f"(must be integer)"
                )
            
            if habit["follow_up_delay_minutes"] < 0:
                raise ValueError(
                    f"Habit at index {index} has invalid follow_up_delay_minutes "
                    f"(must be non-negative)"
                )


# Singleton instance
_habit_loader: Optional[HabitLoader] = None


def get_habit_loader() -> HabitLoader:
    """Get the singleton habit loader instance."""
    global _habit_loader
    if _habit_loader is None:
        _habit_loader = HabitLoader()
    return _habit_loader


__all__ = ["HabitLoader", "get_habit_loader"]

