# Git error: failed to push some refs – remote contains work you do not have
> Encountering Git's "failed to push some refs – remote contains work you do not have" means your local branch is out of sync with the remote, preventing direct pushes; this guide explains how to fix it.

## What This Error Means

This Git error indicates a fundamental mismatch between your local branch's history and its corresponding remote branch. When you attempt to `git push`, Git compares your local commit history with the remote. If Git discovers that the remote branch has commits that are *not* present in your local branch – meaning someone else (or even you, from another machine) has pushed changes to the remote since your last `git pull` – it will refuse your push.

The phrase "failed to push some refs" refers to Git's inability to update the reference (the pointer to the latest commit) for your branch on the remote repository. "Remote contains work you do not have" explicitly states the reason: your local branch is behind the remote, and Git prevents a "non-fast-forward" push to avoid overwriting or losing the remote's newer history. It's Git's way of safeguarding the integrity of the shared codebase.

## Why It Happens

At its core, this error occurs because Git is a distributed version control system. Developers work concurrently, often on the same branches. When you `git clone` or `git pull`, you get a snapshot of the remote repository at that moment. However, the remote repository is a living entity, constantly being updated by other team members' pushes.

When your local copy of a branch falls behind the remote version of that same branch, Git flags this discrepancy. Your local branch's tip commit is no longer a direct ancestor of the remote branch's tip commit. To allow your changes to be pushed, your local history must first incorporate the remote's new commits. This ensures a linear, coherent history or at least a clearly recorded merge, preventing accidental loss of work.

## Common Causes

In my experience, this error is one of the most frequent Git issues developers encounter, especially in collaborative environments. Here are the common scenarios that lead to it:

*   **Coworker Pushed Changes:** This is the most prevalent cause. While you were working on your local changes, a teammate committed and pushed their own changes to the same remote branch you're trying to push to. Your local branch is now "stale" relative to the remote.
*   **You Pushed from Another Machine:** I've definitely done this: working on a feature on my desktop, pushing, then trying to push from my laptop later without first pulling the changes I made on my desktop. Git sees the laptop's branch as behind.
*   **CI/CD Pipeline Updates:** Sometimes, automated processes (like a CI/CD pipeline) might push a version bump, a build artifact, or a deployment tag directly to your branch (or a related branch) on the remote. If your local copy hasn't fetched those changes, you'll hit this error.
*   **Remote Branch Rewritten (Rare on Protected Branches):** In less common scenarios, someone might have force-pushed (`git push --force`) to the remote branch, completely rewriting its history. If your local history doesn't match this new, rewritten remote history, you'll encounter this error. This usually only happens on personal or very temporary branches, as most `main` or `develop` branches are protected from force pushes.
*   **Forgetfulness (Been there!):** Simply forgetting to run `git pull` before starting new work or attempting to push. It's a routine I try to enforce for myself before any major coding session.

## Step-by-Step Fix

The solution involves bringing your local branch up to date with the remote's history. There are two primary strategies for integrating remote changes: **merge** and **rebase**. Both will resolve the "remote contains work you do not have" error, but they handle your branch's history differently.

First, ensure you are on the correct branch and your working directory is clean.

1.  **Check Your Branch and Status:**
    Always start by confirming your current branch and whether you have any uncommitted changes. This is a critical step to avoid losing work or making a mess.

    ```bash
    git status
    git branch --show-current
    ```

    If `git status` shows uncommitted changes, you have two options:
    *   **Commit them:** If they are ready, commit them to your local branch: `git add . && git commit -m "My pending changes"`
    *   **Stash them:** If you're not ready to commit, stash them temporarily: `git stash save "Work in progress"` (You'll need to `git stash pop` or `git stash apply` later).

2.  **Fetch the Latest Remote Changes:**
    Before merging or rebasing, always `fetch` the latest changes from the remote. This updates your local `origin/your-branch` tracking reference without modifying your local working branch.

    ```bash
    git fetch origin
    ```

    Now, your local Git repository knows about all the new commits on the remote.

