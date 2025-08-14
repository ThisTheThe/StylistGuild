#!/usr/bin/env python3
import os
import re
import sys # Import the sys module for exiting the script

import requests
import json
from datetime import datetime
from urllib.parse import quote

markdown_template = """---
title: {title}
tags:
{tags_list_yaml}
---
<div style="theme_page_template_version_1"> </div>

<h1>
    <a href="{repository_link}">{title}</a>
    <sub>By <a href="https://github.com/{author_github_username}">{author_github_username}</a></sub>
</h1>

[{main_screenshot_markdown}]({repository_link})
{images_block_markdown}

<div class="inforow">
    <table>
        <tbody>
            <tr>
                <td><img src="https://img.shields.io/github/stars/{github_user_repo}?color=573E7A&amp;logo=github&amp;style=for-the-badge"></td>
                <td><img src="https://img.shields.io/github/issues/{github_user_repo}?color=573E7A&amp;logo=github&amp;style=for-the-badge"></td>
                <td><img src="https://img.shields.io/github/issues-pr/{github_user_repo}?color=573E7A&amp;logo=github&amp;style=for-the-badge"></td>
                <td><img src="https://img.shields.io/badge/Created%20on-{age_of_theme}-blue?color=573E7A&amp;logo=github&amp;style=for-the-badge"></td>
                <td><img src="https://img.shields.io/github/last-commit/{github_user_repo}?color=573E7A&amp;label=last%20update&amp;logo=github&amp;style=for-the-badge"></td>
            </tr>
        </tbody>
    </table>
</div>
"""

# Define the path to the themes index file for the counter
THEMES_INDEX_FILE = "docs/themes/index.md"
# Define the path to the categories index file
CATEGORIES_FILE = "docs/themes/categories.md"
# Define the default base directory for saving markdown files
# This now defaults to 'docs/themes' to simplify relative paths in categories.md
DEFAULT_BASE_SAVE_DIR = "docs/themes"

# Mapping for tags to category headings
CATEGORY_MAPPING = {
    "underrated_gems": "## Underrated Gems",
    "old_but_gold": "## Old but Gold",
    "new_and_upcoming": "## New and Upcoming",
}

def get_user_input(prompt_text):
    """
    Prompts the user for input and checks if they typed 'exit'.
    If 'exit' is typed, the script terminates.
    """
    user_input = input(prompt_text).strip()
    if user_input.lower() == 'exit':
        print("Exiting Markdown Theme Generator. Goodbye!")
        sys.exit() # Terminate the script
    return user_input

def get_next_counter_value(counter_file_path=THEMES_INDEX_FILE):
    """
    Reads the counter from a specific Markdown file (docs/themes/index.md),
    increments it, and updates the file's content.
    Returns the *new* incremented count.
    Handles file existence and specific content format issues.
    """
    if not os.path.exists(counter_file_path):
        print(f"WARNING: Themes index file '{counter_file_path}' not found. "
              "Please ensure it exists and has the expected counter format. Initializing count to 0.")
        # Create a dummy file with initial content for first run convenience
        os.makedirs(os.path.dirname(counter_file_path), exist_ok=True)
        with open(counter_file_path, 'w', encoding='utf-8') as f:
            f.write("""<p>
    Themes added: 0 / 344
    <progress value="0" max="344"/>
</p>""")
        print(f"Created a dummy '{counter_file_path}' with initial counter.")
        return 0 # Return 0, as it will be incremented to 1 by the user's action
                 # and then the next read will see this updated value.

    try:
        with open(counter_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to find the 'Themes added: count / total' line
        text_line_regex = re.compile(r'(Themes added:\s*)(\d+)(\s*\/\s*)(\d+)', re.IGNORECASE)
        # Regex to find the <progress> tag
        progress_tag_regex = re.compile(r'(<progress\s+value=")(\d+)("\s+max=")(\d+)("\s*\/?>)', re.IGNORECASE)

        text_match = text_line_regex.search(content)
        progress_match = progress_tag_regex.search(content)

        current_count = 0
        total_themes = 0

        if text_match:
            current_count = int(text_match.group(2))
            total_themes = int(text_match.group(4))
        else:
            print(f"WARNING: Could not find 'Themes added: count / total' line in '{counter_file_path}'. "
                  "Please ensure the format is correct. Counter will not be updated.")
            return current_count # Return current_count so it doesn't try to update on a bad parse

        new_count = current_count + 1

        # Replace in text line: use re.sub with a callback to preserve groups
        content = text_line_regex.sub(lambda m: f"{m.group(1)}{new_count}{m.group(3)}{m.group(4)}", content, 1)
        
        # Replace in progress tag: also use re.sub with a callback
        if progress_match:
            content = progress_tag_regex.sub(lambda m: f"{m.group(1)}{new_count}{m.group(3)}{total_themes}{m.group(5)}", content, 1)
        else:
            print(f"WARNING: Could not find '<progress value=\"...\" max=\"...\"/>' tag in '{counter_file_path}'. "
                  "The progress bar will not be updated. This is likely a formatting issue in the file.")

        # Save the updated content back to the file
        with open(counter_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"SUCCESS: Counter in '{counter_file_path}' updated to {new_count}.")
        return new_count

    except ValueError:
        print(f"ERROR: Invalid number format in counter file '{counter_file_path}'. Counter will not be updated.")
        return current_count # Return current_count on parse error
    except Exception as e:
        print(f"ERROR: Failed to update counter in '{counter_file_path}': {e}. Counter will not be updated.")
        return current_count # Generic fallback for other errors

def get_multiline_input(prompt):
    """
    Prompts the user for multi-line input until an empty line is entered.
    Each line is checked for 'exit'.
    """
    print(prompt + " (Press Enter on an empty line to finish, or type 'done' or 'exit' to quit):")
    lines = []
    while True:
        line = get_user_input("") # Use the new get_user_input for each line
        if line.lower() == 'done': # Special keyword to finish multi-line input
            break
        if not line: # Empty line also finishes multi-line input
            break
        lines.append(line)
    return "\n".join(lines)

def extract_github_user_repo(repo_url):
    """
    Extracts 'username/repository' from a GitHub repository URL.
    Returns an empty string if not found.
    """
    match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url, re.IGNORECASE)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return ""

