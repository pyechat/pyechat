"""Chat message logger for PyeChat."""
import os
from datetime import datetime


class ChatLogger:
    """Logs chat messages to disk per network/channel."""
    
    def __init__(self, base_dir="logs"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def _get_log_path(self, network, target):
        """Get the log file path for a network/channel."""
        # Sanitize network and target names for file system
        network_safe = network.replace('/', '_').replace('\\', '_')
        target_safe = target.replace('/', '_').replace('\\', '_').replace('#', '') if target else '_network_'
        
        network_dir = os.path.join(self.base_dir, network_safe)
        os.makedirs(network_dir, exist_ok=True)
        
        return os.path.join(network_dir, f"{target_safe}.log")
    
    def log_message(self, network, target, message, timestamp=None):
        """Log a message to disk."""
        if not message:
            return
        
        log_path = self._get_log_path(network, target)
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Format: [YYYY-MM-DD HH:MM:SS] message
        timestamp_str = timestamp.strftime("[%Y-%m-%d %H:%M:%S]")
        
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp_str} {message}\n")
        except Exception as e:
            print(f"Error logging message: {e}")
    
    def load_logs(self, network, target, max_lines=500):
        """Load recent messages from log file."""
        log_path = self._get_log_path(network, target)
        
        if not os.path.exists(log_path):
            return []
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Return last max_lines messages
            return [line.rstrip('\n') for line in lines[-max_lines:]]
        except Exception as e:
            print(f"Error loading logs: {e}")
            return []
