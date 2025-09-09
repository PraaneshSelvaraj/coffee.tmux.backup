#!/bin/bash

tmux bind-key C run-shell "tmux display-popup -E 'python3 ./ui.py'"