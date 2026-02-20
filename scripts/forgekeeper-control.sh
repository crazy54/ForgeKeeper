#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"
LOG_DIR="/var/log/forgekeeper"
LOG_FILE="${LOG_DIR}/control.log"

log() {
  mkdir -p "${LOG_DIR}"
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*" >> "${LOG_FILE}"
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

[[ -z "${ACTION}" ]] && die "No action specified. Usage: forgekeeper-control.sh <shutdown|reset>"

case "${ACTION}" in
  shutdown)
    log "Shutdown requested"
    # Defer SIGTERM to PID 1 so the HTTP response can be sent first
    nohup bash -c 'sleep 2 && kill -TERM 1' >/dev/null 2>&1 &
    echo "ForgeKeeper shutdown signal issued"
    ;;

  reset)
    WORKDIR="/workspaces"
    if [[ -d "${WORKDIR}" ]]; then
      log "Reset requested: cleaning ${WORKDIR}"
      find "${WORKDIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    fi
    log "Restarting supervised services"
    supervisorctl restart all >/dev/null 2>&1 || true
    echo "ForgeKeeper workspace reset"
    ;;

  *)
    die "Unknown action: ${ACTION}. Valid actions: shutdown, reset"
    ;;
esac
