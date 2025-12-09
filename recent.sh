#!/bin/bash

. .venv/bin/activate
python3 .github/scripts/recent_games.py
python3 .github/scripts/update_games.py
