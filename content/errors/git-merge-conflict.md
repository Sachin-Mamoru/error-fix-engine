# Git merge conflict – Automatic merge failed; fix conflicts
> Encountering "Automatic merge failed" means Git cannot automatically reconcile diverging changes between branches; this guide explains how to fix it.

## What This Error Means

This error message, "Automatic merge failed; fix conflicts," is Git's way of telling you that it tried to combine two sets of changes from different branches, but encountered a situation where it couldn't decide which change to keep. Specifically, it means that the same lines of code (or lines very close to each other) in the same file have been modified differently in the branches you're trying to merge. Git is smart, but it's not intelligent enough to understand your intent, so it pauses the merge process and asks for your human intervention to resolve the ambiguities.

You'll typically see output similar to this after a `git merge` or `git pull` command:

```
Automatic merge failed; fix conflicts and then commit the result.
```

And `git status` will show files that are "unmerged":

```bash
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abandon the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
        both modified:   src/feature.js
        both modified:   docs/README.md
```

The files listed under "Unmerged paths" are the ones you need to manually resolve.

## Why It Happens

Git merges branches by comparing their commit histories to find a common ancestor. From that ancestor, it identifies changes unique to each branch. When these unique changes are applied to the *same content* within the *same file*, Git hits a wall.

Imagine two branches, `main` and `feature-A`. Both started from the same point.
1.  On `main`, a developer changes line 10 of `config.js` to `PORT = 8080`.
2.  On `feature-A`, a different developer (or even the same one working on a separate task) changes line 10 of `config.js` to `PORT = 3000`.

When you try to merge `feature-A` into `main` (or vice versa), Git sees two different changes to the exact same line. It doesn't know whether you want `8080` or `3000`. This ambiguity is why the automatic merge fails. Git needs you to inspect these conflicting sections and explicitly tell it which version to keep, or how to combine them.

## Common Causes

In my experience, merge conflicts often boil down to a few key scenarios:

*   **Parallel Development on the Same Files:** This is the most frequent cause. Multiple developers working independently on different features might inadvertently modify the same lines or sections of a shared file. For instance, two developers might refactor different functions in the same utility file, but their changes overlap on a common import statement or a global configuration block.
*   **Divergent Branches Over Time:** If a feature branch lives for a long time without being regularly updated from the `main` branch, the `main` branch can accumulate many changes. When the feature branch is finally merged, the accumulated differences increase the likelihood of conflicts, especially in frequently modified files like build configurations, API endpoints, or core utilities.
*   **Refactoring Overlaps:** Sometimes, one developer renames a variable or refactors a function, while another developer modifies the content of that same variable/function. Git might struggle to reconcile a content change with a rename if the rename isn't perfectly clean, leading to a content conflict.
*   **Differing Line Endings:** While Git has `core.autocrlf` and `core.safecrlf` settings to handle line ending differences between operating systems (Windows uses CR-LF, Linux/macOS uses LF), misconfigurations or legacy files can sometimes lead to entire files being marked as conflicted due to whitespace changes, even if the actual code content is the same. I've seen this in production when developers with different OSes touched the same file without proper Git configuration.
*   **Accidental Inclusion of Generated Files:** If `*.log`, `*.DS_Store`, or other generated files are committed to the repository (when they should be in `.gitignore`), and different developers generate these files with slightly different content, they will frequently cause conflicts. This is a configuration issue more than a merge issue, but it manifests as merge conflicts.

## Step-by-Step Fix

Resolving a merge conflict can seem daunting at first, but it's a systematic process.

1.  **Identify the Conflicted Files:**
    After a failed merge, `git status` is your best friend. It will clearly list all files that have "unmerged paths."

    ```bash
    git status
    ```

2.  **Open the Conflicted Files:**
    Open each file listed by `git status` in your preferred text editor or IDE. Inside these files, Git inserts special markers to delineate the conflicting sections:

    ```
    <<<<<<< HEAD
    // This is the version from your current branch (HEAD).
    console.log("Feature A is active.");
    function calculatePrice(item, quantity) {
        return item.price * quantity * 1.05; // 5% tax
    }
    =======
    // This is the version from the branch you're merging from.
    console.log("Feature B is active.");
    function calculatePrice(item, quantity) {
        return item.price * quantity * 1.08; // 8% tax
    }
    >>>>>>> feature/new-tax-rate
    ```
    *   `<<<<<<< HEAD`: Marks the beginning of the changes from your current branch (often referred to as "ours").
    *   `=======`: Separates the changes from your current branch (`HEAD`) and the incoming branch.
    *   `>>>>>>> <branch-name>`: Marks the end of the changes from the branch you're merging into your current branch (often referred to as "theirs"). The `<branch-name>` will be the name of the branch you are merging from.

