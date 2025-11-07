import configparser
import os
import sys

class ConfigurationManager:
    def __init__(self, config_file_name="config.ini"):
        self.config = configparser.ConfigParser()
        
        # Determine the base path for the config file
        if getattr(sys, 'frozen', False): # Check if running as a PyInstaller bundle
            # If bundled, config file is next to the executable
            base_path = os.path.abspath(os.path.dirname(sys.executable))
        else:
            # If running as a script, config file is in the parent directory of src
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.config_file_path = os.path.join(base_path, config_file_name)
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_file_path):
            print(f"Config file not found at {self.config_file_path}. Creating default.")
            self._create_default_config()
        self.config.read(self.config_file_path, encoding='utf-8')

    def _create_default_config(self):
        # Default settings if config file doesn't exist
        self.config['NetworkSettings'] = {
            'GatewayIP': '192.168.1.1',
            'PrimaryDNS': '8.8.8.8',
            'SecondaryDNS': '8.8.4.4',
            'InternalServerIP': '192.168.1.254',
            'TestWebsite': 'www.google.com'
        }
        self.config['TestParameters'] = {
            'PingCount': '4',
            'PingTimeout': '1000',
            'TracertMaxHops': '30'
        }
        self.config['DisplaySettings'] = {
            'Language': 'zh_TW'
        }
        self.save_config()

    def get_setting(self, section, key, default=None):
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def set_setting(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save_config(self):
        with open(self.config_file_path, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

# Example usage (for testing purposes, will be removed later)
if __name__ == "__main__":
    # This part assumes config.ini is in the parent directory of src/config_manager.py
    # For actual app, config_file_name might need adjustment or be passed from main.py
    config_manager = ConfigurationManager()
    
    print("Initial Gateway IP:", config_manager.get_setting('NetworkSettings', 'GatewayIP'))
    config_manager.set_setting('NetworkSettings', 'GatewayIP', '192.168.1.254')
    config_manager.save_config()
    print("Updated Gateway IP:", config_manager.get_setting('NetworkSettings', 'GatewayIP'))

    print("Test Website:", config_manager.get_setting('NetworkSettings', 'TestWebsite'))
    config_manager.set_setting('NetworkSettings', 'TestWebsite', 'www.example.com')
    config_manager.save_config()
    print("Updated Test Website:", config_manager.get_setting('NetworkSettings', 'TestWebsite'))

    # Test a new setting
    config_manager.set_setting('NewSection', 'NewKey', 'NewValue')
    config_manager.save_config()
    print("New Setting:", config_manager.get_setting('NewSection', 'NewKey'))
