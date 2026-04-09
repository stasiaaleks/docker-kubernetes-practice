#!/bin/bash

COUNT=10
START=false
STOP=false
NAME_PREFIX="nginx"

while [[ $# -gt 0 ]]; do
    case $1 in
        --start) START=true; shift ;;
        --stop) STOP=true; shift ;;
        --count) COUNT="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

if [[ "$START" == false && "$STOP" == false ]]; then
    log "No --start/--stop parameter provided"
    exit 1
fi

run() {
    local id=$1
    docker rm -f "${NAME_PREFIX}_${id}" 2>/dev/null
    docker run -d --name "${NAME_PREFIX}_${id}" -p $((8080 + id)):80 nginx:latest
}

stop() {
    docker rm -f $(docker ps -a -q --filter "name=${NAME_PREFIX}_")
}

if [[ "$STOP" == true ]]; then
    log "Stopping all ${NAME_PREFIX} containers"
    stop
fi

if [[ "$START" == true ]]; then
    log "Starting $COUNT ${NAME_PREFIX} containers"
    for i in $(seq 1 "$COUNT"); do
        run "$i"
    done
fi
