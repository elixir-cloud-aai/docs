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
  # Not a pipeline: an exit in the loop must end the task, not a subshell.
  find . -name '*.csv' ! -path '*__MACOSX*' | sort > /tmp/cdm.files
  while read -r f; do
    t=$(basename "$f" .csv | tr 'A-Z' 'a-z')
    # Eunomia also ships cohort tables, which are not part of the CDM 5.3 DDL.
    if [ "$(psql -Atc "select to_regclass('demo_cdm.$t') is not null")" != t ]; then
      log "skipping $f: no table demo_cdm.$t in the CDM DDL"; continue
    fi
    # quoted, because note_nlp has a column named "offset"
    cols=$(head -1 "$f" | tr -d '\r' | tr 'A-Z' 'a-z' | sed 's/[^,]*/"&"/g')
    psql -q -v ON_ERROR_STOP=1 -c "\\copy demo_cdm.$t ($cols) from '$f' csv header" \
      || { log "ERROR: could not load $t"; exit 1; }
  done < /tmp/cdm.files
  cd /tmp && rm -rf /tmp/cdm
  log "CDM loaded: $(psql -Atc 'select count(*) from demo_cdm.person') persons"
fi

if [ "${SELFTEST:-0}" = 1 ]; then
  psql -v ON_ERROR_STOP=1 -c "select relname as table, n_live_tup as rows from pg_stat_user_tables where schemaname='demo_cdm' and n_live_tup > 0 order by 1" \
    && [ "$(psql -Atc 'select count(*) from demo_cdm.person')" -gt 0 ] && { log "SELFTEST_OK"; exit 0; }
  log "SELFTEST_FAILED"; exit 1
fi

# Needs WebAPI to have run its migrations (webapi schema) and to serve the results DDL.
register_source() {
  [ "$(psql -Atc "select count(*) from webapi.source where source_key='EUNOMIA'" 2>/dev/null)" = 1 ] && return 0
  wget -q -O /dev/null "$WEBAPI/info" 2>/dev/null || return 1
  [ "$(psql -Atc "select to_regclass('webapi.source_daimon') is not null")" = t ] || return 1
  # Without the results schema, cohorts can't be generated: register the source only after
  # it exists, so that a failed DDL is retried in the next round.
  if [ "$(psql -Atc "select to_regclass('demo_cdm_results.cohort') is not null")" != t ]; then
    log "WebAPI is up, creating the results schema"
    wget -q -O /tmp/results.sql "$WEBAPI/ddl/results?dialect=postgresql&schema=demo_cdm_results&vocabSchema=demo_cdm&tempSchema=temp&initConceptHierarchy=true" \
      && psql -q -f /tmp/results.sql >/dev/null \
      && [ "$(psql -Atc "select to_regclass('demo_cdm_results.cohort') is not null")" = t ] \
      || { log "WARN: results DDL failed, retrying later"; return 1; }
  fi
  log "registering the source"
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
