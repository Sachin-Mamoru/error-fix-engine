# Git error: failed to push some refs – remote contains work you do not have
> Encountering "failed to push some refs – remote contains work you do not have" means your local branch is behind the remote; this guide explains how to fix it efficiently.

## What This Error Means

This Git error indicates that your local branch's history has diverged from its corresponding remote branch. Specifically, the remote branch contains commits that are not present in your local branch. When you attempt to push your local changes, Git identifies that doing so would overwrite or lose work that already exists on the remote, hence the "remote contains work you do not have" message. It's a protective mechanism: Git prevents a non-fast-forward push by default when the remote has new commits. Your local repository lacks the upstream changes, making a direct push impossible without first integrating those changes.

## Why It Happens

At its core, this error occurs because your local branch is out of sync with its upstream counterpart. Git repositories are distributed, and multiple developers often work on the same branches simultaneously. When someone else pushes changes to the same branch you're working on, your local copy instantly becomes outdated.

The `git push` command attempts to update the remote reference (e.g., `origin/main`) to match your local reference (e.g., `main`). If your local reference's commit history does not directly extend the remote's reference (i.e., your local branch doesn't "fast-forward" from the remote), Git blocks the push. This typically happens because new commits have been added to the remote branch since your last `git pull` or `git fetch`. You effectively have a "stale" view of the remote.

In my experience, this is one of the most common Git errors faced by developers, especially those working in collaborative environments with frequent commits to shared branches. It's a signal that you need to synchronize your work before contributing new changes.

## Common Causes

Several scenarios frequently lead to this "failed to push" error:

1.  **Forgot to pull:** This is the most prevalent cause. You started working, made some commits, and then tried to push without first running `git pull` to fetch and integrate any changes made by teammates.
2.  **Team member pushed new work:** While you were developing locally, a colleague pushed their own changes to the same remote branch. Your local branch is now behind.
3.  **Local commits after an outdated `git fetch`:** You might have run `git fetch` to see remote changes but didn't `git merge` or `git rebase` them into your local branch before creating new commits.
4.  **Rebasing the remote branch (uncommon but possible):** In some advanced scenarios, if a shared remote branch was rebased and force-pushed by another developer, your local history would then fundamentally diverge from the rebased remote history. This is generally discouraged on shared branches.
5.  **Working on multiple machines:** If you pushed from one machine, then started working on another machine without pulling those changes, and then tried to push new work from the second machine.

I've seen this in production when a CI/CD pipeline fails because a developer pushes directly to `main` without pulling, and the pipeline's subsequent attempt to fetch/merge fails, or a deployment script tries to push its own changes back to the repo, only to find it's out of date.

## Step-by-Step Fix

The fundamental solution is to bring your local branch up to date with the remote branch before attempting to push your changes. This typically involves fetching the remote changes and then integrating them into your local branch, usually through a merge or a rebase.

Here’s a robust step-by-step approach:

1.  **Ensure you're on the correct branch:**
    Always verify you are on the branch you intend to push.

    ```bash
    git status
    ```
    This command will show your current branch and any uncommitted changes. If you have uncommitted changes, you should `git add` and `git commit` them or `git stash` them temporarily.

2.  **Fetch the latest changes from the remote:**
    This updates your remote-tracking branches (e.g., `origin/main`) without modifying your local working branch.

    ```bash
    git fetch origin
    ```
    Replace `origin` with your remote name if it's different. This step is crucial for getting an accurate picture of what's on the remote.

3.  **Decide on Integration Strategy: `git pull --rebase` vs. `git pull --merge`:**
    This is the critical decision point.

    *   **`git pull --rebase` (Recommended for cleaner history):**
        This command fetches the remote changes and then "replays" your local commits on top of the updated remote branch. It creates a linear history, making it look as if you developed your changes *after* the remote's latest commits. This is generally preferred for feature branches to maintain a clean, linear project history.
        **Use this if:** You want a clean, linear history and are comfortable resolving potential conflicts during the rebase process.

        ```bash
        git pull --rebase origin <your-branch-name>
        ```
        (e.g., `git pull --rebase origin main`)

    *   **`git pull --merge` (Default behavior, adds a merge commit):**
        This command fetches the remote changes and then merges them into your local branch, creating a new merge commit. This preserves the exact history of both branches but can result in a "messy" history with many merge commits if done frequently.
        **Use this if:** You prefer to explicitly record the merge event, or if you're on a very long-lived branch where a rebase might be too disruptive.

        ```bash
        git pull origin <your-branch-name>
        ```
        (e.g., `git pull origin main` which is shorthand for `git pull --merge origin main`)

4.  **Resolve Conflicts (if any):**
    If there are conflicting changes between your local commits and the remote commits, Git will pause the rebase/merge process and prompt you to resolve them.

    *   Use `git status` to see which files have conflicts.
    *   Open the conflicting files, resolve the differences manually (Git marks conflict sections with `<<<<<<<`, `=======`, `>>>>>>>`).
    *   After resolving conflicts in a file, stage it:
        ```bash
        git add <conflicted-file>
        ```
    *   Continue the rebase/merge:
        For rebase:
        ```bash
        git rebase --continue
        ```
        For merge:
        ```bash
        git commit -m "Merge remote-tracking branch 'origin/main' into main"
        ```
        (Git often pre-populates a merge commit message for you).

5.  **Push your changes:**
    Once your local branch is fully synchronized with the remote, you can now push your commits.

    ```bash
    git push origin <your-branch-name>
    ```
    (e.g., `git push origin main`)

    This push should now succeed because your local branch's history now properly incorporates the remote changes, allowing for a fast-forward update or a standard merge commit push.

## Code Examples

Here are the most common commands you'll use:

**Scenario 1: Standard pull with merge (default)**

```bash
# First, ensure your working directory is clean or commit/stash your changes
git status

# Fetch and merge remote changes into your current branch
git pull origin main
# If conflicts arise, resolve them, then:
# git add .
# git commit -m "Resolved merge conflicts"

# Then push your combined changes
git push origin main
```

**Scenario 2: Pull with rebase (recommended for linear history)**

```bash
# First, ensure your working directory is clean or commit/stash your changes
git status

# Fetch remote changes and reapply your local commits on top
git pull --rebase origin feature/my-new-feature
# If conflicts arise during rebase, resolve them, then:
# git add .
# git rebase --continue
# Repeat until rebase is complete. If you need to stop: git rebase --abort

# Then push your rebased changes
git push origin feature/my-new-feature
```

**Scenario 3: Fixing after a previous failed push attempt**

```bash
# You just got the "failed to push" error
# 1. Fetch remote changes to update your remote-tracking branches
git fetch origin

# 2. Rebase your local branch onto the updated remote branch
#    (assuming you want a clean history)
git rebase origin/main # or origin/your-branch

# 3. Resolve any conflicts during the rebase
#    git status (to see conflicts)
#    (edit files)
#    git add <conflicted-file-1> <conflicted-file-2>
#    git rebase --continue

# 4. Push your now synchronized local branch
git push origin main
```

## Environment-Specific Notes

The core Git commands remain consistent across different environments, but how you encounter or manage this error can vary slightly.

*   **Cloud Git Providers (GitHub, GitLab, Bitbucket):** These platforms are just remote Git servers. The error message originates from Git itself, not the platform. However, the platform's UI might show you that your branch is "behind" or "diverged" from the default branch, visually reinforcing the CLI error. You'll still use the same `git pull` and `git push` commands locally. Some platforms offer "sync" buttons in their UI, which often perform a merge behind the scenes, potentially without an explicit rebase option. When I'm working with cloud providers, I always default to the CLI for fine-grained control over merge vs. rebase.
*   **Docker/CI/CD Pipelines:** In a CI/CD context, this error can halt builds or deployments. If a pipeline step involves pushing changes (e.g., updating a version file, pushing build artifacts), and the pipeline's local clone isn't up-to-date, it will fail.
    *   **Prevention:** Ensure your CI/CD scripts always start by pulling the latest changes (`git pull --ff-only` to ensure no divergence, or simply `git fetch && git merge origin/main`) *before* making any new commits or attempting to push.
    *   **Example:** A build script that increments a version number and tries to push it back. If another build beat it to the push, or a developer pushed, the second build will fail to push.
*   **Local Development:** This is where you'll most frequently encounter and resolve the error. It highlights the importance of regular `git pull` operations, especially when collaborating on shared branches. I've often seen junior developers forget to pull for hours, leading to larger, more complex merge conflicts when they finally synchronize. Establish a habit of `git pull --rebase` at the start of your day and periodically throughout.

## Frequently Asked Questions

**Q: Should I always use `git pull --rebase`?**
A: Not always, but often. `git pull --rebase` creates a linear history which is generally preferred for feature branches as it makes the commit history cleaner and easier to follow. However, if you are on a public branch (like `main`) and other developers have already based their work on your commits, rebasing that branch can rewrite history and cause problems for them. For shared, stable branches, `git pull` (which merges by default) is safer to avoid rewriting history that others depend on.

**Q: What if I accidentally force-pushed (`git push -f`) and caused this for others?**
A: If you force-pushed a rebased branch, you've rewritten history. Other developers will now get this error because their local branch history no longer matches the remote. They will need to run `git fetch` and then either `git reset --hard origin/<branch-name>` (if they haven't committed any work they want to keep) or `git pull --rebase` followed by careful conflict resolution (if they have local commits they want to save). This is why force-pushing shared branches is generally discouraged.

