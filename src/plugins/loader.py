"""Plugin loader for PyeChat scripts."""
import os
import sys
import importlib.util
import traceback
try:
    import tkinter
    TCL_AVAILABLE = True
except ImportError:
    TCL_AVAILABLE = False


class PluginLoader:
    """Loads and manages Python and TCL scripts from the scripts directory."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.plugins = {}
        self.tcl_interp = None
        self.scripts_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..', 'scripts'
        ))
        
        # Initialize TCL interpreter if available
        if TCL_AVAILABLE:
            try:
                self.tcl_interp = tkinter.Tcl()
                self._setup_tcl_bridge()
            except Exception as e:
                print(f"Warning: Failed to initialize TCL interpreter: {e}")
                self.tcl_interp = None
    
    def _setup_tcl_bridge(self):
        """Setup TCL commands to bridge back to Python."""
        if not self.tcl_interp:
            return
        
        # Register Python callback for TCL scripts to use
        def pyechat_log(message):
            print(f"[TCL] {message}")
        
        def pyechat_send(network, target, message):
            """Send IRC message from TCL."""
            if network in self.main_window.clients:
                client = self.main_window.clients[network]
                client.send_message(target, message)
        
        # Make Python functions available to TCL
        self.tcl_interp.createcommand('pyechat_log', pyechat_log)
        self.tcl_interp.createcommand('pyechat_send', pyechat_send)
        
    def load_all(self):
        """Load all Python and TCL scripts from the scripts directory."""
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir, exist_ok=True)
            print(f"Created scripts directory: {self.scripts_dir}")
            return
        
        print(f"Loading scripts from: {self.scripts_dir}")
        
        for filename in os.listdir(self.scripts_dir):
            script_path = os.path.join(self.scripts_dir, filename)
            if filename.endswith('.py') and not filename.startswith('_'):
                self.load_script(filename[:-3], script_path)
            elif filename.endswith('.tcl') and not filename.startswith('_'):
                self.load_tcl_script(filename[:-4], script_path)
    
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
    
    def load_tcl_script(self, name, path):
        """Load a single TCL script."""
        if not self.tcl_interp:
            print(f"✗ Cannot load TCL script {name}: TCL interpreter not available")
            return
        
        try:
            with open(path, 'r') as f:
                tcl_code = f.read()
            
            # Execute the TCL script
            self.tcl_interp.eval(tcl_code)
            
            # Check if the script has a setup procedure
            try:
                self.tcl_interp.eval('info procs setup')
                # Call setup if it exists
                self.tcl_interp.eval('setup')
                print(f"✓ Loaded TCL script: {name}")
            except tkinter.TclError:
                print(f"✓ Loaded TCL script: {name} (no setup procedure)")
            
            self.plugins[name] = {'type': 'tcl', 'path': path}
        except Exception as e:
            print(f"✗ Failed to load TCL script {name}: {e}")
            traceback.print_exc()
    
    def unload_script(self, name):
        """Unload a script."""
        if name in self.plugins:
            plugin = self.plugins[name]
            
            # Handle TCL scripts
            if isinstance(plugin, dict) and plugin.get('type') == 'tcl':
                if self.tcl_interp:
                    try:
                        self.tcl_interp.eval('info procs teardown')
                        self.tcl_interp.eval('teardown')
                    except tkinter.TclError:
                        pass  # No teardown procedure
                del self.plugins[name]
                print(f"Unloaded TCL script: {name}")
                return
            
            # Handle Python modules
            if hasattr(plugin, 'teardown'):
                try:
                    plugin.teardown(self.main_window)
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
