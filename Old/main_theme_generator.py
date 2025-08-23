#!/usr/bin/env python3
"""
Main Theme Generator Script

Orchestrates the theme generation process using the modular components.
"""

import sys
from pythonThemeTools.theme_data_collector import collect_theme_data, interactive_mode
from pythonThemeTools.theme_configurations import ThemeConfigurations
from pythonThemeTools.theme_renderer import ThemeRenderer


def choose_mode():
    """
    Prompts user to choose between different modes of operation.
    
    Returns:
        str: The chosen mode ('interactive', 'testing', 'batch', 'config')
    """
    print("--- Markdown Theme Generator (Stylist Guild) ---")
    print("\nAvailable modes:")
    print("1. Interactive mode - Enter theme data manually")
    print("2. Testing mode - Use predefined test data") 
    print("3. Batch mode - Process multiple predefined themes")
    print("4. Configuration mode - Choose from specific presets")
    print("5. Exit")
    
    while True:
        choice = input("\nSelect mode (1-5): ").strip()
        if choice == '1':
            return 'interactive'
        elif choice == '2':
            return 'testing'
        elif choice == '3':
            return 'batch'
        elif choice == '4':
            return 'config'
        elif choice == '5':
            print("Exiting Markdown Theme Generator. Goodbye!")
            sys.exit()
        else:
            print("Please enter a number between 1 and 5.")


def run_interactive_mode(renderer):
    """
    Runs the interactive mode where users manually input theme data.
    
    Args:
        renderer (ThemeRenderer): The theme renderer instance
    """
    print("\n=== Interactive Mode ===")
    print("You can type 'exit' at any prompt to quit the application.")
    
    while True:
        try:
            # Collect theme data from user
            theme_data = collect_theme_data()
            
            if theme_data is None:
                break
            
            # Render and save the theme
            success = renderer.render_and_save_theme_markdown(theme_data)
            
            if not success:
                print("Failed to create theme entry. Please try again.")
                continue
            
            # Ask if user wants to create another theme
            another = input("\nWould you like to create another theme? (yes/no): ").lower().strip()
            if another not in ['yes', 'y']:
                break
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue


def run_testing_mode(renderer):
    """
    Runs the testing mode using predefined test data.
    
    Args:
        renderer (ThemeRenderer): The theme renderer instance
    """
    print("\n=== Testing Mode ===")
    
    # Get test theme data
    test_data = ThemeConfigurations.testing_mode()
    
    try:
        # Render and save the test theme
        success = renderer.render_and_save_theme_markdown(test_data)
        
        if success:
            print("Testing mode completed successfully!")
        else:
            print("Testing mode failed!")
            
    except Exception as e:
        print(f"An error occurred during testing: {e}")


def run_batch_mode(renderer):
    """
    Runs the batch mode processing multiple predefined themes.
    
    Args:
        renderer (ThemeRenderer): The theme renderer instance
    """
    print("\n=== Batch Mode ===")
    
    # Get batch themes
    batch_themes = ThemeConfigurations.get_batch_themes()
    
    try:
        # Process all themes in batch
        results = renderer.batch_render_themes(batch_themes)
        
        print(f"\nBatch processing completed!")
        print(f"Results: {results['successful']} successful, {results['failed']} failed")
        
        # Show details if there were failures
        if results['failed'] > 0:
            print("\nFailed themes:")
            for detail in results['details']:
                if detail['status'] != 'success':
                    print(f"  - {detail['theme']}: {detail['message']}")
                    
    except Exception as e:
        print(f"An error occurred during batch processing: {e}")


def run_configuration_mode(renderer):
    """
    Runs the configuration mode allowing users to choose from specific presets.
    
    Args:
        renderer (ThemeRenderer): The theme renderer instance
    """
    print("\n=== Configuration Mode ===")
    
    # List available configurations
    configs = ThemeConfigurations.list_available_configurations()
    print("Available configurations:")
    for i, config in enumerate(configs, 1):
        print(f"{i}. {config}")
    
    while True:
        try:
            choice = input(f"\nSelect configuration (1-{len(configs)}) or 'exit': ").strip()
            
            if choice.lower() == 'exit':
                break
                
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(configs):
                config_name = configs[choice_idx]
                
                if config_name == 'batch':
                    # Special case for batch processing
                    run_batch_mode(renderer)
                else:
                    # Get the specific configuration
                    theme_data = ThemeConfigurations.get_configuration_by_name(config_name)
                    
                    if theme_data:
                        print(f"Using '{config_name}' configuration for theme: '{theme_data['title']}'")
                        success = renderer.render_and_save_theme_markdown(theme_data)
                        
                        if success:
                            print(f"Successfully processed '{config_name}' configuration!")
                        else:
                            print(f"Failed to process '{config_name}' configuration!")
                    else:
                        print(f"Configuration '{config_name}' not found!")
                break
            else:
                print(f"Please enter a number between 1 and {len(configs)}.")
                
        except ValueError:
            print("Please enter a valid number or 'exit'.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")


def main():
    """
    Main function that orchestrates the theme generation process.
    """
    try:
        # Initialize the theme renderer
        renderer = ThemeRenderer()
        print(f"Theme files will be saved within the base directory: '{renderer.base_dir}'")
        
        # Choose and run the appropriate mode
        mode = choose_mode()
        
        if mode == 'interactive':
            run_interactive_mode(renderer)
        elif mode == 'testing':
            run_testing_mode(renderer)
        elif mode == 'batch':
            run_batch_mode(renderer)
        elif mode == 'config':
            run_configuration_mode(renderer)
            
        print("\nTheme generation process completed.")
        
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Goodbye!")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()