# 02 - Bash script exercise

Statement: https://courses.dallard.tech/linux/bash_exo/ (slide 18)

## Part 1 - Improve the shell

```bash
echo $0        # the shell that is running right now (e.g. -zsh or bash)
echo $SHELL    # my login shell, the one set for my user (e.g. /bin/zsh)
```

They can be different: if my login shell is zsh and I type `bash`, `$0` says bash but `$SHELL` still says `/bin/zsh`.

macOS uses zsh by default, so the framework is **Oh My Zsh** (on a Linux machine with bash it would be Oh My Bash, same idea). After installing it I changed `ZSH_THEME` in `~/.zshrc`, and in the same file I added git to the plugins:

```bash
plugins=(git)
```

then reloaded the config with `source ~/.zshrc`.

**What's the purpose of `source`?** `source file` (or `. file`) executes the file *inside the current shell*. If I ran `./.zshrc` instead, it would run in a child shell and everything it defines (aliases, variables, PATH, theme) would disappear when that child shell ends. That's why `source` is used to reload a config without opening a new terminal.

Git plugin aliases tested: `gst` → `git status`, `glog` → `git log --oneline --decorate --graph`, `gp` → `git push`, `gl` → `git pull`.

## Part 2 - Python

```bash
python3 --version   # Python 3.x
```

I always use `python3` (not `python`), because on some systems `python` is still Python 2 or does not exist.

## Part 3 & 4 - The script

```bash
chmod +x env_install.sh           # without the x permission: "permission denied"
./env_install.sh --dry-run        # show the commands, change nothing
./env_install.sh                  # real run
./env_install.sh --help
```

Structure of [`env_install.sh`](env_install.sh): shebang → strict mode and settings → helper functions → one function per feature → `main` that calls them in order.

| Feature | Function | How |
|---|---|---|
| 1. Pretty printing | `pretty_print` | `printf` with a blank line before and after, + a color |
| 2. OS detection | `detect_os` | `case` on `$OSTYPE` (`darwin*`, `linux*`, `msys*`) |
| 3. Python check | `check_python` | `command -v python3`, installs it with brew/apt if missing, shows the version otherwise |
| 4. pip check | `check_pip` | `python3 -m pip --version` (apt package `python3-pip` or `ensurepip` if missing) |
| 5. Jupyter | `install_jupyter` | macOS: `brew install jupyterlab`, Linux: apt `jupyter-notebook` (pip `--user` as fallback) |
| 6. macOS health | `brew_doctor` | `brew doctor`, a warning does not stop the script |

Note: I don't use `pip install` directly on macOS/Ubuntu because recent Homebrew and Ubuntu Pythons are "externally managed" (PEP 668) and refuse global pip installs.

### Best practices I followed

- comments explain *why* (e.g. why `brew doctor` is allowed to fail)
- every variable is quoted (`"$1"`, `"$LOG_FILE"`)
- errors are handled: `fail` prints in red and stops, failed commands are logged with their exit code
- tested after each feature with `--dry-run`, and checked with `shellcheck` (no warnings)

## Verification checklist (to tick after the real run)

- [ ] the prompt shows the Oh My Zsh theme
- [ ] `gst` works like `git status`
- [ ] `python3 --version` → 3.x
- [ ] `python3 -m pip --version` shows pip
- [ ] `jupyter notebook` opens in the browser
- [ ] macOS: `brew doctor` → "Your system is ready to brew."

## Bonus done

- **colors**: green = success, yellow = warning, red = error (only when the output is a terminal)
- **logging**: `env_install.log` gets a timestamp, the level, each command run and its result
- **strict mode**: `set -Eeuo pipefail` + a `trap` on `ERR` that logs the line where the script stopped
- **arguments**: `--dry-run`, `--verbose`, `--quiet` (parsed with `while` + `case` + `shift`)
- **uninstall**: `--uninstall` removes Jupyter Notebook