3.  **Inspect the Divergence (Optional but Recommended):**
    To understand what you're about to do, you can visualize the differences:

    ```bash
    git log --oneline --graph --all
    # Or to see commits on remote that aren't local:
    git log your-branch..origin/your-branch
    # And commits on local that aren't remote:
    git log origin/your-branch..your-branch
    ```

    This helps clarify if you have unique local commits and what new commits are on the remote.

4.  **Integrate Remote Changes (Choose One Option):**

    *   ### Option A: `git pull --rebase` (Preferred for clean, linear history)
        This command fetches changes and then reapplies your local commits *on top* of the fetched remote changes. It creates a linear history, making it look like you started your work *after* the remote's latest changes. This is generally preferred for feature branches to keep the history clean before merging into `main`.

        ```bash
        git pull --rebase origin your-branch
        ```

        **Conflict Resolution with Rebase:**
        If there are conflicts, Git will pause the rebase.
        *   Edit the conflicting files to resolve the differences.
        *   Mark them as resolved: `git add <conflicted-file>`
        *   Continue the rebase: `git rebase --continue`
        *   To abort the rebase at any point: `git rebase --abort`

    *   ### Option B: `git pull` (Merges remote changes, preserves history)
        This command fetches changes and then creates a new merge commit in your local branch, combining the remote's history with your local history. This preserves the exact history of *when* you branched and merged, but it can create a more "jagged" history with many merge commits, especially if done frequently.

        ```bash
        git pull origin your-branch
        ```

        **Conflict Resolution with Merge:**
        If there are conflicts, Git will pause the merge.
        *   Edit the conflicting files to resolve the differences.
        *   Mark them as resolved: `git add <conflicted-file>`
        *   Continue the merge: `git merge --continue`
        *   To abort the merge at any point: `git merge --abort`

5.  **Push Your Changes:**
    Once you've successfully integrated the remote changes (either via rebase or merge) and resolved any conflicts, your local branch is now up to date and contains all the remote's history plus your own changes. You can now push.

    ```bash
    git push origin your-branch
    ```

    If you rebased your branch, you are effectively pushing a *new* history that replaces your old local history. Since the remote hasn't seen this specific rebased history before, your `git push` will likely be a fast-forward or a simple update.

## Code Examples

Here are some concise, copy-paste ready examples of the commands you'll typically use:

**1. Checking status and current branch:**
```bash
git status
git branch --show-current
```

**2. Stashing uncommitted changes:**
```bash
git stash save "WIP on current feature before pulling"
```

**3. Fetching latest remote changes:**
```bash
git fetch origin
```

**4. Resolving the error using `pull --rebase` (recommended):**
```bash
git pull --rebase origin your-branch-name
```
*If conflicts:*
```bash
# ... resolve conflicts in files ...
git add conflicted-file-1.js conflicted-file-2.ts
git rebase --continue
```
*If you need to give up on the rebase:*
```bash
git rebase --abort
```

**5. Resolving the error using `pull` (merge):**
```bash
git pull origin your-branch-name
```
*If conflicts:*
```bash
# ... resolve conflicts in files ...
git add conflicted-file-1.js conflicted-file-2.ts
git merge --continue
```
*If you need to give up on the merge:*
```bash
git merge --abort
```

**6. Pushing after successful pull/rebase:**
```bash
git push origin your-branch-name
```

**7. Reapplying stashed changes (if you stashed earlier):**
```bash
git stash pop
# Or if you want to keep the stash:
git stash apply
```

## Environment-Specific Notes

While the core Git commands remain the same, how you encounter and manage this error can vary slightly depending on your environment and workflow.

*   **Cloud Hosting (GitHub, GitLab, Bitbucket):** These platforms often enforce branch protection rules, especially for `main` or `develop` branches. These rules typically prevent direct pushes to the branch and require changes to come in via approved Pull Requests (PRs) or Merge Requests (MRs). When working on a feature branch destined for a PR/MR, you're expected to keep your feature branch up-to-date with the target branch (e.g., `main`) frequently. This often involves pulling/rebasing `main` into your feature branch. The "remote contains work you do not have" error here usually means your feature branch on the remote is behind another copy of itself, or behind the target branch if you're trying to push directly to a target branch without a PR.

