#!/bin/bash
# Double-click this file to start the InvoiceShield Decision Console.
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is not installed on this Mac."
  echo "Install it by running this in Terminal:  xcode-select --install"
  echo "Then double-click this file again."
  read -p "Press Enter to close. "
  exit 1
fi
echo "Starting InvoiceShield Decision Console..."
echo "Your browser will open at http://localhost:8000"
echo "Keep THIS window open during the demo. Press Ctrl+C here to stop."
echo ""
python3 demo_ui.py
