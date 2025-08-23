#!/usr/bin/env python3
"""
Theme Data Collection Module

Handles user input prompts for collecting theme data interactively.
"""

import sys


def get_user_input(prompt_text):
    """
    Prompts the user for input and checks if they typed 'exit'.
    If 'exit' is typed, the script terminates.
    """
    user_input = input(prompt_text).strip()
    if user_input.lower() == 'exit':
        print("Exiting Markdown Theme Generator. Goodbye!")
        sys.exit()  # Terminate the script
    return user_input


def get_multiline_input(prompt):
    """
    Prompts the user for multi-line input until an empty line is entered.
    Each line is checked for 'exit'.
    """
    print(prompt + " (Press Enter on an empty line to finish, or type 'done' or 'exit' to quit):")
    lines = []
    while True:
        line = get_user_input("")  # Use the new get_user_input for each line
        if line.lower() == 'done':  # Special keyword to finish multi-line input
            break
        if not line:  # Empty line also finishes multi-line input
            break
        lines.append(line)
    return "\n".join(lines)


def collect_theme_data():
    """
    Collects all theme data from user input prompts.
    Returns a dictionary containing all the necessary data for theme generation,
    or None if user exits.
    """
    print("\n--- New Theme Entry ---")
    
    # --- 1. Get the title first to check for exit condition ---
    title = get_user_input("Enter the Theme Title: ")
    # No need for manual 'exit' check here, get_user_input handles sys.exit()

    # --- 2. Prompts for YAML Front Matter and Main Screenshot ---
    # Tags input for YAML list format
    raw_tags_input = get_user_input("Enter Tags (comma-separated, e.g., dark_theme, custom_fonts): ")
    tags_list = [tag.strip() for tag in raw_tags_input.split(',') if tag.strip()]
    
    main_screenshot_url = get_user_input("Enter URL for Main Theme Screenshot: ")

    # --- 3. Prompts for Additional Image Lines and construct combined image block ---
    additional_image_urls = []
    add_more_images = get_user_input("Add more image links (e.g., ![]()) after the main screenshot? (yes/no): ").lower()
    if add_more_images == 'yes':
        print("Enter details for additional images (type 'done' when finished):")
        while True:
            src_url = get_user_input("  Enter image URL: ")
            if src_url.lower() == 'done':
                break
            if src_url:  # Only add if URL is provided
                additional_image_urls.append(f"{src_url}")
            else:
                print("  Image URL cannot be empty. Skipping this image.")
                break  # Exit the loop if no URL is provided

    # --- 4. Prompts for 'Info' Table ---
    repository_link = get_user_input("Enter GitHub Repository Link (e.g., https://github.com/user/repo): ")
    
    # Return all collected data as a dictionary
    return {
        'title': title,
        'tags_list': tags_list,
        'main_screenshot_url': main_screenshot_url,
        'additional_image_urls': additional_image_urls,
        'repository_link': repository_link,
    }


def interactive_mode():
    """
    Main interactive mode function that continuously creates new theme entries
    until the user exits.
    """
    print("You can type 'exit' at any prompt to quit the application.")
    
    while True:
        try:
            # Collect all theme data from user
            theme_data = collect_theme_data()
            
            if theme_data is None:
                # User chose to exit
                break
                
            return theme_data
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"An unexpected error occurred during data collection: {e}")
            continue