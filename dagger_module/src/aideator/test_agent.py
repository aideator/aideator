#!/usr/bin/env python3
"""Test agent that outputs simple messages."""

import time
import sys

def main():
    print("Test agent starting...")
    sys.stdout.flush()
    
    for i in range(5):
        print(f"Test output {i + 1}")
        sys.stdout.flush()
        time.sleep(1)
    
    print("Test agent completed!")
    sys.stdout.flush()

if __name__ == "__main__":
    main()