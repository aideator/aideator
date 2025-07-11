#!/usr/bin/env python3
"""
Stamp the database with the current alembic migration version.
This is used when the database schema already exists but alembic hasn't been initialized.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config

def main():
    """Stamp the database with the latest migration."""
    # Get the alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Stamp the database with the latest revision
    # Since the database already has all migrations applied (including dropping the name column),
    # we'll stamp it with revision 006
    print("Stamping database with migration 006...")
    command.stamp(alembic_cfg, "006")
    print("Database stamped successfully!")
    
if __name__ == "__main__":
    main()