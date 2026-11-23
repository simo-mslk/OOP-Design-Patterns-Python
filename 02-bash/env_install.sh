#!/usr/bin/env bash
#
# env_install.sh - prepare a small Python dev environment on a new machine.
#
#   1. pretty printing helper (printf + blank lines, colored)
#   2. operating system detection with $OSTYPE
#   3. python3 check (install it if missing, show the version otherwise)
#   4. pip check
#   5. Jupyter Notebook installation (command depends on the OS)
#   6. macOS only: `brew doctor`
#
# Bonus: colors, log file, strict mode, --dry-run / --verbose / --quiet, --uninstall
#
# Usage: ./env_install.sh [--dry-run] [--verbose] [--quiet] [--uninstall] [--help]

# Strict mode: exit on error (-e), error on unset variables (-u), ERR trap inside functions (-E),
# and a pipeline fails if any command inside it fails (pipefail).
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
LOG_FILE="$(cd "$(dirname "$0")" && pwd)/env_install.log"

dry_run=0
verbose=0
quiet=0
mode="install"

# Colors only when the output is a terminal (no escape codes inside files/pipes)
if [ -t 1 ]; then
    C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_INFO=$'\033[36m'; C_END=$'\033[0m'
else
    C_OK=""; C_WARN=""; C_ERR=""; C_INFO=""; C_END=""
fi

# ----------------------------------------------------------------- helpers ---

# Append "<date> [LEVEL] message" to the log file, so a failed install can be debugged later
log() {
    local level="$1"; shift
    printf '%s [%s] %s\n' "$(date '+%F %T')" "$level" "$*" >> "$LOG_FILE"
}

# Feature 1: print a message with an empty line before and after it.
# $1 = message, $2 = color (optional). printf is used because echo -e is not portable.
pretty_print() {
    local message="$1" color="${2:-$C_INFO}"
    [ "$quiet" -eq 1 ] && return 0
    printf '\n%s%s%s\n\n' "$color" "$message" "$C_END"
}

info()    { pretty_print "$*" "$C_INFO"; log INFO "$*"; }
success() { pretty_print "OK  $*" "$C_OK"; log OK "$*"; }
# Warnings and errors are printed even with --quiet (they go to stderr)
warn()    { printf '\n%sWARN  %s%s\n\n' "$C_WARN" "$*" "$C_END" >&2; log WARN "$*"; }
fail()    { printf '\n%sERROR %s%s\n\n' "$C_ERR" "$*" "$C_END" >&2; log ERROR "$*"; exit 1; }
detail()  { [ "$verbose" -eq 1 ] && printf '    %s\n' "$*"; return 0; }

has() { command -v "$1" >/dev/null 2>&1; }

# Every command that changes the system goes through here:
# it is logged, and with --dry-run it is only displayed.
execute() {
    log CMD "$*"
    if [ "$dry_run" -eq 1 ]; then
        printf '    (dry-run) %s\n' "$*"
        return 0
    fi
    detail "\$ $*"
    if "$@"; then
        log OK "$*"
    else
        local code=$?
        log ERROR "exit $code: $*"
        return "$code"
    fi
}

show_help() {
    cat <<EOF
Usage: $SCRIPT_NAME [options]

Installs python3, pip and Jupyter Notebook (and runs brew doctor on macOS).

Options:
  --dry-run     print the commands instead of running them
  --verbose     print every command before running it
  --quiet       only print warnings and errors
  --uninstall   remove Jupyter Notebook
  -h, --help    show this message
EOF
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --dry-run)   dry_run=1 ;;
            --verbose)   verbose=1 ;;
            --quiet)     quiet=1 ;;
            --uninstall) mode="uninstall" ;;
            -h|--help)   show_help; exit 0 ;;
            *)           show_help >&2; fail "unknown option '$1'" ;;
        esac
        shift
    done
}

# ---------------------------------------------------------------- features ---

