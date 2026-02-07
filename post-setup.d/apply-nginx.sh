#!/bin/bash
# Apply custom nginx config after Puppet has run
if [ -f /opt/custom_nginx/zulip-include/app ]; then
    echo "Applying custom nginx configuration..."
    cp -f /opt/custom_nginx/zulip-include/app /etc/nginx/zulip-include/app
    echo "Custom nginx config applied."
fi

# Add CORS headers to internal uploads location for Merview integration
# Django uses X-Accel-Redirect to serve files via this internal location,
# so CORS headers must be here (not in the user-facing location block)
UPLOADS_CONF="/etc/nginx/zulip-include/app.d/uploads-internal.conf"
if [ -f "$UPLOADS_CONF" ] && ! grep -q "Access-Control-Allow-Origin" "$UPLOADS_CONF"; then
    echo "Adding CORS headers to internal uploads config..."
    sed -i '/location \/internal\/local\/uploads {/,/}/ {
        /include \/etc\/nginx\/zulip-include\/headers;/a\
    add_header Access-Control-Allow-Origin https://merview.com always;\
    add_header Access-Control-Allow-Headers Authorization always;\
    add_header Access-Control-Allow-Methods '\''GET, HEAD, OPTIONS'\'' always;
    }' "$UPLOADS_CONF"
    echo "CORS headers added to internal uploads."
fi

nginx -t && nginx -s reload 2>/dev/null || true
echo "Nginx reload complete."
