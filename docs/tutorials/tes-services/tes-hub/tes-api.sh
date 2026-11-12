# shellcheck shell=bash
# Requests to the GA4GH TES API, sourced by the launchers on this VM (tes-service.sh,
# ../omop-tesk/omop-tesk-fi.sh). They set TES_URL and TES_API first.
#
# If TES_TOKEN is set, every request carries "Authorization: Bearer $TES_TOKEN". The
# header reaches curl through a pipe that the builtin printf writes (process
# substitution), so the token never appears on a command line, in a file or in a log.

# tes_curl <curl arguments>: prints the body of a 2xx answer. Otherwise prints why to
# stderr and returns 1.
tes_curl() {
  local out code
  if [[ -n "${TES_TOKEN:-}" ]]; then
    out="$(curl -sS -w '\n%{http_code}' -H @<(printf 'Authorization: Bearer %s\n' "$TES_TOKEN") "$@")" || return 1
  else
    out="$(curl -sS -w '\n%{http_code}' "$@")" || return 1
  fi
  code="${out##*$'\n'}"; out="${out%$'\n'*}"
  case "$code" in
    2??) printf '%s\n' "$out" ;;
    401)
      if [[ -n "${TES_TOKEN:-}" ]]; then
        echo "ERROR: $TES_URL answered 401 Unauthorized: the token in TES_TOKEN is invalid or has expired (after about 4 hours). Get a new LS Login access token, set TES_TOKEN again and rerun the command" >&2
      else
        echo "ERROR: $TES_URL answered 401 Unauthorized: it needs a token. Get an LS Login access token and set TES_TOKEN (see the tutorial)" >&2
      fi
      return 1 ;;
    403)
      echo "ERROR: $TES_URL answered 403 Forbidden: the token is valid, but your account may not run tasks there. On the TES services of ELIXIR On-Cloud, you need membership in the compute group ECP_CLN:EOC-Compute of LS Login" >&2
      return 1 ;;
    *)
      echo "ERROR: $TES_URL answered HTTP ${code:-without status}: ${out:0:300}" >&2
      return 1 ;;
  esac
}

# tes_check: fails early, with the reason, if the TES doesn't let us list tasks.
tes_check() { tes_curl -m 30 "$TES_API/tasks?view=MINIMAL&page_size=1" >/dev/null; }
