#!/bin/bash


set-environment -g TMUX_PLUGIN_MANAGER_PATH "$HOME/.tmux/coffee/plugins"
run-shell "python3 $HOME/Documents/coffee.tmux/main.py --bootstrap"
bind-key C run-shell "tmux display-popup -E 'python3 $HOME/Documents/coffee.tmux/ui.py'"