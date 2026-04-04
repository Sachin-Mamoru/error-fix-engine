# Git error: failed to push some refs – remote contains work you do not have
> Encountering this Git push error means your remote branch has commits your local branch lacks; this guide explains how to fix it.

## What This Error Means

When you encounter the message "Git error: failed to push some refs – remote contains work you do not have," it signifies that your attempt to push local changes to a remote Git repository was rejected. This isn't a failure of Git itself, but rather Git's protective mechanism at work. It means that the remote branch you're trying to push to has commits that are not present in your local branch. In simpler terms, your local branch is "behind" the remote branch.

Git operates on a principle where it won't allow a "non-fast-forward" push by default. A fast-forward push happens when your local branch contains all the commits of the remote branch, plus some new ones. In this scenario, Git can simply append your new commits to the remote's history without any ambiguity. However, when the remote has commits you don't have, a direct push would effectively overwrite or diverge the remote's history, potentially losing work. Git prevents this to maintain a linear and coherent commit history, requiring you to integrate the remote's changes locally first.

## Why It Happens

This error primarily occurs because the state of your local branch's history has diverged from the remote's history since your last `git pull` or `git fetch`. The most common reason is that another developer has pushed changes to the same branch on the remote repository before you. Git detects this divergence and refuses your push to prevent data loss or a messy history.

Another frequent scenario I've seen is working from multiple machines. If you push changes from your laptop, then try to push different changes from your desktop without first pulling the laptop's pushes to your desktop, you'll hit this error. Similarly, if you've performed a destructive operation locally, like a `git rebase` or `git reset --hard`, which rewrites your branch's history, and then attempt to push to a remote that already contains the "old" history, Git will reject it. Git's default behavior forces you to reconcile the differing histories before pushing. It's a critical safety net in collaborative environments.

## Common Causes

Understanding the specific scenarios that lead to this error can help in both prevention and troubleshooting. Here are the most common causes I've encountered in various projects:

1.  **Concurrent Development:** This is by far the most frequent cause. You and a teammate are working on the same branch (e.g., `develop` or a feature branch). Your teammate finishes their work, pushes it to the remote, and then you try to push your own changes. Since their commits are now on the remote and not in your local branch, your push is rejected.

2.  **Working from Multiple Machines:** As mentioned, if you're developing on a branch across different computers (e.g., a work desktop and a home laptop), and you push from one machine, then attempt to push from the other without pulling the latest changes, you'll face this error. The second machine's local history is now stale relative to the remote.

3.  **Local History Rewriting:**
    *   **Rebasing:** If you `git rebase` your local branch to incorporate changes from another branch (e.g., `main`), or to clean up your commit history, and then try to push that rebased branch to a remote where the *original* commits still exist, Git will see the history as divergent.
    *   **`git reset --hard`:** Using `git reset --hard` to revert to an earlier commit and then attempting to push might similarly lead to this error if those "reset" commits were already on the remote. Generally, rewriting history on branches that others are actively using is discouraged for this reason.

4.  **CI/CD Pipeline Updates:** In some setups, a CI/CD pipeline might have permissions to push changes back to a branch (e.g., updating a version file, generating documentation, or merging a sub-branch). If this happens between your last pull and your current push, your local branch will be behind.

5.  **Accidental Force Push:** Less common, but sometimes a force push (`git push --force` or `-f`) might have been performed from another source (another user, a script) that overwrote the remote history. If your local history is based on the *original* remote history, then your subsequent push will fail because your base commits are no longer recognized as ancestors of the remote's HEAD. This is a more problematic scenario as it implies history was lost or altered.

## Step-by-Step Fix

The standard and safest way to resolve the "remote contains work you do not have" error is to first integrate the remote's changes into your local branch, and then push your combined changes. This typically involves a `git pull` operation.

1.  **Check Your Current Status:**
    Before doing anything, always check the state of your repository. This helps confirm which branch you're on and if you have uncommitted changes.

    ```bash
    git status
    ```
    If you have uncommitted changes, you should `git add` and `git commit` them, or `git stash` them temporarily. Pushing uncommitted changes is not possible, and trying to pull with uncommitted changes might lead to issues.

2.  **Fetch the Latest Remote Changes:**
    It's good practice to `fetch` first to see what's changed on the remote without actually merging anything into your local branch.

    ```bash
    git fetch origin
    ```
    This updates your local copy of the remote tracking branches (e.g., `origin/main`, `origin/feature-branch`).