**Q: Can this error be avoided entirely?**
A: While it can't be entirely avoided in a collaborative environment (unless you're the sole developer on a repo), its frequency can be minimized. Best practices include:
    *   **Frequent `git pull`s:** Pull before you start work, and periodically throughout the day.
    *   **Small, frequent commits:** Smaller changes mean less chance of large, complex conflicts.
    *   **Work on feature branches:** Avoid direct commits to `main` or `develop`.

**Q: What's the difference between `git fetch` and `git pull`?**
A: `git fetch` downloads changes from the remote repository to your local repository, but it *does not* integrate them into your working branch. It updates your remote-tracking branches (e.g., `origin/main`). `git pull` is essentially `git fetch` followed by either `git merge` or `git rebase` of the fetched changes into your current local branch. Using `git fetch` first allows you to inspect changes before integrating them, offering more control.

**Q: I have untracked files, how does that affect this error?**
A: Untracked files typically don't directly cause this "failed to push" error. Git is concerned with committed changes. However, if you have uncommitted changes (modified but not staged or committed files), `git pull --rebase` might refuse to run or `git pull --merge` might create conflicts with your unstaged changes. Always `git stash` or `git commit` your work before attempting a `git pull` operation to avoid losing progress or complicating the synchronization process.

## Related Errors
*(none)*