3.  **Manually Resolve the Conflicts:**
    Edit the file to remove the conflict markers and keep only the code you want. You have a few options for each conflict block:
    *   **Keep "ours":** Delete the `=======` line, the `>>>>>>>` line, and all the content between them.
    *   **Keep "theirs":** Delete the `<<<<<<<` line, the `=======` line, and all the content between them.
    *   **Combine both:** Manually edit the section to integrate changes from both sides. This is often necessary when both branches added valid, but different, code that needs to coexist.
    *   **Keep neither:** If both changes are obsolete, simply delete the entire block, including the markers.

    Continuing the example above, if you decide you need the 8% tax from the `feature/new-tax-rate` branch, and the console log message from `HEAD`, you'd edit it to:

    ```javascript
    console.log("Feature A is active.");
    function calculatePrice(item, quantity) {
        return item.price * quantity * 1.08; // 8% tax
    }
    ```
    Save the file after resolution.

4.  **Add the Resolved File to the Staging Area:**
    After resolving conflicts in a file, you must tell Git that the file is ready by adding it to the staging area.

    ```bash
    git add src/feature.js
    git add docs/README.md # Repeat for all resolved files
    ```
    You can use `git add .` to stage all modified files, but be careful that you haven't introduced any unintended changes elsewhere.

5.  **Commit the Merge:**
    Once all conflicts are resolved and all conflicted files are added to the staging area, you can commit the merge. Git will pre-populate a commit message for you, usually starting with "Merge branch 'feature/new-tax-rate' into main". It's good practice to review this message and add a brief explanation of how you resolved the conflicts, especially if it was a complex resolution.

    ```bash
    git commit -m "Merge branch 'feature/new-tax-rate' into main, resolved tax rate conflict"
    ```

    Git will create a new "merge commit" that ties the histories of both branches together.

6.  **Test Your Code (Crucial!):**
    After resolving conflicts and committing the merge, it is absolutely critical to test your application thoroughly. Merging different code paths can introduce subtle bugs that aren't immediately obvious. Run your unit tests, integration tests, and perform manual smoke testing.

7.  **Aborting a Merge:**
    If you get overwhelmed or realize you've made a mess, you can always abort the merge and return to the state before you started merging.

    ```bash
    git merge --abort
    ```
    This command will stop the merge process, revert your repository to the state it was in before the merge attempt, and remove any conflict markers.

## Code Examples

Here are some concise, copy-paste ready examples for common conflict scenarios:

**1. Simple Conflict Resolution:**
Assume `foo.js` has a conflict:

```javascript
// Before resolution
<<<<<<< HEAD
const VERSION = "1.0.0";
function init() { console.log("Init v1"); }
=======
const VERSION = "1.0.1";
function init() { console.log("Init v2"); }
>>>>>>> feature/update-version
```

To keep `VERSION = "1.0.1"` and `init() { console.log("Init v2"); }`:

```javascript
// After resolution
const VERSION = "1.0.1";
function init() { console.log("Init v2"); }
```

Then:
```bash
git add foo.js
git commit -m "Resolved conflict in foo.js, updated version"
```

**2. Keeping "Our" or "Their" Version of a File:**
Sometimes, for a specific file, you simply want to discard all changes from one side and keep the entire file from the other.

To keep your current branch's version of `config.json` entirely:
```bash
git checkout --ours config.json
git add config.json
git commit -m "Resolved conflict in config.json, kept our version"
```

To keep the incoming branch's version of `config.json` entirely:
```bash
git checkout --theirs config.json
git add config.json
git commit -m "Resolved conflict in config.json, kept their version"
```
Remember `HEAD` refers to "ours" (your current branch), and the merging branch refers to "theirs".

**3. Using a Merge Tool:**
For more complex conflicts, or when dealing with many files, a visual merge tool can be invaluable. Git can be configured to use external tools like VS Code's merge editor, KDiff3, Meld, Beyond Compare, etc.

First, configure your merge tool (example for VS Code):
```bash
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait --merge $LOCAL $REMOTE $BASE $MERGED'
git config --global mergetool.vscode.trustExitCode true
```

Then, when you have conflicts:
```bash
git mergetool
```
This will launch your configured merge tool, allowing you to visually compare the three versions (base, local, remote) and select changes. After saving and closing the tool, Git will automatically stage the file.