def get_first_letter_info(theme_title):
    """
    Determines the 'Letter' column content and the corresponding directory name
    based on the first character of the theme title.
    Handles alphanumeric and special cases like '80s Neon'.
    Returns a dictionary {'link_char': '$a$', 'dir_name': 'a'}
    """
    first_char = theme_title.strip()[0].lower() if theme_title.strip() else ''
    
    if not first_char or not first_char.isalnum():
        # If title is empty, or starts with a non-alphanumeric character (e.g., '!', '#')
        # Based on example '80s Neon' -> $<a$, _a
        return {'link_char': '$<a$', 'dir_name': '_a'}
    elif first_char.isdigit():
        # If it starts with a digit (e.g., '80s Neon')
        return {'link_char': '$<a$', 'dir_name': '_a'}
    else: # If it starts with an alphabet
        return {'link_char': f'${first_char}$', 'dir_name': first_char}

def custom_table_row_sort_key(row_data):
    """
    Custom sort key for table rows. Sorts by 'Letter' (with _a before a), then by Theme Title.
    row_data is a tuple: (link_char, theme_title, theme_link_path)
    """
    link_char, theme_title, _ = row_data
    
    # Custom order for link_char: '$<a$' should come before '$a$', '$b$' etc.
    # We can use a numerical prefix for sorting
    if link_char == '$<a$':
        letter_sort_value = '00' # Comes first
    else:
        letter_sort_value = link_char.replace('$', '').lower() # e.g., 'a', 'b', etc.
        # Ensure 'a' (01) comes after '00'
        if letter_sort_value.isalpha():
            letter_sort_value = '01' + letter_sort_value

    return (letter_sort_value, theme_title.lower()) # Sort by custom letter value, then by title

