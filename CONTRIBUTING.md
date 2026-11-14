# Contributing to CareLoop

We are a team of four. There are **no fixed roles**: anyone can pick up any issue. Work is grouped into **workstreams** (labels), and every change goes through a pull request that someone else reviews.

## Ground rules

1. **Never commit real patient data.** Only synthetic data belongs in this repository.
2. **Never commit secrets** (keys, passwords, tokens). Use `.env` locally; only `.env.example` is committed.
3. **Nobody commits directly to `main`.** Use a branch and a pull request.
4. **No claims without evidence.** Do not describe a feature as working, validated or integrated unless it is. Mark assumptions as assumptions.
5. **AI may draft, never decide.** See [docs/SECURITY_AND_PRIVACY.md](docs/SECURITY_AND_PRIVACY.md).

## Workflow, step by step

You need Git installed and a GitHub account that has been invited to the repository.

```bash
# 1. Clone (download) the repository once
git clone https://github.com/Maureen13-d/CareLoop.git
cd CareLoop
code .                      # opens the folder in VS Code

# 2. Start each work session by getting the latest main
git switch main             # move to the main branch
git pull                    # download the newest changes

# 3. Create a branch for ONE issue
git switch -c feature/case-state-machine

# 4. Work on the task, then check what changed
git status                  # lists changed files
git diff                    # shows the exact changes

# 5. Save a snapshot (commit)
git add path/to/changed-file.py     # choose which files go in the snapshot
git commit -m "feat: add case state machine (#12)"

# 6. Send your branch to GitHub
git push -u origin feature/case-state-machine
```

7. **Open a pull request (PR):** GitHub shows a "Compare & pull request" button after you push. Fill in the template and write `Closes #12` so the issue closes when the PR merges.
8. **Review:** a teammate opens the PR, reads the "Files changed" tab, leaves comments, then clicks **Approve** or **Request changes**.
9. **Merge:** once approved and conversations are resolved, click **Squash and merge**, then **Delete branch**.
10. **Update your laptop:** `git switch main` then `git pull`.

If `git pull` or a PR reports a **merge conflict**, two people edited the same lines. Open the file, keep the right version, remove the `<<<<<<<` markers, then `git add` and `git commit`. Ask a teammate if unsure.

## Branch names

`type/short-description`, for example `feature/overdue-check`, `fix/login-redirect`, `docs/architecture`, `task/seed-script`.

## Commit messages

`type: short summary (#issue)`, with types `feat`, `fix`, `docs`, `test`, `chore`, `refactor`.

## Pull request rules

- One issue, one branch, one PR. Keep PRs small.
- Someone other than the author reviews. Aim to review within a few hours.
- Squash and merge. Delete the branch afterwards.
- Run the tests locally before opening a PR (once tests exist).

## Staying out of each other's way

- Work inside your module's folder. Backend modules talk to each other only through their service functions, never by reading each other's tables.
- Agree API shapes in `docs/API_DOCUMENTATION.md` (via a PR) before building both sides.
- Change shared files (README, ARCHITECTURE, requirements) in small, quick PRs.
- Need a change in someone else's module? Comment on their issue or open a new one.

## Labels

| Family | Labels |
|---|---|
| Workstream | `ws:case-engine`, `ws:records-referrals`, `ws:frontend`, `ws:data-ai`, `ws:docs-governance`, `ws:platform` |
| Type | `type:feature`, `type:bug`, `type:task`, `type:docs` |
| Priority | `P0-must`, `P1-should`, `P2-could` |
| Other | `blocked`, `needs-review`, `good-first-issue` |

`scripts/create_labels.sh` creates them if you have the GitHub CLI (`gh`) installed and logged in. Otherwise create them by hand under **Issues > Labels**.

## Milestones

M1 Foundation (15 Nov), M2 Core loop (17 Nov), M3 Demo-ready (19 Nov), M4 Submission (20 Nov). See [project-management/MILESTONES.md](project-management/MILESTONES.md).
