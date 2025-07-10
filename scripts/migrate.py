#!/usr/bin/env python3
"""
Database migration script using Alembic.
"""

import sys
import os
import logging
import subprocess
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_alembic_command(command: str, *args) -> int:
    """Run an Alembic command."""
    cmd = ["python", "-m", "alembic", command] + list(args)
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        return result.returncode
    
    except FileNotFoundError:
        logger.error("Alembic not found. Please install alembic: pip install alembic")
        return 1
    except Exception as e:
        logger.error(f"Error running alembic command: {e}")
        return 1


def migrate_up(revision: str = "head") -> int:
    """Run database migrations."""
    logger.info(f"Running migrations to {revision}...")
    return run_alembic_command("upgrade", revision)


def migrate_down(revision: str) -> int:
    """Downgrade database to a specific revision."""
    logger.info(f"Downgrading to {revision}...")
    return run_alembic_command("downgrade", revision)


def show_current_revision() -> int:
    """Show current database revision."""
    logger.info("Current database revision:")
    return run_alembic_command("current")


def show_history() -> int:
    """Show migration history."""
    logger.info("Migration history:")
    return run_alembic_command("history", "--verbose")


def show_pending() -> int:
    """Show pending migrations."""
    logger.info("Pending migrations:")
    return run_alembic_command("heads")


def create_migration(message: str) -> int:
    """Create a new migration."""
    logger.info(f"Creating new migration: {message}")
    return run_alembic_command("revision", "--autogenerate", "-m", message)


def main():
    """Main entry point for migration script."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate.py <command> [args]")
        print()
        print("Commands:")
        print("  up [revision]     - Run migrations (default: head)")
        print("  down <revision>   - Downgrade to revision")
        print("  current          - Show current revision")
        print("  history          - Show migration history")
        print("  pending          - Show pending migrations")
        print("  create <message> - Create new migration")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    # Verify database connection
    try:
        settings = get_settings()
        logger.info(f"Using database: {settings.database_url}")
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        sys.exit(1)
    
    try:
        if command == "up":
            revision = args[0] if args else "head"
            exit_code = migrate_up(revision)
        elif command == "down":
            if not args:
                logger.error("Down command requires a revision argument")
                sys.exit(1)
            exit_code = migrate_down(args[0])
        elif command == "current":
            exit_code = show_current_revision()
        elif command == "history":
            exit_code = show_history()
        elif command == "pending":
            exit_code = show_pending()
        elif command == "create":
            if not args:
                logger.error("Create command requires a message argument")
                sys.exit(1)
            exit_code = create_migration(" ".join(args))
        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()