*   **Docker Development:** If you're developing inside a Docker container, your Git client within the container is typically isolated.
    *   Ensure your `~/.gitconfig` and credentials are correctly mounted or configured inside the container if you're performing Git operations from within it.
    *   The error itself means the same thing, but the *cause* might sometimes be that your container's Git state is stale, or that a build process within the container modified the repo. My advice: generally, keep Git operations on the host machine where possible, and only perform `git clone` or `git pull` from within the container if strictly necessary for a build step. If your `git push` fails from within a container, it's almost certainly because the container's version of the repo is behind the remote, and the fix is the same: `git pull --rebase`.

*   **Local Development with Multiple Machines:** As mentioned earlier, pushing from one machine, then trying to push from another without syncing first, is a common trap. The key is to treat each machine as a distinct "developer" when it comes to Git syncing. Always `git pull --rebase` on the machine you're about to work on before making new commits, and *definitely* before pushing. I've found that consistency across my devices saves a lot of headaches here.

## Frequently Asked Questions

**Q: Can I just force push (`git push --force`) to fix this?**
**A:** No, not generally. Force pushing (`git push --force` or `git push --force-with-lease`) overwrites the remote history with your local history. If other developers have based their work on the "old" remote history, force pushing will cause them significant problems, including potentially losing their work or requiring complex rebases on their end. Only use `git push --force-with-lease` on branches that *only you* are working on and where you are absolutely certain no one else has pulled from it since your last push (e.g., after you've performed a rebase on your local branch that rewrites its history). For shared branches, always pull and integrate changes.

**Q: What's the difference between `git pull` and `git pull --rebase`?**
**A:** `git pull` is shorthand for `git fetch` followed by `git merge`. It downloads remote changes and then creates a *merge commit* to combine the remote's history with your local commits. This preserves the exact history of both branches but can result in a "messier" graph with many merge commits. `git pull --rebase` is shorthand for `git fetch` followed by `git rebase`. It downloads remote changes and then "replays" your local commits *on top* of the new remote history. This creates a clean, linear history, making it look as if you started your work *after* the latest remote commits. It's generally preferred for feature branches to keep the history tidy.

**Q: What if I have uncommitted changes when I try to `git pull` or `git pull --rebase`?**
**A:** Git will typically prevent the operation, warning you about uncommitted changes. The safest approach is to `git stash` your changes first (`git stash save "WIP"`). After successfully pulling/rebasing, you can then `git stash pop` to reapply your changes. This ensures your work-in-progress isn't accidentally overwritten or causes conflicts during the pull/rebase process.

**Q: How can I avoid this error in the future?**
**A:** The best way is proactive syncing.
1.  **Pull Frequently:** Make it a habit to `git pull --rebase` before you start any significant work session and periodically throughout the day, especially if you're on a shared branch.
2.  **Communicate:** Talk to your team. Knowing who's working on what and when they plan to push can help avoid simultaneous pushes to the same branch.
3.  **Feature Branches:** Work on dedicated feature branches that diverge from `main`/`develop` and integrate `main`/`develop` frequently into your feature branch (via rebase) to keep it updated.
4.  **Use `git push --force-with-lease` cautiously:** If you absolutely need to rewrite history on a branch (e.g., you rebased your own feature branch), use `git push --force-with-lease` instead of `--force`. This provides a safeguard, ensuring you only force push if the remote branch hasn't changed since you last fetched.

**Q: My remote tracking branch is out of sync (e.g., `origin/my-branch` refers to a deleted remote branch). How do I clean that up?**
**A:** Sometimes a remote branch is deleted, but your local Git still has a reference to `origin/my-branch`. You can prune these stale remote-tracking branches with:
```bash
git fetch --prune origin
```
Or simply:
```bash
git remote prune origin
```

## Related Errors