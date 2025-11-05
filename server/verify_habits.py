#!/usr/bin/env python3
"""Verification script for habit tracking system."""

import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.goals import (
    get_goals_database,
    get_habit_manager,
    get_progress_tracker,
    get_habit_loader,
)
from logging_config import logger


def verify_database():
    """Verify database is initialized and accessible."""
    print("\n=== Verifying Database ===")
    try:
        db = get_goals_database()
        print("✅ Database initialized successfully")
        
        # Test query
        habits = db.fetch_all("SELECT * FROM habits WHERE active = 1")
        print(f"✅ Database query successful ({len(habits)} active habits)")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def verify_habit_loader():
    """Verify habit loader can read JSON config."""
    print("\n=== Verifying Habit Loader ===")
    try:
        loader = get_habit_loader()
        habits = loader.load_default_habits()
        print(f"✅ Loaded {len(habits)} habits from JSON config")
        
        for i, habit in enumerate(habits, 1):
            print(f"   {i}. {habit['name']} ({habit['target_frequency']}x/week at {habit['check_in_time']})")
        
        return True
    except FileNotFoundError:
        print("❌ default_habits.json not found")
        return False
    except Exception as e:
        print(f"❌ Habit loader error: {e}")
        return False


def verify_habit_manager():
    """Verify habit manager can read existing habits."""
    print("\n=== Verifying Habit Manager ===")
    try:
        manager = get_habit_manager()
        habits = manager.list_habits("default_user", active_only=True)
        
        if len(habits) == 0:
            print("⚠️  No habits found in database")
            print("   This is normal on first run - habits will be created on first message")
            return True
        
        print(f"✅ Found {len(habits)} active habits:")
        for habit in habits:
            print(f"   - {habit.name} ({habit.current_frequency}/{habit.target_frequency}x/week)")
        
        return True
    except Exception as e:
        print(f"❌ Habit manager error: {e}")
        return False


def verify_progress_tracker():
    """Verify progress tracker is functional."""
    print("\n=== Verifying Progress Tracker ===")
    try:
        tracker = get_progress_tracker()
        manager = get_habit_manager()
        habits = manager.list_habits("default_user", active_only=True)
        
        if len(habits) == 0:
            print("⚠️  No habits to track progress for (expected on first run)")
            return True
        
        # Get progress for first habit
        habit = habits[0]
        recent_progress = tracker.get_recent_progress(habit.id, days=7)
        
        print(f"✅ Progress tracker functional")
        print(f"   {habit.name}: {len(recent_progress)} entries in last 7 days")
        
        return True
    except Exception as e:
        print(f"❌ Progress tracker error: {e}")
        return False


def verify_all():
    """Run all verification checks."""
    print("=" * 60)
    print("HABIT TRACKING SYSTEM VERIFICATION")
    print("=" * 60)
    
    results = []
    
    results.append(("Database", verify_database()))
    results.append(("Habit Loader", verify_habit_loader()))
    results.append(("Habit Manager", verify_habit_manager()))
    results.append(("Progress Tracker", verify_progress_tracker()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All checks passed! System is ready.")
        return 0
    else:
        print("\n⚠️  Some checks failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(verify_all())

