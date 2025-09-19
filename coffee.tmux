#!/usr/bin/env bash

# Bind key to open Coffee TUI in popup
bind-key C run-shell 'COFFEE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; tmux display-popup -E "python3 \"$COFFEE_DIR/ui.py\""'

# Source all enabled plugins
run-shell 'COFFEE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; python3 "$COFFEE_DIR/cli/main.py" --source-plugins'