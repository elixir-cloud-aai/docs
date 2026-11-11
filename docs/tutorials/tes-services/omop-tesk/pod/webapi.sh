# WebAPI task (image: ohdsi/webapi). Reaches the CDM database through the hub on
# 127.0.0.1:5432 and publishes WebAPI (:8080 in the pod) on the hub.
start_tunnel "R:127.0.0.1:${HUB_WEBAPI_PORT}:127.0.0.1:8080" "127.0.0.1:5432:127.0.0.1:${HUB_DB_PORT}"

# chisel accepts locally even when the DB task is down, so ask Postgres itself (SSLRequest).
pg_alive() { timeout 5 bash -c 'exec 3<>/dev/tcp/127.0.0.1/5432; printf "\0\0\0\10\4\322\26\57" >&3; head -c1 <&3' 2>/dev/null | grep -q '[NS]'; }
log "waiting for the database task"
until pg_alive; do sleep 10; done
# The DB task creates the webapi schema after loading the CDM; Flyway fills it.
sleep 20

cd /var/lib/ohdsi/webapi || exit 1
# The start command of the WebAPI 2.x images (exploded WAR; java expands only WEB-INF/lib/*,
# the Spring Boot WarLauncher loads the jars itself). WebAPI 3 images have only WebAPI.jar
# and start with "java -jar WebAPI.jar": this script does not support them yet.
log "starting WebAPI (first start runs all Flyway migrations, this takes several minutes)"
# shellcheck disable=SC2086
java $WEBAPI_JAVA_OPTS -cp ".:WebAPI.jar:WEB-INF/lib/*.jar" org.springframework.boot.loader.WarLauncher &
API=$!

# Spring Boot can leave the JVM running after a failed start: give up after STARTUP_TIMEOUT.
i=0
until curl -fs -o /dev/null http://127.0.0.1:8080/WebAPI/info; do
  kill -0 $API 2>/dev/null || { log "WebAPI exited during startup"; exit 1; }
  i=$((i + 10)); [ $i -ge "${STARTUP_TIMEOUT:-2400}" ] && { log "WebAPI not up after ${i}s"; kill $API; exit 1; }
  sleep 10
done
log "WebAPI up: $(curl -fs http://127.0.0.1:8080/WebAPI/info)"
wait $API
log "WebAPI exited"; exit 1
