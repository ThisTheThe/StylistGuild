#!/usr/bin/env python3
"""
Theme Configuration Presets

Contains predefined configurations for testing and batch processing.
"""


class ThemeConfigurations:
    """
    Container for various theme data configurations.
    Makes it easy to add new presets and access them programmatically.
    """
    
    @staticmethod
    def get_test_theme():
        """
        Returns predefined test data for testing mode.
        This bypasses all user input prompts.
        
        Returns:
            dict: Test theme data dictionary
        """
        return {
            'title': 'Test Theme',
            'tags_list': ['tag1', 'tag2'],
            'main_screenshot_url': 'https://camo.githubusercontent.com/ea7d35caa775edffbc49421cb7ff85ac85f07ca2a1b82d3ccd7047542d747442/68747470733a2f2f692e696d6775722e636f6d2f6a53546c7052492e706e67',
            'additional_image_urls': [
                'https://camo.githubusercontent.com/633df2f755e2102e43606782a6e2212a4cb553bcc857a552f24857f7681a5f81/68747470733a2f2f692e696d6775722e636f6d2f495775544942662e706e67',
                'https://camo.githubusercontent.com/633df2f755e2102e43606782a6e2212a4cb553bcc857a552f24857f7681a5f81/68747470733a2f2f692e696d6775722e636f6d2f495775544942662e706e67'
            ],
            'repository_link': 'https://github.com/ThisTheThe/MicroMike',
        }
    
    @staticmethod
    def get_minimal_theme():
        """
        Returns a minimal theme configuration for testing basic functionality.
        
        Returns:
            dict: Minimal theme data dictionary
        """
        return {
            'title': 'Minimal Test',
            'tags_list': ['minimal'],
            'main_screenshot_url': 'https://via.placeholder.com/800x600?text=Minimal+Theme',
            'additional_image_urls': [],
            'repository_link': 'https://github.com/example/minimal',
        }
    
    @staticmethod
    def get_complex_theme():
        """
        Returns a complex theme configuration with multiple images and tags.
        
        Returns:
            dict: Complex theme data dictionary
        """
        return {
            'title': 'Complex Multi-Feature Theme',
            'tags_list': ['complex', 'multi_feature', 'dark_theme', 'custom_fonts', 'animations'],
            'main_screenshot_url': 'https://via.placeholder.com/1200x800?text=Complex+Theme+Main',
            'additional_image_urls': [
                'https://via.placeholder.com/600x400?text=Feature+1',
                'https://via.placeholder.com/600x400?text=Feature+2',
                'https://via.placeholder.com/600x400?text=Feature+3',
                'https://via.placeholder.com/600x400?text=Feature+4'
            ],
            'repository_link': 'https://github.com/example/complex-theme',
        }
    
    @staticmethod
    def get_batch_themes():
        """
        Returns a list of themes for batch processing.
        
        Returns:
            list: List of theme data dictionaries
        """
        return [
            {
                'title': 'Batch Theme Alpha',
                'tags_list': ['batch', 'alpha', 'light_theme'],
                'main_screenshot_url': 'https://via.placeholder.com/800x600?text=Alpha+Theme',
                'additional_image_urls': [],
                'repository_link': 'https://github.com/example/alpha-theme',
            },
            {
                'title': 'Batch Theme Beta',
                'tags_list': ['batch', 'beta', 'dark_theme'],
                'main_screenshot_url': 'https://via.placeholder.com/800x600?text=Beta+Theme',
                'additional_image_urls': [
                    'https://via.placeholder.com/400x300?text=Beta+Feature'
                ],
                'repository_link': 'https://github.com/example/beta-theme',
            },
            {
                'title': 'Batch Theme Gamma',
                'tags_list': ['batch', 'gamma', 'colorful'],
                'main_screenshot_url': 'https://via.placeholder.com/800x600?text=Gamma+Theme',
                'additional_image_urls': [],
                'repository_link': 'https://github.com/example/gamma-theme',
            }
        ]
    
    @staticmethod
    def get_special_character_theme():
        """
        Returns a theme with special characters to test edge cases.
        
        Returns:
            dict: Theme data with special characters
        """
        return {
            'title': '80s Neon Retro-Wave!',
            'tags_list': ['retro', 'neon', 'special_chars', '80s'],
            'main_screenshot_url': 'https://via.placeholder.com/800x600?text=80s+Neon+Theme',
            'additional_image_urls': [],
            'repository_link': 'https://github.com/example/80s-neon-theme',
        }
    
    @staticmethod
    def get_configuration_by_name(config_name):
        """
        Returns a specific configuration by name.
        
        Args:
            config_name (str): Name of the configuration to retrieve
            
        Returns:
            dict: Theme data dictionary or None if not found
        """
        configurations = {
            'test': ThemeConfigurations.get_test_theme(),
            'minimal': ThemeConfigurations.get_minimal_theme(),
            'complex': ThemeConfigurations.get_complex_theme(),
            'special_chars': ThemeConfigurations.get_special_character_theme(),
        }
        
        return configurations.get(config_name.lower())
    
    @staticmethod
    def list_available_configurations():
        """
        Returns a list of all available configuration names.
        
        Returns:
            list: List of configuration names
        """
        return ['test', 'minimal', 'complex', 'special_chars', 'batch']
    
    @staticmethod
    def testing_mode():
        """
        Main testing mode function that demonstrates different configurations.
        
        Returns:
            dict: Test theme data
        """
        print("*** TESTING MODE ACTIVATED ***")
        print("Using predefined test data instead of user input.")
        
        # You can easily change which test configuration to use here
        test_data = ThemeConfigurations.get_test_theme()
        print(f"Using test data for theme: '{test_data['title']}'")
        
        return test_data