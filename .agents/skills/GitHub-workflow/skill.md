---
name: github-sync-before-edit
description: Always sync with GitHub before editing code, then commit and push changes automatically.
---

# GitHub Sync Before Every Code Edit

Whenever you are about to modify any project files, you MUST follow this workflow.

## Rules

1. Detect whether the current project is a Git repository.
2. If it is a Git repository:
   - Run `git pull` from the current branch before making any edits.
   - Resolve any merge conflicts if they occur before continuing.
3. After pulling:
   - Read the latest version of any files you are going to modify.
   - Make your requested changes on the newest version.
4. When editing is complete:
   - Review the modified files.
   - Stage all changes.
   - Generate a short, meaningful English commit message describing the changes.
   - Commit the changes.
   - Push them to the current remote branch.

## Git Commands

```bash
git pull
# Edit files
git add .
git commit -m "<generated English commit message>"
git push
```

## Commit Message Rules

- Always write the commit message in English.
- Keep it short and descriptive.
- Examples:
  - Fix login validation
  - Update dashboard UI
  - Refactor API service
  - Improve error handling
  - Add settings page
  - Fix responsive layout

## Important

- Never edit project files before completing `git pull`.
- Always work on the latest remote version.
- Always push the commit after successful completion unless the user explicitly says not to commit or not to push.
- If `git pull` fails, stop and explain the issue before making any edits.
- If the project is not a Git repository, inform the user and continue editing normally.