def update_categories_file(theme_title, kebab_case_filename, original_tags_list):
    """
    Updates docs/themes/categories.md with the new theme entry if it belongs to
    underrated_gems, old_but_gold, or new_and_upcoming categories.
    Inserts entry alphabetically within its section.
    """
    print(f"\nAttempting to update {CATEGORIES_FILE}...")
    
    # Read existing content
    categories_lines = []
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
            categories_lines = f.read().splitlines() 
    else:
        print(f"WARNING: '{CATEGORIES_FILE}' not found. Creating a default structure.")
        # Create a basic file structure with all headings and empty tables
        for heading_text in CATEGORY_MAPPING.values():
            categories_lines.append(heading_text)
            categories_lines.append("") # One blank line after heading
            categories_lines.append("|Letter|Theme|")
            categories_lines.append("|---|---|")
            categories_lines.append("") # One blank line after table separator
        os.makedirs(os.path.dirname(CATEGORIES_FILE), exist_ok=True)

    parsed_sections = {}
    current_section_heading = None
    
    for heading_text in CATEGORY_MAPPING.values():
        parsed_sections[heading_text] = []

    # Parse existing content into structured data
    i = 0
    while i < len(categories_lines):
        line = categories_lines[i].strip()
        
        is_category_heading = False
        for heading_text in CATEGORY_MAPPING.values():
            if line == heading_text:
                current_section_heading = heading_text
                is_category_heading = True
                break
        
        if is_category_heading:
            i += 1 # Move past the heading line
            # Consume blank lines after heading (if any)
            while i < len(categories_lines) and not categories_lines[i].strip():
                i += 1
            
            # Consume table header and separator (checking current line and next)
            if i < len(categories_lines) and categories_lines[i].strip() == "|Letter|Theme|":
                i += 1 
                if i < len(categories_lines) and categories_lines[i].strip() == "|---|---|":
                    i += 1 
            
            # Now, read table rows until next heading or blank line or EOF
            while i < len(categories_lines) and categories_lines[i].strip().startswith('|'):
                # Skip the table header and separator lines themselves if they somehow recur within rows
                if categories_lines[i].strip() == "|Letter|Theme|" or categories_lines[i].strip() == "|---|---|":
                    i += 1
                    continue 
                
                full_row_markdown = categories_lines[i].rstrip() # Store original line without trailing newline
                
                # Extract content for sorting from the row.
                cells = [cell.strip() for cell in re.split(r'(?<!\\)\|', full_row_markdown)][1:-1]
                if len(cells) >= 2:
                    letter_col_content = cells[0].strip()
                    theme_col_content = cells[1].strip()
                    
                    theme_title_in_row_match = re.search(r'\[([^\]]+)\]', theme_col_content)
                    row_theme_title = theme_title_in_row_match.group(1) if theme_title_in_row_match else theme_col_content
                    
                    if current_section_heading: # Only add if we have a valid heading context
                        parsed_sections[current_section_heading].append((letter_col_content, row_theme_title, full_row_markdown))
                i += 1
            # Consume blank lines after table (if any) until next content or EOF
            while i < len(categories_lines) and not categories_lines[i].strip():
                i += 1
            continue 

        i += 1 

    # Construct the new theme entry tuple
    letter_info = get_first_letter_info(theme_title)
    link_char = letter_info['link_char']
    dir_name = letter_info['dir_name']
    
    # Relative path from categories.md to the theme file
    theme_file_relative_path = os.path.join("./", dir_name, kebab_case_filename)
    new_entry_markdown_row = f"|{link_char}|[{theme_title}]({theme_file_relative_path})|"
    new_entry_tuple = (link_char, theme_title, new_entry_markdown_row)

    # Add the new entry to the appropriate category lists in parsed_sections
    added_to_any_category = False
    for tag_key, heading_text in CATEGORY_MAPPING.items():
        if tag_key in original_tags_list:
            parsed_sections[heading_text].append(new_entry_tuple)
            added_to_any_category = True
            print(f"Prepared to add '{theme_title}' to '{heading_text}' section.")

    if not added_to_any_category:
        print(f"No relevant category tags found for '{theme_title}'. Not updating '{CATEGORIES_FILE}'.")
        return 

    # Reconstruct the full content of categories.md with sorted rows
    final_categories_content_lines = []
    
    for heading_text in CATEGORY_MAPPING.values():
        final_categories_content_lines.append(heading_text)
        final_categories_content_lines.append("") # One blank line after heading
        final_categories_content_lines.append("|Letter|Theme|")
        final_categories_content_lines.append("|---|---|")

        # Sort and add rows for this section
        sorted_rows_for_section = sorted(parsed_sections[heading_text], key=custom_table_row_sort_key)
        for row_tuple in sorted_rows_for_section:
            final_categories_content_lines.append(row_tuple[2]) 

        final_categories_content_lines.append("") # One blank line after table
        
    # Join all parts to form the final content.
    # The `filter(None, ...)` and `strip()` is used at the very end to
    # clean up any unintended leading/trailing/multiple blank lines,
    # ensuring only necessary newlines are present.
    final_categories_content = "\n".join(line for line in final_categories_content_lines if line is not None).strip()
    
    # Ensure a single trailing newline at the very end of the file for good measure
    if final_categories_content and not final_categories_content.endswith('\n'):
        final_categories_content += '\n'

    try:
        with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
            f.write(final_categories_content)
        print(f"SUCCESS: '{CATEGORIES_FILE}' updated for '{theme_title}'.")
    except IOError as e:
        print(f"ERROR: Could not save '{CATEGORIES_FILE}': {e}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while writing to '{CATEGORIES_FILE}': {e}")

