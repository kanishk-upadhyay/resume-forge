---
name: github
description: Comprehensive expert guide for GitHub CLI (gh) and Git over SSH and HTTPS. Use when creating, cloning, or pushing repositories, creating and reviewing pull requests, inspecting failed GitHub Actions runs, managing releases, querying GitHub API/GraphQL, or configuring SSH keys and authentication.
license: MIT
metadata:
  author: Antigravity & AgentSkills Ecosystem
  last-updated: '2026-11-09'
  keywords:
  - github
  - gh
  - git
  - ssh
  - actions
  - pull-request
  - issues
  - releases
  - agentskills
---

# 🐙 Comprehensive GitHub CLI (`gh`) & Git Skill

This skill is the authoritative, production-grade guide for interacting with GitHub directly from the command line using the **GitHub CLI (`gh`)** and **Git over SSH / HTTPS**.

---

## Table of Contents
1. [Authentication & SSH Setup](#1-authentication--ssh-setup)
2. [Repository Creation & Remote Publishing (Terminal-Only)](#2-repository-creation--remote-publishing-terminal-only)
3. [Branch Operations & Conventional Commits](#3-branch-operations--conventional-commits)
4. [Pull Request (PR) Lifecycle Management](#4-pull-request-pr-lifecycle-management)
5. [Issue & Project Tracking](#5-issue--project-tracking)
6. [GitHub Actions & CI/CD Debugging](#6-github-actions--cicd-debugging)
7. [Releases & Artifact Distribution](#7-releases--artifact-distribution)
8. [Advanced Code & Commit Search](#8-advanced-code--commit-search)
9. [Direct GitHub REST & GraphQL API (`gh api`)](#9-direct-github-rest--graphql-api-gh-api)
10. [Agent Skills Management (`gh skill`)](#10-agent-skills-management-gh-skill)
11. [Troubleshooting & Common Failure Modes](#11-troubleshooting--common-failure-modes)

---

## 1. Authentication & SSH Setup

### A. Checking Auth Status
```bash
gh auth status
```
If authenticated, it will display the active account, scopes (`repo`, `workflow`, `read:org`), and default git protocol (`ssh` or `https`).

### B. Logging in via GitHub CLI
```bash
# Interactive login (selects GitHub.com, SSH/HTTPS, and browser or token):
gh auth login -h github.com

# Non-interactive login using a personal access token (PAT):
echo "$GITHUB_TOKEN" | gh auth login --with-token

# Configure git to use gh credentials for HTTPS remotes:
gh auth setup-git
```

### C. Testing and Configuring SSH Keys
GitHub supports modern `ed25519` and `rsa` SSH keys:
```bash
# 1. Test existing SSH connection to GitHub:
ssh -T git@github.com
# Expected output: "Hi <username>! You've successfully authenticated, but GitHub does not provide shell access."

# 2. If SSH agent does not have your key loaded:
ssh-add -l                                # List loaded keys
ssh-add ~/.ssh/id_ed25519                 # Load modern ed25519 key
ssh-add ~/.ssh/id_rsa                     # Or load RSA key

# 3. Generate a new SSH key if none exists:
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519 -N ""
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519

# 4. Upload SSH public key to GitHub directly via CLI:
gh ssh-key add ~/.ssh/id_ed25519.pub --title "MacBook Workstation"
```

---

## 2. Repository Creation & Remote Publishing (Terminal-Only)

### A. Create and Push a Local Project in One Shot
When you have an existing local directory with committed code:
```bash
cd /path/to/project

# Create a public repository on your personal account and push immediately:
gh repo create my-repo --public --source=. --remote=origin --push

# Create a private repository:
gh repo create my-repo --private --source=. --remote=origin --push

# Create under an organization:
gh repo create my-org/my-repo --public --source=. --remote=origin --push
```

### B. Standard Git over SSH Setup
If the remote repository already exists on GitHub:
```bash
# Check current remote:
git remote -v

# Set or update remote origin to SSH:
git remote set-url origin git@github.com:<username>/<repo>.git

# Push current branch and set upstream tracking:
git push -u origin main
```

### C. Repository Management Recipes
```bash
# Clone a repository using SSH:
gh repo clone <owner>/<repo> -- --protocol ssh

# Fork a repository and configure upstream remote automatically:
gh repo fork <owner>/<repo> --clone --remote

# View repository details & README in terminal:
gh repo view <owner>/<repo>

# Edit repository settings (e.g. description, homepage):
gh repo edit --description "In-house resume parser and studio" --homepage "https://kanishk-upadhyay.github.io"
```

---

## 3. Branch Operations & Conventional Commits

Follow the **Conventional Commits 1.0.0** format:
- `feat:` A new feature for the user
- `fix:` A bug fix
- `docs:` Documentation updates
- `test:` Adding or refactoring tests
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `perf:` Performance improvements
- `ci:` Changes to CI/CD workflows and scripts

```bash
# Stage and commit with structured message:
git add .
git commit -m "feat(parser): add nested brace extraction for project headings"

# Push to a feature branch:
git push -u origin feature/my-feature

# Pull remote changes with rebase:
git pull --rebase origin main
```

---

## 4. Pull Request (PR) Lifecycle Management

### A. Creating Pull Requests
```bash
# Create PR interactively:
gh pr create

# Create PR using the current branch and automated commit title/body:
gh pr create --fill --base main

# Create PR with explicit title, body, and reviewer:
gh pr create --title "feat: single-page auto-fit compressor" \
             --body "Implements dynamic margin/font squeezer when page count > 1." \
             --reviewer "teammate" \
             --assignee "@me"
```

### B. Inspecting and Reviewing PRs
```bash
# Check status of PRs relevant to current branch / user:
gh pr status

# List open PRs:
gh pr list --state open --limit 10

# View PR details and diff:
gh pr view 42
gh pr diff 42

# Check out a pull request branch locally for testing:
gh pr checkout 42

# Submit a review:
gh pr review 42 --approve --body "Verified single-page rendering. LGTM!"
gh pr review 42 --request-changes --body "Please handle null location fields in schema.py."
gh pr comment 42 --body "Ran unit tests: 67/67 passing."
```

### C. Merging Pull Requests
```bash
# Squash and merge, deleting the remote branch automatically:
gh pr merge 42 --squash --delete-branch

# Auto-merge when all checks pass:
gh pr merge 42 --auto --squash
```

---

## 5. Issue & Project Tracking

```bash
# List open issues:
gh issue list --state open

# Create an issue with labels:
gh issue create --title "bug: accent macros stripped in ModernCV" \
                --body "Diacritics like \v{c} are removed during macro peeling." \
                --label "bug,parser"

# Comment on and close an issue:
gh issue comment 12 --body "Fixed in commit 8eb1532 with ACCENTS_MAP pre-processing."
gh issue close 12 --reason "completed"
```

---

## 6. GitHub Actions & CI/CD Debugging

### A. Monitoring Workflow Runs
```bash
# List recent runs across all workflows:
gh run list --limit 10

# Filter runs for a specific workflow file:
gh run list --workflow=build-pdf.yml

# Watch an in-progress workflow run in real time:
gh run watch <run-id>
```

### B. Inspecting Failures (Zero Guesswork)
```bash
# View summary and failing step:
gh run view <run-id>

# Extract the exact failed step logs directly to terminal:
gh run view <run-id> --log-failed

# Download all run logs to inspect locally:
gh run download <run-id>
```

### C. Triggering & Rerunning Workflows
```bash
# Rerun only failed jobs from a run:
gh run rerun <run-id> --failed

# Rerun all jobs in a run:
gh run rerun <run-id>

# Manually trigger a workflow dispatch:
gh workflow run deploy-pages.yml --ref main
```

---

## 7. Releases & Artifact Distribution

```bash
# Create a release with compiled binary/PDF assets:
gh release create v1.0.0 output/*.pdf \
  --title "v1.0.0 - Production In-House Resume Engine" \
  --notes "Zero-cloud compiler, multi-template parser, and Web Studio."

# List releases:
gh release list

# Download release artifacts:
gh release download v1.0.0 -D ./downloads
```

---

## 8. Advanced Code & Commit Search

```bash
# Search code across your repositories:
gh search code "ResumeData.from_dict" --owner kanishk-upadhyay

# Search commits across a repository:
gh search commits "auto-fit" -R kanishk-upadhyay/resume-forge

# Search pull requests matching keywords:
gh search prs "diacritics" --state merged -R kanishk-upadhyay/resume-forge
```

---

## 9. Direct GitHub REST & GraphQL API (`gh api`)

When no built-in `gh` subcommand exists, `gh api` executes authenticated API queries directly:

### REST API Examples
```bash
# Get repository metadata:
gh api repos/kanishk-upadhyay/resume-forge

# Get repository contributors:
gh api repos/kanishk-upadhyay/resume-forge/contributors

# Trigger repository dispatch event:
gh api repos/kanishk-upadhyay/resume-forge/dispatches -X POST -f event_type="build_all"
```

### GraphQL API Examples
```bash
# Fetch latest 5 pull request titles and authors:
gh api graphql -f query='
query {
  repository(owner: "kanishk-upadhyay", name: "resume-forge") {
    pullRequests(first: 5, states: OPEN) {
      nodes {
        number
        title
        author { login }
      }
    }
  }
}'
```

---

## 10. Agent Skills Management (`gh skill`)

GitHub CLI (`gh` v2.90+) natively implements the open **Agent Skills** specification:
```bash
# Search available agent skills across GitHub:
gh skill search latex

# Install an agent skill from a repository into user or project scope:
gh skill install github/awesome-copilot git-commit --agent antigravity --scope user

# List all installed skills for all coding agents:
gh skill list

# Update all installed agent skills to latest versions:
gh skill update --all
```

---

## 11. Troubleshooting & Common Failure Modes

### 1. `ssh: connect to host github.com port 22: Operation not permitted`
- **Cause:** Network egress is blocked by a local firewall, sandbox, or port 22 is filtered by the ISP/network.
- **Solution:** Test SSH over the HTTPS port (port 443):
  Add this to `~/.ssh/config`:
  ```ssh
  Host github.com
    Hostname ssh.github.com
    Port 443
    User git
  ```
  Test with: `ssh -T -p 443 git@ssh.github.com`

### 2. `HTTP 401: Requires authentication` on `gh` commands
- **Cause:** The stored CLI token has expired or was revoked.
- **Solution:** Re-authenticate:
  ```bash
  gh auth login -h github.com
  ```

### 3. `fatal: remote origin already exists`
- **Solution:** Update the remote URL instead of adding:
  ```bash
  git remote set-url origin git@github.com:<username>/<repo>.git
  ```

### 4. `error: failed to push some refs to ... (fetch first)`
- **Solution:** Remote has commits not present locally. Rebase without merge commit clutter:
  ```bash
  git pull --rebase origin main
  git push origin main
  ```
