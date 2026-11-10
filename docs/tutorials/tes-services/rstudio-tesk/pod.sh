# Runs inside the TES pod (image rocker/rstudio): random UID, read-only image,
# outbound HTTPS only, no curl. tes-service.sh prepends ../tes-hub/common.sh
# (set -u, log, start_tunnel) and passes service.conf as environment.

# The image's /init (s6) needs root, so start rserver directly as the pod user.
# Its passwd home is "/" (not writable): give R a home under /tmp. Data is lost when the
# task ends (this TESK does not start tasks that request disk_gb).
USER="$(id -un)"; export HOME=/tmp/home USER
RS=/tmp/rs; mkdir -p "$HOME" $RS/data $RS/run $RS/etc $RS/log
# Own config dir (copy of the image's /etc/rstudio) so rserver can log to stderr, which
# TESK returns in the task logs. rsession's stderr ends up in the R console, so it logs
# to a file instead (/tmp/rs/log, readable from RStudio's terminal).
cp -r /etc/rstudio/. $RS/etc/ 2>/dev/null
export RSTUDIO_CONFIG_DIR=$RS/etc
printf '[@rserver]\nlog-level=%s\nlogger-type=stderr\n\n[@rsession]\nlog-level=%s\nlogger-type=file\nlog-dir=%s/log\n' \
  "$RS_LOG_LEVEL" "$RS_LOG_LEVEL" $RS > $RS/etc/logging.conf
printf 'provider=sqlite\ndirectory=%s/data\n' $RS > $RS/db.conf
printf 'session-default-working-dir=%s\nsession-default-new-project-dir=%s\n' "$HOME" "$HOME" > $RS/rsession.conf

# rserver starts rsession with HOME taken from passwd ("/", not writable), so the session
# cannot create its state dirs and the browser gets "Unable to connect to service".
# This wrapper points HOME and the XDG dirs to /tmp/home before starting the real rsession.
cat > $RS/rsession.sh <<EOS
#!/bin/sh
export HOME=$HOME USER=$USER RSTUDIO_CONFIG_DIR=$RS/etc
export XDG_DATA_HOME=$HOME/.local/share XDG_CONFIG_HOME=$HOME/.config XDG_CACHE_HOME=$HOME/.cache
exec /usr/lib/rstudio-server/bin/rsession "\$@"
EOS
chmod 755 $RS/rsession.sh

RSERVER_ARGS="--server-daemonize=0 --www-address=127.0.0.1 --www-port=$PORT
  --auth-none=1 --server-user=$USER --server-data-dir=$RS/run
  --database-config-file=$RS/db.conf --rsession-config-file=$RS/rsession.conf
  --rsession-path=$RS/rsession.sh
  --secure-cookie-key-file=$RS/cookie.key --server-pid-file=$RS/rserver.pid"

if [ "${SELFTEST:-0}" = 1 ]; then
  log "verify-installation (starts a test R session)"
  /usr/lib/rstudio-server/bin/rserver $RSERVER_ARGS --verify-installation=1 && { log "SELFTEST_OK"; exit 0; }
  exit 1
fi

# Publish the pod's :$PORT as 127.0.0.1:$HUB_PORT on the hub VM.
start_tunnel "R:127.0.0.1:${HUB_PORT}:127.0.0.1:${PORT}"

log "RStudio Server starting on :$PORT as $USER"
/usr/lib/rstudio-server/bin/rserver $RSERVER_ARGS
log "rserver exited ($?)"; exit 1
