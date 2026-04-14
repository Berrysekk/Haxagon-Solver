#!/usr/bin/env bash
set -e
pip install -r requirements.txt
playwright install chromium
brew install exiftool binwalk foremost node 2>/dev/null || true
npm install -g cyberchef-cli 2>/dev/null || true
echo "Setup complete."
