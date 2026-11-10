# Atlas task (image: ohdsi/atlas). Serves the Atlas UI on :8080, proxies /WebAPI/ to the
# WebAPI task through the hub, and publishes :8080 on the hub (-> localhost:8080 on the VM).
start_tunnel "R:127.0.0.1:${HUB_ATLAS_PORT}:127.0.0.1:8080" "127.0.0.1:18081:127.0.0.1:${HUB_WEBAPI_PORT}"

# The image's html is read-only for the random UID: render config-local.js into /tmp and
# serve it from there. Relative WebAPI URL = same origin, works on any forwarded port.
D=/tmp/atlas; mkdir -p $D
WEBAPI_URL=/WebAPI/ envsubst < /usr/share/nginx/html/atlas/js/config-local.js > $D/config-local.js
cat > $D/nginx.conf <<EOF
worker_processes 1;
daemon off;
pid $D/nginx.pid;
error_log stderr warn;
events { worker_connections 256; }
http {
    include /etc/nginx/mime.types;
    access_log off;
    absolute_redirect off;
    client_body_temp_path $D/body;
    proxy_temp_path $D/proxy;
    fastcgi_temp_path $D/fastcgi;
    uwsgi_temp_path $D/uwsgi;
    scgi_temp_path $D/scgi;
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    server {
        listen 8080;
        root /usr/share/nginx/html;
        location = / { return 302 /atlas/; }
        location = /atlas/js/config-local.js { alias $D/config-local.js; }
        location ^~ /WebAPI/ {
            proxy_pass http://127.0.0.1:18081;
            proxy_http_version 1.1;
            proxy_set_header Host \$http_host;
            proxy_read_timeout 600s;
        }
        location ~ ^.*[^/]\$ { try_files \$uri @rewrite; }
        location @rewrite { return 302 \$uri/; }
    }
}
EOF

nginx -e stderr -c $D/nginx.conf &
WEB=$!
sleep 2

if [ "${SELFTEST:-0}" = 1 ]; then
  wget -q -O - http://127.0.0.1:8080/atlas/js/config-local.js | grep -n 'webapi_url = ' \
    && wget -q -O /dev/null http://127.0.0.1:8080/atlas/ && log "SELFTEST_OK"
  kill $WEB; exit 0
fi

log "Atlas serving on :8080"
wait $WEB
log "nginx exited"; exit 1
