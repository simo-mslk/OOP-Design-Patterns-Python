# 01 - Git mini exercise

Statement: https://gist.github.com/bdallard/8bdbdd70f234f94823c0c2cde9515388 (slide 26)

The script asked in part 7 is [`install.sh`](install.sh). I wrote it on a feature branch and merged it into `main` afterwards (part 11).

## Part 1 - Setup & config

```bash
git --version                                   # git version 2.x
git config --global user.name "Simo"
git config --global user.email "simo@example.com"
git config --global --list                      # check that both values are saved
```

## Part 2 - Create the first repository

| Task | Command |
|---|---|
| Create the folder | `mkdir my-first-repo` |
| Go inside | `cd my-first-repo` |
| Initialize git | `git init` (creates the hidden `.git` folder) |
| Create the file | `touch readme.txt` |

## Part 3 - First commit

| Question | Command |
|---|---|
| State of the repo | `git status` |
| Stage `readme.txt` | `git add readme.txt` |
| Commit | `git commit -m "Add readme file"` |
| History | `git log` |

## Part 4 - Make changes

```bash
echo "Hello from Simo" >> readme.txt
git status
```

`git status` now lists `readme.txt` as **modified** (in red, under "Changes not staged for commit"). Git noticed the file is different from the last commit, but the change will not go in the next commit until I stage it.

```bash
git add readme.txt
git commit -m "Add a greeting line to readme"
git log --oneline
```

I have **2 commits** now.

## Part 5 - Exploration

- `git diff` compares my working files with the staging area, line by line (`+` added, `-` removed). After `git add` it shows nothing anymore, then `git diff --staged` is the one that shows the staged changes.
- `git log --oneline` prints the history in a compact way: one commit per line, short hash + message, newest first.

## Part 6 - Branches

| Step | Command |
|---|---|
| 1. List branches | `git branch` |
| 2. Create `feature-script` | `git branch feature-script` |
| 3. Switch to it | `git switch feature-script` (older syntax: `git checkout feature-script`) |
| 4. Create + switch to `dev` in one command | `git switch -c dev` (or `git checkout -b dev`) |
| 5. Back to `feature-script` | `git switch feature-script` |
| 6. Check where I am | `git branch` (the `*` marks the current branch) or `git status` (first line: "On branch ...") |

## Part 7 - Bash script on a branch

```bash
git switch feature-script
touch install.sh            # content: see install.sh
chmod +x install.sh         # make it executable
git add install.sh
git commit -m "Add install script"
git log --oneline           # the new commit is on top, on this branch only
```

## Part 8 - Merge

```bash
git switch main
ls                          # only readme.txt
```

`install.sh` is **not** there: it was committed on `feature-script`, and `main` does not have that commit yet. Switching branch changes the files in the folder to match the branch.

```bash
git merge feature-script
ls                          # readme.txt  install.sh
git log --oneline
```

After the merge `install.sh` appears. In the log, the "Add install script" commit is now part of `main`. Since `main` had no new commit of its own, git did a **fast-forward**: it just moved `main` forward, no merge commit was created.

```bash
git branch -d feature-script    # -d refuses if the branch is not merged, -D forces it
```

## Part 9 - Push to GitHub

On github.com: New repository → `my-first-repo` → **no** README, .gitignore or license. If GitHub creates a first commit, my local history and the remote one have nothing in common and the push is rejected.

```bash
git remote add origin https://github.com/simo-mslk/my-first-repo.git
git branch -M main          # make sure the branch is called main
git push -u origin main     # -u remembers origin/main, next time `git push` is enough
```

After refreshing the page I can see `readme.txt`, `install.sh` and my commits in the history.

## Part 10 - Delete and clone

```bash
cd ..
rm -rf my-first-repo
git clone https://github.com/simo-mslk/my-first-repo.git
cd my-first-repo
ls && git log --oneline     # files and history are back
```

## Part 11 - Full workflow from scratch

```bash
rm -rf my-first-repo                     # 1. local folder
# 2. delete the repo on GitHub: Settings > Danger Zone > Delete this repository
mkdir bash-installer && cd bash-installer    # 3.
git init                                 # 4.
cat > README.md <<'EOF'
# bash-installer
Small Bash script that updates the package lists and installs a tool.
EOF
git add README.md                        # 5-6.
git commit -m "Add README"
git switch -c feature-install            # 7.
cp ../install.sh . && chmod +x install.sh    # 8.
git add install.sh
git commit -m "Add install script"       # 9.
git switch main                          # 10.
git merge feature-install                # 11.
git branch -d feature-install            # 12.
# 13. create an empty bash-installer repo on GitHub
git remote add origin https://github.com/simo-mslk/bash-installer.git
git push -u origin main                  # 14.
```

## Reflection questions

1. **Why is version control useful?** Every version of the project is saved, so I can see what changed, when and by whom, and go back to a version that worked. It also lets several people work on the same code at the same time and merge their work instead of sending files around.
2. **Staging vs committing?** Staging (`git add`) prepares the next snapshot: I pick which changes go in it. Committing (`git commit`) records that snapshot in the history for good, with a message. So I can change many files and still make clean, separate commits.
3. **When should I commit?** When one logical change is done and the code still works: a function added, a bug fixed, a config changed. Often, and in small pieces, so each commit is easy to understand and easy to revert.
4. **`git init` vs `git clone`?** `git init` turns the current folder into a brand new, empty repository. `git clone <url>` downloads a repository that already exists, with all its history, and configures the `origin` remote automatically.
5. **Why write good commit messages?** The history is documentation. "Fix rounding error in total price" tells me in 6 months why a line changed; "update" tells me nothing. It also helps with `git log`, `git blame` and code reviews.
6. **Why use branches?** A branch is an isolated line of work: I can try a feature or fix a bug without touching the stable code, and merge only when it is finished and tested.
7. **When create a branch instead of working on `main`?** For every new feature, bug fix or experiment, and always when working in a team (one branch per task, then a pull request). `main` should stay deployable at all times.
