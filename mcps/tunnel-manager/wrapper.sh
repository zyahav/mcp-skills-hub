#!/bin/bash
export TUNNEL_CONFIG_PATH="/Users/zyahav/tunnel-management/configs/config.yml"
export TUNNEL_LEDGER_PATH="/Users/zyahav/tunnel-management/run-state.json"
node "$(dirname "$0")/build/index.js"
