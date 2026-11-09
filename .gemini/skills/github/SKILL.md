---
name: github
description: Authoritative guide and workflows for GitHub CLI (gh) and Git over SSH/HTTPS. Use when creating repos, managing remotes, pushing branches, configuring SSH auth, or managing GitHub Actions and releases directly from the terminal.
license: MIT
metadata:
  author: Antigravity
  last-updated: '2026-11-09'
  keywords:
  - github
  - gh
  - git
  - ssh
  - repository
  - actions
---

## Overview

This skill equips agents with complete, expert knowledge for interacting with GitHub directly from the terminal using the **GitHub CLI (`gh`)** and **Git over SSH / HTTPS**.

---

## 1. Creating & Uploading Repositories 100% in the Terminal

### Method A: Single-Command Creation & Push via GitHub CLI (`gh`)
If you have a local directory with git initialized and committed, create the remote repo and push in one shot:
```bash
# Public repository:
gh repo create resume-forge --public --source=. --remote=origin --push

# Private repository:
gh repo create resume-forge --private --source=. --remote=origin --push
```

### Method B: Git over SSH
If the remote repository already exists on GitHub or was created via API/browser:
```bash
# 1. Set SSH remote origin
git remote set-url origin git@github.com:<username>/<repo>.git

# 2. Push default branch (main)
git push -u origin main
```

---

## 2. GitHub CLI (`gh`) Authentication & SSH Setup

### Checking Authentication
```bash
# Check current authentication status:
gh auth status

# Re-authenticate if token is expired or missing:
gh auth login -h github.com
# Choose: GitHub.com -> SSH (or HTTPS) -> Paste token or Authenticate via browser
```

### Checking & Testing SSH Connection
```bash
# Test SSH connectivity to GitHub:
ssh -T git@github.com
# Expected output: "Hi <username>! You've successfully authenticated, but GitHub does not provide shell access."

# If key is missing from SSH agent:
ssh-add ~/.ssh/id_ed25519
# or
ssh-add ~/.ssh/id_rsa
```

---

## 3. Common Terminal Workflows

### GitHub Actions & Workflows
```bash
# List workflow runs:
gh run list -R <org>/<repo>

# View specific run logs:
gh run view <run-id> -R <org>/<repo>

# Trigger manual workflow dispatch:
gh workflow run deploy-pages.yml --ref main -R <org>/<repo>
```

### Releases & Tags
```bash
# Create a release with attached artifacts:
gh release create v1.0.0 output/*.pdf --title "v1.0.0 - Production Release" --notes "Initial release"
```

### Pull Requests & Issues
```bash
# Create a pull request:
gh pr create --title "Feature description" --body "Details"

# Check PR status:
gh pr status
```
