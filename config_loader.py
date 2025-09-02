import os
import shutil

def load_config():
    config_path = "config.py"
    example_path = "config.example.py"
    
    # Create config.py from example if it doesn't exist
    if not os.path.exists(config_path):
        if os.path.exists(example_path):
            shutil.copy2(example_path, config_path)
            print(f"Created {config_path} from {example_path}")
            print("You can now edit config.py with your personal settings.")
        else:
            raise FileNotFoundError(f"Neither {config_path} nor {example_path} found")
    
    # Import the config module
    try:
        import config
        return config
    except ImportError as e:
        raise ImportError(f"Could not import config: {e}")

# Load configuration
try:
    config = load_config()
except (FileNotFoundError, ImportError):
    raise