## Environment-Specific Notes

Merge conflicts are fundamentally about file changes in your repository, so the core resolution process remains the same regardless of your environment. However, how you *interact* with those files and how conflicts impact your workflow can differ.

*   **Local Development:** This is where 99% of merge conflict resolution happens. Your IDE (like VS Code, IntelliJ IDEA, Sublime Text) usually offers excellent built-in merge conflict resolution tools, often showing the base, "ours," and "theirs" versions side-by-side with buttons to accept changes. Using these integrated tools can significantly streamline the process compared to manual editing in a plain text editor. Always resolve locally *before* pushing to a remote.

*   **CI/CD (Cloud Services like GitHub Actions, GitLab CI, Jenkins):** Merge conflicts typically *prevent* a merge from being completed in a pull request (PR) or merge request (MR) workflow. Your CI/CD pipeline will not even kick off on the combined (unresolved) code because the merge simply won't happen. The resolution *must* occur on a local machine, then the resolved merge commit (or rebased branch) is pushed. If you use "squash and merge" on platforms like GitHub, the conflict resolution still happens locally on your branch (e.g., merging `main` into your feature branch to resolve conflicts), and then the squashed commit is applied cleanly to `main`. The "squash" itself doesn't resolve conflicts, it just consolidates commits.

*   **Docker/Containerized Environments:** Docker containers run your application, but they don't directly manage your source code's Git history. Conflicts arise in your *host machine's* local Git repository, where your source code resides. Any resolution you perform is on your host machine's filesystem. Once resolved and committed, your Docker build process will simply pick up the updated, merged code. Docker itself neither causes nor helps resolve Git merge conflicts.

*   **Monorepos:** In large monorepos with many teams, the chances of conflicts increase due to the sheer volume of changes across a shared codebase. Establishing clear code ownership, using feature flags to decouple deployments from merges, and maintaining small, frequent merges (e.g., rebasing frequently from `main`) are strategies I've found helpful to mitigate conflict frequency.

## Frequently Asked Questions

**Q: What's the difference between `git merge --abort` and `git reset --hard HEAD`?**
**A:** `git merge --abort` is specifically designed to stop an in-progress merge and reset your branch to its state *before* the merge attempt. It's safe when you're in a merge conflict state. `git reset --hard HEAD`, on the other hand, discards *all* local changes (staged and unstaged) and resets your branch to the last commit, potentially losing work if you had uncommitted changes *before* the merge attempt. Use `git merge --abort` when resolving merge conflicts; use `git reset --hard HEAD` with caution.

**Q: Can I avoid merge conflicts altogether?**
**A:** Not entirely, especially in collaborative environments. However, you can significantly reduce their frequency and complexity by:
*   **Pulling `main` frequently:** Regularly update your feature branches with changes from the main development branch.
*   **Keeping feature branches small and short-lived:** Smaller changesets are easier to merge.
*   **Good communication:** Coordinate with teammates about who is working on which files.
*   **Clear code ownership:** If certain modules or files have clear owners, conflicts within those areas can be minimized.

**Q: What do "ours" and "theirs" mean in a merge conflict?**
**A:** "Ours" refers to the changes on your current branch (`HEAD`), the branch you are currently on and into which you are merging. "Theirs" refers to the changes on the branch you are attempting to merge *from*.

**Q: Should I use `git merge` or `git rebase` to avoid conflicts?**
**A:** Neither `merge` nor `rebase` truly *avoids* conflicts; they just handle them differently.
*   **`git merge`** creates a merge commit and integrates the branches. Conflicts are resolved once in this merge commit.
*   **`git rebase`** reapplies your branch's commits one-by-one onto the target branch's tip. If conflicts occur, you resolve them *per commit* as Git reapplies them. This results in a cleaner linear history but can lead to more frequent conflict resolution if your branch has many commits that conflict. The choice often depends on team preference and workflow. I generally prefer `merge` for integrating feature branches into `main` and `rebase` for keeping a feature branch up-to-date with `main` *before* merging.

**Q: My IDE is showing different merge markers, what gives?**
**A:** Many modern IDEs (like VS Code, IntelliJ) provide their own visual merge editors that interpret the raw Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) and present them in a more user-friendly way. These tools often show three panes: one for the base version (common ancestor), one for "ours," and one for "theirs," with options to accept current, incoming, or combine changes. While the visual representation differs, the underlying conflict is the same.

## Related Errors