# Feature 2: OSTYPE is set by the shell itself (darwin23, linux-gnu, msys...)
detect_os() {
    case "${OSTYPE:-}" in
        darwin*)          os="macos";   pkg="brew" ;;
        linux*)           os="linux";   pkg="apt-get" ;;
        msys*|cygwin*)    os="windows"; pkg="" ;;
        *)                os="unknown"; pkg="" ;;
    esac
    info "Operating system: $os (OSTYPE=${OSTYPE:-not set})"

    if [ "$os" = "linux" ] && ! has apt-get; then
        warn "This script only knows apt-get on Linux, automatic installs are disabled."
        pkg=""
    fi
    if [ "$os" = "macos" ] && ! has brew; then
        warn "Homebrew is not installed (https://brew.sh), automatic installs are disabled."
        pkg=""
    fi
}

# Install one package with the package manager found by detect_os
pkg_install() {
    case "$pkg" in
        brew)    execute brew install "$1" ;;
        apt-get) execute sudo apt-get update -qq && execute sudo apt-get install -y "$1" ;;
        *)       fail "Please install '$1' manually: no supported package manager on $os." ;;
    esac
}

# Feature 3
check_python() {
    if has python3; then
        success "python3 is installed: $(python3 --version 2>&1)"
        return 0
    fi
    warn "python3 is missing, installing it"
    if [ "$os" = "macos" ]; then pkg_install python; else pkg_install python3; fi
    [ "$dry_run" -eq 1 ] || success "python3 installed: $(python3 --version 2>&1)"
}

# Feature 4
check_pip() {
    if python3 -m pip --version >/dev/null 2>&1; then
        success "pip is available: $(python3 -m pip --version | cut -d' ' -f1-2)"
        return 0
    fi
    warn "pip is missing, installing it"
    if [ "$os" = "linux" ]; then
        pkg_install python3-pip          # Debian/Ubuntu ship pip as a separate package
    else
        execute python3 -m ensurepip --upgrade
    fi
}

# Feature 5: each OS has its own "right" way to install Jupyter
install_jupyter() {
    if has jupyter && jupyter notebook --version >/dev/null 2>&1; then
        success "Jupyter Notebook already installed (version $(jupyter notebook --version))"
        return 0
    fi
    info "Installing Jupyter Notebook..."
    case "$os" in
        macos)
            # Homebrew's Python refuses global pip installs (PEP 668), so use the formula
            pkg_install jupyterlab ;;
        linux)
            # Same PEP 668 protection on recent Ubuntu: apt package first, pip --user as fallback
            pkg_install jupyter-notebook || execute python3 -m pip install --user notebook ;;
        *)
            execute python3 -m pip install --user notebook ;;
    esac
    success "Jupyter Notebook is ready, start it with: jupyter notebook"
}

# Feature 6: brew doctor exits with 1 for simple warnings, which must not stop the script
brew_doctor() {
    [ "$os" = "macos" ] || { detail "not on macOS, skipping brew doctor"; return 0; }
    has brew || return 0
    info "Checking Homebrew health (brew doctor)..."
    if execute brew doctor; then
        success "Homebrew is healthy"
    else
        warn "brew doctor found some problems, read its output above"
    fi
}

# Bonus: undo what the script installed (python and pip are left alone on purpose)
uninstall() {
    info "Removing Jupyter Notebook..."
    case "$os" in
        macos) execute brew uninstall jupyterlab || true ;;
        linux) execute sudo apt-get remove -y jupyter-notebook || true
               execute python3 -m pip uninstall -y notebook || true ;;
        *)     execute python3 -m pip uninstall -y notebook || true ;;
    esac
    success "Uninstall finished"
}

# -------------------------------------------------------------------- main ---
main() {
    parse_args "$@"
    log INFO "=== $SCRIPT_NAME $* (mode=$mode, dry_run=$dry_run) ==="
    # If something fails unexpectedly, write the line number in the log
    trap 'log ERROR "script stopped at line $LINENO"' ERR

    [ "$dry_run" -eq 1 ] && info "Dry-run mode: nothing will be changed"
    detect_os

    if [ "$mode" = "uninstall" ]; then
        uninstall
        exit 0
    fi

    check_python
    check_pip
    install_jupyter
    brew_doctor

    success "All done. Log file: $LOG_FILE"
}

main "$@"
