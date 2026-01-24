"""Plugin loader for PyeChat scripts."""
import os
import sys
import importlib.util
import traceback


class PluginLoader:
    """Loads and manages Python scripts from the scripts directory."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.plugins = {}
        self.scripts_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..', 'scripts'
        ))
        
    def load_all(self):
        """Load all Python scripts from the scripts directory."""
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir, exist_ok=True)
            print(f"Created scripts directory: {self.scripts_dir}")
            return
        
        print(f"Loading scripts from: {self.scripts_dir}")
        
        for filename in os.listdir(self.scripts_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                script_path = os.path.join(self.scripts_dir, filename)
                self.load_script(filename[:-3], script_path)
    
    def load_script(self, name, path):
        """Load a single Python script."""
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                
                # Initialize the script if it has a setup function
                if hasattr(module, 'setup'):
                    module.setup(self.main_window)
                    print(f"✓ Loaded script: {name}")
                else:
                    print(f"✓ Loaded script: {name} (no setup function)")
                
                self.plugins[name] = module
        except Exception as e:
            print(f"✗ Failed to load script {name}: {e}")
            traceback.print_exc()
    
    def unload_script(self, name):
        """Unload a script."""
        if name in self.plugins:
            module = self.plugins[name]
            if hasattr(module, 'teardown'):
                try:
                    module.teardown(self.main_window)
                except Exception as e:
                    print(f"Error during teardown of {name}: {e}")
            del self.plugins[name]
            if name in sys.modules:
                del sys.modules[name]
            print(f"Unloaded script: {name}")
    
    def reload_script(self, name):
        """Reload a script."""
        if name in self.plugins:
            path = self.plugins[name].__file__
            self.unload_script(name)
            self.load_script(name, path)