def get_repo_creation_date(repo_url, token=None):
    """
    Fetch repository creation date from GitHub API.
    
    Args:
        username (str): GitHub username or organization
        repo_name (str): Repository name
        token (str, optional): GitHub personal access token for higher rate limits
    
    Returns:
        dict: Contains original date, formatted dates, and URL-encoded versions
    """
    
    url = f"https://api.github.com/repos/{repo_url}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Creation-Date-Fetcher"
    }
    
    # Add authorization if token provided
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        repo_data = response.json()
        created_at = repo_data["created_at"]
        
        # Parse the datetime
        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        # Format options
        formats = {
            'iso_date': dt.strftime('%Y-%m-%d'),
            'readable': dt.strftime('%B %Y'),
            'short': dt.strftime('%b %Y'),
            'year_only': dt.strftime('%Y'),
            'full_readable': dt.strftime('%B %d, %Y'),
            'compact': dt.strftime('%m/%y')
        }
        
        # URL-encoded versions for shields.io
        encoded_formats = {
            f"{key}_encoded": quote(value)
            for key, value in formats.items()
        }
        
        return {
            'raw_date': created_at,
            'datetime_obj': dt,
            'repo_info': {
                'name': repo_data['name'],
                'full_name': repo_data['full_name'],
                'description': repo_data.get('description', '')
            },
            **formats,
            **encoded_formats
        }
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise ValueError(f"Repository {repo_url} not found")
        elif response.status_code == 403:
            raise ValueError("Rate limit exceeded. Consider using a GitHub token.")
        else:
            raise ValueError(f"GitHub API error: {e}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Network error: {e}")
    except KeyError:
        raise ValueError("Unexpected API response format")



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


def render_and_save_theme_markdown(theme_data):
    """
    Takes theme data dictionary and renders the markdown template,
    then saves it to the specified file path.
    
    Args:
        theme_data (dict): Dictionary containing all theme data from collect_theme_data()
    
    Returns:
        bool: True if successful, False if failed
    """
    
    # Extract data from the dictionary
    title = theme_data['title']
    tags_list = theme_data['tags_list']
    main_screenshot_url = theme_data['main_screenshot_url']
    additional_image_urls = theme_data['additional_image_urls']
    repository_link = theme_data['repository_link']
    
    # Process and format the data
    # Format tags for YAML: each tag on a new line with '- ' prefix and 2-space indent
    tags_list_yaml = "\n".join([f"  - {tag}" for tag in tags_list]) if tags_list else ""
    
    main_screenshot_markdown = f"![{title} Theme Screenshot]({main_screenshot_url})"
    
    # Process additional images
    images_block_markdown = ""
    if additional_image_urls:
        table_cells = ""
        for url in additional_image_urls:
            table_cells += f'    <td><img src="{url}" alt="Additional Screenshot" style="max-width: 200px; height: auto;"></td>\n'
        
        html_table = f'<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">\n  <tr>\n{table_cells}  </tr>\n</table>'
        images_block_markdown = html_table
    
    # Process GitHub repository info
    github_user_repo = extract_github_user_repo(repository_link) if repository_link else ""
    
    date_info = get_repo_creation_date(github_user_repo)
    age_of_theme = f"{date_info['readable']}"
    
    # Extract author_github_username from github_user_repo
    author_github_username = github_user_repo.split('/')[0] if github_user_repo else "N/A"
    
    # --- 5. Determine default save directory based on first letter of title ---
    first_letter_info = get_first_letter_info(title)
    first_letter_dir = first_letter_info['dir_name']  # e.g., 'a' or '_a'
    
    default_letter_subdir_path = os.path.join(DEFAULT_BASE_SAVE_DIR, first_letter_dir)
    
    current_full_save_dir = default_letter_subdir_path
    
    # --- 6. Generate filename in kebab-case based solely on title ---
    sanitized_title_kebab_case = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    suggested_filename = f"{sanitized_title_kebab_case}.md"
    
    output_filename_base = suggested_filename
    
    full_output_filepath = os.path.join(current_full_save_dir, output_filename_base)

    # Ensure the entire directory path exists before saving
    os.makedirs(current_full_save_dir, exist_ok=True)
    print(f"Saving to: '{current_full_save_dir}'")

    # --- Fill the template with all collected and derived data ---
    try:
        final_markdown_content = markdown_template.format(
            title=title,
            tags_list_yaml=tags_list_yaml,
            images_block_markdown=images_block_markdown,
            github_user_repo=github_user_repo,
            repository_link=repository_link,
            author_github_username=author_github_username,
            main_screenshot_markdown=main_screenshot_markdown,
            age_of_theme=age_of_theme
        )
    except KeyError as e:
        print(f"ERROR: Missing data for template placeholder: {e}. Please ensure all prompts are answered.")
        return False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while formatting the template: {e}")
        return False

    # --- Save the combined content to the specified Markdown file ---
    try:
        with open(full_output_filepath, 'w', encoding='utf-8') as f:
            f.write(final_markdown_content)
        print(f"\nSuccessfully created '{full_output_filepath}'!")
        print("--- Content Preview (first 20 lines) ---")
        print("\n".join(final_markdown_content.split('\n')[:20]))
        print("...")
        print("-----------------------")
        
        # --- IMPORTANT: Update the categories file ONLY if theme file generation was successful ---
        # Pass the original tags list to check which categories it belongs to
        update_categories_file(title, suggested_filename, tags_list)
        
        # --- Update the global themes counter ONLY if all operations (theme file + categories) were successful ---
        get_next_counter_value()
        
        return True

    except IOError as e:
        print(f"ERROR: Could not save file to '{full_output_filepath}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during file save or counter update: {e}")
        return False


