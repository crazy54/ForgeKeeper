#!/usr/bin/env bash
set -euo pipefail
ACTION=${1:-}
LOG_FILE=/var/log/forgekeeper/control.log
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

log() {
  mkdir -p $(dirname "$LOG_FILE")
  echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

case "$ACTION" in
  shutdown)
    log "Shutdown requested"
    # Give portal response before terminating PID 1
    nohup bash -c 'sleep 2 && kill -TERM 1' >/dev/null 2>&1 &
    echo "ForgeKeeper shutdown signal issued"
    ;;
  reset)
    WORKDIR=/workspaces
    if [ -d "$WORKDIR" ]; then
      log "Reset requested: cleaning $WORKDIR"
      find "$WORKDIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    fi
    log "Restarting supervised services"
    supervisorctl restart all >/dev/null 2>&1 || true
    echo "ForgeKeeper workspace reset"
    ;;
  *)
    echo "Unknown action: $ACTION" >&2
    exit 1
    ;;
esac
