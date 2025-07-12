#!/usr/bin/env python3
"""Wrapper for async agent main script."""

import asyncio

from agent.main import main


def sync_main():
    """Synchronous wrapper for async main."""
    asyncio.run(main())


if __name__ == "__main__":
    sync_main()
