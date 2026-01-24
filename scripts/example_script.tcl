# Example TCL Script for PyeChat
# This demonstrates how to create a TCL plugin for PyeChat

# Setup procedure - called when the script loads
proc setup {} {
    pyechat_log "Example TCL script loaded!"
    pyechat_log "TCL version: [info patchlevel]"
}

# Teardown procedure - called when the script unloads (optional)
proc teardown {} {
    pyechat_log "Example TCL script unloaded!"
}

# Example procedure that could be called
proc greet {name} {
    pyechat_log "Hello, $name from TCL!"
}

# Available PyeChat commands:
# - pyechat_log <message>             - Print a log message
# - pyechat_send <network> <target> <message>  - Send IRC message

# Example: Auto-respond to specific keywords (demonstration only)
proc handle_message {network target sender message} {
    if {[string match "*tcl*" [string tolower $message]]} {
        pyechat_log "TCL mentioned by $sender in $target on $network"
    }
}

# Test the greet function
greet "PyeChat User"