3.  **Review Differences (Optional but Recommended):**
    You can now compare your local branch with the remote's version to see what commits you're missing. Replace `your-branch-name` with the actual name of your branch (e.g., `main`, `develop`, `feature/my-task`).

    ```bash
    git log --oneline --graph --decorate origin/your-branch-name..HEAD
    ```
    This command shows commits that are in your local `HEAD` but *not* in `origin/your-branch-name`. If this command shows nothing, it means your local branch is behind. To see what the remote has that you don't, you'd reverse it:
    ```bash
    git log --oneline --graph --decorate HEAD..origin/your-branch-name
    ```
    This second command should now show the commits on the remote that you're missing, confirming the reason for the push failure.

4.  **Integrate Remote Changes Using `git pull`:**
    This is the crucial step. `git pull` is essentially a `git fetch` followed by a `git merge` (by default) or `git rebase`. For most straightforward cases, a simple `git pull` is sufficient.

    ```bash
    git pull origin your-branch-name
    ```
    *   **Merge (default):** `git pull` will attempt to merge the remote branch (`origin/your-branch-name`) into your local `your-branch-name`. If there are no conflicting changes, Git will automatically create a merge commit. If there are conflicts, Git will pause and prompt you to resolve them.
    *   **Rebase (alternative):** If you prefer a linear history and want to avoid merge commits, you can use `git pull --rebase`. This will take your local commits, stash them, pull the remote changes, and then reapply your stashed commits on top of the newly pulled history. This is often preferred in projects that aim for a clean, linear history. Be cautious with rebase if you've already shared your branch, as it rewrites history. In my experience, for feature branches that aren't shared widely yet, `rebase` makes for a much cleaner log.

5.  **Resolve Merge Conflicts (If Any):**
    If `git pull` results in merge conflicts, Git will tell you which files are conflicted.
    *   Open the conflicted files in your editor.
    *   Look for conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
    *   Manually edit the files to resolve the conflicts, choosing which changes to keep.
    *   After resolving each file, `git add <conflicted-file>` to mark it as resolved.
    *   Once all conflicts are resolved and added, `git commit` to complete the merge. Git will usually pre-populate a commit message for the merge; you can accept it or modify it.

6.  **Push Your Changes:**
    Once you've successfully integrated the remote changes and resolved any conflicts, your local branch now includes both your work and the remote's work. You can now push without error.

    ```bash
    git push origin your-branch-name
    ```

7.  **Verify:**
    Check your remote repository (e.g., GitHub, GitLab UI) to ensure your changes have been pushed successfully. A quick `git log` locally should also show the merged history.

## Code Examples

Here are the most common commands you'll use, ready to copy-paste. Replace `your-branch-name` with the actual branch you are working on.

**Standard Fix (Merge Strategy):**

1.  **Commit any outstanding local changes:**
    ```bash
    git add .
    git commit -m "My pending changes before pulling remote work"
    ```

2.  **Pull latest changes from the remote, merging them into your branch:**
    ```bash
    git pull origin your-branch-name
    ```
    *   *If conflicts arise, resolve them, `git add` the files, and `git commit` to finalize the merge.*

3.  **Push your updated local branch to the remote:**
    ```bash
    git push origin your-branch-name
    ```

**Alternative Fix (Rebase Strategy):**

1.  **Commit any outstanding local changes:**
    ```bash
    git add .
    git commit -m "My pending changes before rebasing remote work"
    ```

2.  **Pull latest changes from the remote, rebasing your local commits on top:**
    ```bash
    git pull --rebase origin your-branch-name
    ```
    *   *If conflicts arise during rebase, resolve them, then `git add` the files, and continue with `git rebase --continue`. If you need to stop, use `git rebase --abort`.*

3.  **Push your rebased local branch to the remote:**
    ```bash
    git push origin your-branch-name
    ```

**Viewing Remote Differences:**

To see what commits are on the remote that you don't have locally (after a `git fetch`):
```bash
git log HEAD..origin/your-branch-name
```

## Environment-Specific Notes

While the core Git commands remain consistent, the context in which you encounter and resolve this error can sometimes vary slightly across different development environments.