def get_test_theme_data():
    """
    Returns predefined test data for testing mode.
    This bypasses all user input prompts.
    
    Returns:
        dict: Test theme data dictionary
    """
    # Determine test file paths based on first letter
    
    return {
        'title': 'Test',
        'tags_list': ['tag1', 'tag2'],
        'main_screenshot_url': 'https://camo.githubusercontent.com/ea7d35caa775edffbc49421cb7ff85ac85f07ca2a1b82d3ccd7047542d747442/68747470733a2f2f692e696d6775722e636f6d2f6a53546c7052492e706e67',
        'additional_image_urls': [
            'https://camo.githubusercontent.com/633df2f755e2102e43606782a6e2212a4cb553bcc857a552f24857f7681a5f81/68747470733a2f2f692e696d6775722e636f6d2f495775544942662e706e67',
            'https://camo.githubusercontent.com/633df2f755e2102e43606782a6e2212a4cb553bcc857a552f24857f7681a5f81/68747470733a2f2f692e696d6775722e636f6d2f495775544942662e706e67'
        ],
        'repository_link': 'https://github.com/ThisTheThe/MicroMike',
    }


def create_markdown_theme_entry(testing_mode=None):
    """
    Main function that continuously creates new Markdown theme entries based on user input
    until the user types 'exit' for the title.
    Uses collect_theme_data() to gather input and render_and_save_theme_markdown() to process and save.
    
    Args:
        testing_mode (bool, optional): If True, uses predefined test data instead of prompting user.
                                     If None, prompts user to choose.
    """
    print("--- Markdown Theme Generator (Stylist Guild) ---")
    
    # If testing_mode is not specified, prompt the user
    if testing_mode is None:
        while True:
            mode_choice = input("Do you want to activate testing mode? (yes/no): ").lower().strip()
            if mode_choice in ['yes', 'y']:
                testing_mode = True
                break
            elif mode_choice in ['no', 'n']:
                testing_mode = False
                break
            else:
                print("Please enter 'yes' or 'no'.")
    
    if testing_mode:
        print("*** TESTING MODE ACTIVATED ***")
        print("Using predefined test data instead of user input.")
    else:
        print("You can type 'exit' at any prompt to quit the application.")
    
    # Ensure the default base directory exists once at the start
    os.makedirs(DEFAULT_BASE_SAVE_DIR, exist_ok=True)
    print(f"All theme files will be saved within the base directory: '{DEFAULT_BASE_SAVE_DIR}'")

    while True:
        try:
            if testing_mode:
                # Use predefined test data
                theme_data = get_test_theme_data()
                print(f"Using test data for theme: '{theme_data['title']}'")
            else:
                # Collect all theme data from user
                theme_data = collect_theme_data()
                
                if theme_data is None:
                    # User chose to exit
                    break
            
            # Render and save the theme markdown
            success = render_and_save_theme_markdown(theme_data)
            
            if not success:
                print("Failed to create theme entry. Please try again.")
                if testing_mode:
                    break  # Exit testing mode on failure
                continue
            
            if testing_mode:
                print("Testing mode completed successfully!")
                break  # Exit after one successful test run
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            if testing_mode:
                break  # Exit testing mode on error
            continue

if __name__ == "__main__":
    # Ensure the directories for the counter file and categories file exist.
    os.makedirs(os.path.dirname(THEMES_INDEX_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(CATEGORIES_FILE), exist_ok=True) # Ensure docs/themes exists for categories.md
    
    create_markdown_theme_entry()
