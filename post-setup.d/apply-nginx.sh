#!/bin/bash
# Apply custom nginx config after Puppet has run
if [ -f /opt/custom_nginx/zulip-include/app ]; then
    echo "Applying custom nginx configuration..."
    cp -f /opt/custom_nginx/zulip-include/app /etc/nginx/zulip-include/app
    nginx -t && nginx -s reload 2>/dev/null || true
    echo "Custom nginx config applied."
fi