**Cloud Platforms (GitHub, GitLab, Bitbucket, Azure DevOps):**
*   **Protected Branches:** Many teams configure protected branches (e.g., `main`, `develop`) that prevent direct pushes, especially non-fast-forward pushes or force pushes. This means you *must* pull and merge/rebase locally. Trying to bypass the error with `git push --force` will simply be rejected by the server if the branch is protected.
*   **Pull Requests/Merge Requests:** This error often occurs when you're working on a feature branch, and the base branch (e.g., `main`) has been updated. Before submitting your PR, or if your PR goes stale, you'll need to pull the latest `main` into your feature branch to keep it up-to-date and pass CI checks. I've seen this in production when a CI/CD pipeline inadvertently pushed to a branch I was working on, requiring me to pull those changes before my own PR could be merged.
*   **Web IDEs/Integrated Editors:** If you're using a web-based IDE (like GitHub Codespaces or GitLab Web IDE), the Git operations are often abstracted. However, if you drop to a terminal within these environments, the same `git pull` and `git push` commands apply. The platform might even warn you that your branch is behind.

**Docker/Containerized Development:**
*   **Git inside Containers:** If your development workflow involves running Git commands *inside* a Docker container, ensure that the Git client within the container is properly configured (e.g., `user.name`, `user.email`). The `.git` directory is usually mounted from your host machine into the container, so the repository's state is shared.
*   **Host vs. Container Git:** More commonly, you'll be using Git on your *host* machine to interact with the repository, even if your application code runs in containers. The error itself is typically a host-side problem. Be mindful if your workflow involves building Docker images that embed Git repositories – ensure the `git clone` or `git pull` operations within your Dockerfile or build script are always getting the very latest version to avoid building from stale code.

**Local Development Environment:**
*   This is where the standard `git pull` and `git push` approach directly applies. There are no additional layers of abstraction or server-side protections to consider beyond what's configured for the remote repository itself.
*   The only potential difference is if you're working with local-only Git repositories (without a remote), but this error specifically refers to a "remote," so it's less relevant in that context. However, it can manifest if you treat different local clones as "remotes" and accidentally diverge their histories.

## Frequently Asked Questions

**Q: Can I just use `git push --force` to override this error?**
**A:** While `git push --force` (or `git push -f`) would technically allow you to push and overwrite the remote's history with your local history, it is almost always a bad idea for branches that other developers are working on. This can lead to lost work for others and create significant headaches as they try to reconcile their local copies with your force-pushed, rewritten history. Only use `git push --force` if you are absolutely certain you understand the implications, are pushing to a personal or isolated branch, or are intentionally rewriting shared history after coordinating with your team.

**Q: What is the difference between `git pull` and `git pull --rebase` in this context?**
**A:** `git pull` (by default) performs a `git fetch` followed by a `git merge`. This creates a new merge commit in your history, explicitly showing where the remote changes were integrated. `git pull --rebase` performs a `git fetch` followed by a `git rebase`. This rewrites your local commits to apply them *on top* of the remote's latest history, resulting in a cleaner, linear history without extra merge commits. It's often preferred for feature branches before merging into `main`.

**Q: How can I prevent this error from happening frequently?**
**A:**
1.  **Pull Frequently:** Make it a habit to `git pull` before you start working each day, and periodically throughout the day, especially before pushing.
2.  **Communicate:** Coordinate with your team. If you're working on a shared branch, let others know when you're about to push significant changes.
3.  **Use Feature Branches:** For most substantial work, create a dedicated feature branch. This isolates your changes and minimizes conflicts with the main development line until your work is ready.
4.  **Avoid Destructive History Rewriting:** Unless absolutely necessary and coordinated, avoid `git rebase` or `git reset --hard` on branches that have already been pushed to a remote and are being used by others.

**Q: My `git pull` says "Already up to date", but `git push` still fails. What now?**
**A:** This is rare, but can indicate a few things:
    *   **Incorrect Tracking Branch:** Your local branch might not be tracking the correct remote branch. Check with `git branch -vv`. If it's tracking the wrong one, you can reset it using `git branch --set-upstream-to=origin/correct-remote-branch your-local-branch`.
    *   **Diverged Branches (Rare Edge Case):** In very specific circumstances, your local and remote branches might have diverged, with commits unique to both, but `git pull` isn't seeing a direct merge path without more intervention. A `git fetch origin` followed by `git rebase origin/your-branch-name` might resolve it, but proceed with caution.
    *   **Stale Local Cache:** Try refreshing your remote cache: `git remote update origin --prune`.

## Related Errors

- [git-merge-conflict](/errors/git-merge-conflict.html)
- [git-detached-head](/errors/git-detached-head.html)