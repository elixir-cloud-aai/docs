# CDM database task (image: postgres:16-alpine).
# Loads the Eunomia GiBleed demo CDM into a fresh Postgres, publishes it on the hub and,
# once WebAPI is up, creates the results schema and registers the CDM as a WebAPI source.
export PGDATA=/tmp/pgdata POSTGRES_PASSWORD="$DB_PASSWORD"
export PGHOST=127.0.0.1 PGUSER=postgres PGDATABASE=postgres PGPASSWORD="$DB_PASSWORD"
WEBAPI=http://127.0.0.1:18081/WebAPI

start_tunnel "R:127.0.0.1:${HUB_DB_PORT}:127.0.0.1:5432" "127.0.0.1:18081:127.0.0.1:${HUB_WEBAPI_PORT}"

# The stock entrypoint handles the random UID (nss_wrapper) and runs initdb into /tmp.
docker-entrypoint.sh postgres -c listen_addresses=127.0.0.1 &
PG=$!
until pg_isready -q; do kill -0 $PG 2>/dev/null || { log "postgres failed to start"; exit 1; }; sleep 2; done

if [ "$(psql -Atc "select to_regclass('demo_cdm.person') is not null")" != t ]; then
  log "loading Eunomia CDM from $EUNOMIA_URL"
  mkdir -p /tmp/cdm && cd /tmp/cdm || exit 1
  fetch "$EUNOMIA_URL" eunomia.zip && unzip -q -o eunomia.zip && fetch "$CDM_DDL_URL" ddl.sql \
    || { log "ERROR: download failed"; exit 1; }
  # WebAPI's Flyway may already have created "webapi" while this loads.
  for s in demo_cdm demo_cdm_results temp webapi; do psql -q -c "create schema if not exists $s"; done
  sed 's/@cdmDatabaseSchema/demo_cdm/g' ddl.sql | psql -q -v ON_ERROR_STOP=1 || exit 1
  find . -name '*.csv' ! -path '*__MACOSX*' | sort | while read -r f; do
    t=$(basename "$f" .csv | tr 'A-Z' 'a-z')
    # quoted, because note_nlp has a column named "offset"
    cols=$(head -1 "$f" | tr -d '\r' | tr 'A-Z' 'a-z' | sed 's/[^,]*/"&"/g')
    psql -q -c "\\copy demo_cdm.$t ($cols) from '$f' csv header" || log "WARN: could not load $t"
  done
  cd /tmp && rm -rf /tmp/cdm
  log "CDM loaded: $(psql -Atc 'select count(*) from demo_cdm.person') persons"
fi

if [ "${SELFTEST:-0}" = 1 ]; then
  psql -c "select relname as table, n_live_tup as rows from pg_stat_user_tables where schemaname='demo_cdm' and n_live_tup > 0 order by 1"
  log "SELFTEST_OK"; exit 0
fi

# Needs WebAPI to have run its migrations (webapi schema) and to serve the results DDL.
register_source() {
  [ "$(psql -Atc "select count(*) from webapi.source where source_key='EUNOMIA'" 2>/dev/null)" = 1 ] && return 0
  wget -q -O /dev/null "$WEBAPI/info" 2>/dev/null || return 1
  [ "$(psql -Atc "select to_regclass('webapi.source_daimon') is not null")" = t ] || return 1
  log "WebAPI is up, creating results schema and registering source"
  wget -q -O /tmp/results.sql "$WEBAPI/ddl/results?dialect=postgresql&schema=demo_cdm_results&vocabSchema=demo_cdm&tempSchema=temp&initConceptHierarchy=true" \
    && psql -q -f /tmp/results.sql >/dev/null || log "WARN: results DDL failed"
  # source_connection is used by WebAPI, which reaches this DB on its own 127.0.0.1:5432.
  psql -q -v ON_ERROR_STOP=1 <<SQL || return 1
insert into webapi.source (source_id, source_name, source_key, source_connection, source_dialect)
  values (nextval('webapi.source_sequence'), 'Eunomia GiBleed (TESK @ ELIXIR-FI)', 'EUNOMIA',
          'jdbc:postgresql://127.0.0.1:5432/postgres?user=postgres&password=${DB_PASSWORD}', 'postgresql');
insert into webapi.source_daimon (source_daimon_id, source_id, daimon_type, table_qualifier, priority)
  select nextval('webapi.source_daimon_sequence'), s.source_id, d.t, d.q, d.p
  from webapi.source s, (values (0,'demo_cdm',0), (1,'demo_cdm',1), (2,'demo_cdm_results',1), (5,'temp',0)) d(t,q,p)
  where s.source_key = 'EUNOMIA';
SQL
  wget -q -O /dev/null "$WEBAPI/source/refresh" || true
  log "source EUNOMIA registered"
}

log "database ready"
while kill -0 $PG 2>/dev/null; do
  register_source || true
  sleep 30
done
log "postgres exited"; exit 1
