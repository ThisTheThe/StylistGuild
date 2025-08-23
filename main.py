#!/usr/bin/env python3
"""
Obsidian Theme Tools - Main Entry Point

Provides unified access to both legacy and new batch processing tools.
"""

import sys
import os

# Add pythonThemeTools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pythonThemeTools'))

def main():
    print("=== Obsidian Theme Tools ===")
    print("1. Legacy Theme Generator (Interactive)")
    print("2. Batch Theme Processor (New)")
    print("3. Exit")
    
    while True:
        choice = input("\nSelect tool (1-3): ").strip()
        
        if choice == '1':
            from legacy.main_theme_generator import main as legacy_main
            legacy_main()
            break
        elif choice == '2':
            from batch_processor.main import main as batch_main
            batch_main()
            break
        elif choice == '3':
            print("Goodbye!")
            sys.exit()
        else:
            print("Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()