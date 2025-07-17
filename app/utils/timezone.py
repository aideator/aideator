"""
Timezone utilities for handling user-specific timezone display.

This module provides utilities for converting UTC timestamps to user-specific
timezones. Currently hardcoded to CST but designed to support user preferences
in the future.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo


# TODO: Replace with user profile setting when user profiles are implemented
DEFAULT_USER_TIMEZONE = "America/Chicago"  # CST/CDT


def get_user_timezone(user_id: Optional[str] = None) -> ZoneInfo:
    """
    Get the timezone for a specific user.
    
    Currently hardcoded to CST but designed to be replaced with
    user profile lookup when user profiles are implemented.
    
    Args:
        user_id: User ID (currently unused, for future implementation)
        
    Returns:
        ZoneInfo object for the user's timezone
    """
    # TODO: When user profiles are implemented, replace with:
    # user_profile = get_user_profile(user_id)
    # return ZoneInfo(user_profile.timezone)
    return ZoneInfo(DEFAULT_USER_TIMEZONE)


def utc_to_user_timezone(utc_datetime: datetime, user_id: Optional[str] = None) -> datetime:
    """
    Convert UTC datetime to user's timezone.
    
    Args:
        utc_datetime: Datetime in UTC (can be naive or timezone-aware)
        user_id: User ID for timezone lookup (currently unused)
        
    Returns:
        Datetime converted to user's timezone
    """
    # Ensure the datetime is UTC timezone-aware
    if utc_datetime.tzinfo is None:
        # Assume naive datetime is UTC
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    elif utc_datetime.tzinfo != timezone.utc:
        # Convert to UTC if it's in a different timezone
        utc_datetime = utc_datetime.astimezone(timezone.utc)
    
    # Get user's timezone and convert
    user_tz = get_user_timezone(user_id)
    return utc_datetime.astimezone(user_tz)


def format_user_timestamp(utc_datetime: datetime, user_id: Optional[str] = None, 
                         format_type: str = "full") -> str:
    """
    Format a UTC datetime for display in user's timezone.
    
    Args:
        utc_datetime: Datetime in UTC
        user_id: User ID for timezone lookup (currently unused)
        format_type: Format type ("full", "date", "time", "short")
        
    Returns:
        Formatted timestamp string
    """
    user_datetime = utc_to_user_timezone(utc_datetime, user_id)
    
    if format_type == "full":
        return user_datetime.strftime("%Y-%m-%d %I:%M:%S %p %Z")
    elif format_type == "date":
        return user_datetime.strftime("%Y-%m-%d")
    elif format_type == "time":
        return user_datetime.strftime("%I:%M:%S %p %Z")
    elif format_type == "short":
        return user_datetime.strftime("%m/%d %I:%M %p")
    else:
        return user_datetime.strftime("%Y-%m-%d %I:%M:%S %p %Z")


def get_user_timezone_name(user_id: Optional[str] = None) -> str:
    """
    Get the display name for user's timezone.
    
    Args:
        user_id: User ID for timezone lookup (currently unused)
        
    Returns:
        Human-readable timezone name
    """
    user_tz = get_user_timezone(user_id)
    now = datetime.now(user_tz)
    
    # Get the timezone abbreviation (CST/CDT)
    return now.strftime("%Z")


def utc_to_user_timezone_iso(utc_datetime: datetime, user_id: Optional[str] = None) -> str:
    """
    Convert UTC datetime to user's timezone and return as ISO string.
    
    This is useful for API responses where we want to include timezone info.
    
    Args:
        utc_datetime: Datetime in UTC
        user_id: User ID for timezone lookup (currently unused)
        
    Returns:
        ISO format string with timezone info
    """
    user_datetime = utc_to_user_timezone(utc_datetime, user_id)
    return user_datetime.isoformat()