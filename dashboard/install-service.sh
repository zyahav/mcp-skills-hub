#!/bin/bash

# Configuration
SERVICE_LABEL="com.zurielyahav.mcp-dashboard"
PLIST_PATH="$HOME/Library/LaunchAgents/$SERVICE_LABEL.plist"
DASHBOARD_DIR="$(cd "$(dirname "$0")" && pwd)"
NODE_PATH=$(which node)

# Check if node is found
if [ -z "$NODE_PATH" ]; then
    echo "Error: Node.js not found in PATH"
    exit 1
fi

echo "Installing Dashboard Service..."
echo "  - Directory: $DASHBOARD_DIR"
echo "  - Node Path: $NODE_PATH"

# Create plist file
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$SERVICE_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$NODE_PATH</string>
        <string>$DASHBOARD_DIR/server.js</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$DASHBOARD_DIR</string>
    <key>StandardOutPath</key>
    <string>/tmp/$SERVICE_LABEL.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/$SERVICE_LABEL.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "  - Generated plist: $PLIST_PATH"

# Unload previous instance if exists
launchctl unload "$PLIST_PATH" 2>/dev/null

# Load new instance
launchctl load "$PLIST_PATH"

echo "✅ Service Installed & Started!"
echo "Logs available at: /tmp/$SERVICE_LABEL.out.log"
