#!/usr/bin/env bash
# install.sh - Git mini exercise, part 7.
# Updates the package lists and installs one tool (jq, a JSON processor).

PACKAGE="jq"

echo "Starting installation..."

# Pick the package manager available on this machine
if command -v brew >/dev/null 2>&1; then
    brew update                 # macOS (Homebrew)
    brew install "$PACKAGE"
elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update         # Debian / Ubuntu
    sudo apt-get install -y "$PACKAGE"
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf check-update       # Fedora
    sudo dnf install -y "$PACKAGE"
else
    echo "Error: no supported package manager found (brew, apt-get or dnf)." >&2
    exit 1
fi

echo "Installation complete!"
