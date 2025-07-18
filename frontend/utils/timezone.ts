/**
 * Timezone utilities for frontend timestamp display.
 * 
 * This module provides utilities for converting UTC timestamps to user-specific
 * timezones on the frontend. Currently hardcoded to CST but designed to support
 * user preferences in the future.
 */

// TODO: Replace with user profile setting when user profiles are implemented
const DEFAULT_USER_TIMEZONE = 'America/Chicago'; // CST/CDT
const DEFAULT_TIMEZONE_OFFSET = -6; // CST is UTC-6, CDT is UTC-5 (auto-handled by America/Chicago)

/**
 * Format a date with manual timezone offset.
 * 
 * @param date - Date object (already adjusted for timezone)
 * @param formatType - Format type ("full", "date", "time", "short")
 * @param timezoneOffset - Timezone offset in hours
 * @returns Formatted timestamp string
 */
function formatDateWithOffset(
  date: Date,
  formatType: 'full' | 'date' | 'time' | 'short',
  timezoneOffset: number
): string {
  switch (formatType) {
    case 'full':
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    case 'date':
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      });
    case 'time':
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    case 'short':
      return date.toLocaleString('en-US', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    default:
      return date.toLocaleString('en-US');
  }
}

/**
 * Get the timezone for a specific user.
 * 
 * Currently hardcoded to CST but designed to be replaced with
 * user profile lookup when user profiles are implemented.
 * 
 * @param userId - User ID (currently unused, for future implementation)
 * @param timezoneOffset - Manual timezone offset in hours (optional override)
 * @returns Timezone string (IANA timezone identifier) or offset
 */
export function getUserTimezone(userId?: string, timezoneOffset?: number): string {
  // TODO: When user profiles are implemented, replace with:
  // const userProfile = getUserProfile(userId);
  // return userProfile.timezone;
  
  // If manual offset provided, we'll handle it differently
  if (timezoneOffset !== undefined) {
    // For manual offset, we'll use a different approach
    return DEFAULT_USER_TIMEZONE; // Still return timezone string for now
  }
  
  return DEFAULT_USER_TIMEZONE;
}

/**
 * Convert UTC timestamp to user's timezone.
 * 
 * @param utcTimestamp - UTC timestamp (ISO string or Date object)
 * @param userId - User ID for timezone lookup (currently unused)
 * @returns Date object in user's timezone
 */
export function utcToUserTimezone(utcTimestamp: string | Date, userId?: string): Date {
  const date = utcTimestamp instanceof Date ? utcTimestamp : new Date(utcTimestamp);
  
  // The Date object automatically handles timezone conversion when using
  // toLocaleString with a specific timezone
  return date;
}

/**
 * Format a UTC timestamp for display in user's timezone.
 * 
 * @param utcTimestamp - UTC timestamp (ISO string or Date object)
 * @param userId - User ID for timezone lookup (currently unused)
 * @param formatType - Format type ("full", "date", "time", "short")
 * @param timezoneOffset - Manual timezone offset in hours (optional override)
 * @returns Formatted timestamp string
 */
export function formatUserTimestamp(
  utcTimestamp: string | Date,
  userId?: string,
  formatType: 'full' | 'date' | 'time' | 'short' = 'full',
  timezoneOffset?: number
): string {
  const date = utcTimestamp instanceof Date ? utcTimestamp : new Date(utcTimestamp);
  
  // If manual offset provided, apply it directly
  if (timezoneOffset !== undefined) {
    const adjustedDate = new Date(date.getTime() + (timezoneOffset * 60 * 60 * 1000));
    return formatDateWithOffset(adjustedDate, formatType, timezoneOffset);
  }
  
  const userTimezone = getUserTimezone(userId, timezoneOffset);
  
  const options: Intl.DateTimeFormatOptions = {
    timeZone: userTimezone,
  };
  
  switch (formatType) {
    case 'full':
      return date.toLocaleString('en-US', {
        ...options,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short',
      });
    case 'date':
      return date.toLocaleDateString('en-US', {
        ...options,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      });
    case 'time':
      return date.toLocaleTimeString('en-US', {
        ...options,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short',
      });
    case 'short':
      return date.toLocaleString('en-US', {
        ...options,
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short',
      });
    default:
      return date.toLocaleString('en-US', {
        ...options,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short',
      });
  }
}

/**
 * Get the display name for user's timezone.
 * 
 * @param userId - User ID for timezone lookup (currently unused)
 * @returns Human-readable timezone name (e.g., "CST", "CDT")
 */
export function getUserTimezoneName(userId?: string): string {
  const userTimezone = getUserTimezone(userId);
  const now = new Date();
  
  // Get the short timezone name
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: userTimezone,
    timeZoneName: 'short',
  });
  
  const parts = formatter.formatToParts(now);
  const timeZonePart = parts.find(part => part.type === 'timeZoneName');
  
  return timeZonePart?.value || 'CST';
}

/**
 * Format timestamp for logs display (commonly used pattern).
 * 
 * @param utcTimestamp - UTC timestamp (ISO string or Date object)
 * @param userId - User ID for timezone lookup (currently unused)
 * @param timezoneOffset - Manual timezone offset in hours (optional override, defaults to -6 for CST)
 * @returns Formatted timestamp string for logs
 */
export function formatLogTimestamp(utcTimestamp: string | Date, userId?: string, timezoneOffset: number = -6): string {
  return formatUserTimestamp(utcTimestamp, userId, 'time', timezoneOffset);
}

/**
 * Format timestamp for task cards display (commonly used pattern).
 * 
 * @param utcTimestamp - UTC timestamp (ISO string or Date object)
 * @param userId - User ID for timezone lookup (currently unused)
 * @param timezoneOffset - Manual timezone offset in hours (optional override, defaults to -6 for CST)
 * @returns Formatted timestamp string for task cards
 */
export function formatTaskTimestamp(utcTimestamp: string | Date, userId?: string, timezoneOffset: number = -6): string {
  return formatUserTimestamp(utcTimestamp, userId, 'short', timezoneOffset);
}