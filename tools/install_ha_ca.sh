#!/usr/bin/env bash
# Duenner Wrapper fuer die kanonische Version im Add-on-Image. Auf dem HA-Host
# laesst sich das Skript direkt vom Add-on laden:
#   curl -fsSL http://<HA-IP>:19980/install-ca.sh -o /tmp/install_ha_ca.sh
#   bash /tmp/install_ha_ca.sh
exec "$(dirname "$0")/../dreame_local/app/install_ca.sh" "$@"
