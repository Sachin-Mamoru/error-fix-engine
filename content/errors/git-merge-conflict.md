# Git merge conflict – Automatic merge failed; fix conflicts
> Encountering "Automatic merge failed" means Git cannot reconcile divergent changes; this guide explains how to fix it manually.

## What This Error Means

When you attempt to merge one Git branch into another, you might encounter the message "Automatic merge failed; fix conflicts and then commit the result." This error isn't a showstopper; it's Git's way of telling you it needs human intervention. Specifically, it means that changes in the branch you're trying to merge (the "source" branch) and the branch you're merging into (the "target" branch, often `main` or `develop`) overlap in the same file and lines. Git, being a deterministic tool, cannot automatically decide which change should prevail. It halts the merge process, marks the conflicting areas in the affected files, and waits for you to resolve the ambiguity manually.

In my experience, this message is a common sight when working in teams, especially on actively developed features. It means your repository is now in a "merging" state, awaiting your input. Until you resolve these conflicts and commit the merge, your branch remains in this intermediate state.

## Why It Happens

Git's merge algorithm is robust, capable of automatically merging changes that occur in different parts of a file or even in the same parts of different files. It uses a three-way merge strategy, comparing the common ancestor of the two branches with the latest state of each branch. It identifies what changes were made on each side.

The conflict arises when Git detects that both branches have modified the *same specific lines* of code, or when one branch modifies a section of code that another branch has deleted, or vice-versa. In these scenarios, Git cannot determine the "correct" version without your guidance. It doesn't know whether to keep your changes, the other branch's changes, or a combination of both.

For example, if you modify lines 5-10 of `index.js` on your feature branch, and a colleague modifies lines 7-12 of the *same* `index.js` on their branch, merging these two branches will likely result in a conflict because of the overlapping lines 7-10. Git cannot intelligently decide which specific version of those lines to retain.

## Common Causes

Merge conflicts are a natural part of collaborative software development. Here are some of the most common scenarios I've encountered:

*   **Simultaneous Modification of the Same Lines:** This is the most straightforward cause. Two developers make changes to the exact same lines of code within the same file. For example, both modify a function signature or a variable initialization.
*   **Different Approaches to the Same Feature:** Sometimes, two developers might independently implement parts of the same feature or fix, leading to divergent changes in related code blocks.
*   **Refactoring Conflicts:** One developer might refactor a section of code (renaming variables, extracting methods) while another simultaneously modifies that same original code. When merged, Git sees the refactored code and the original code as different, leading to conflicts.
*   **Changes to Shared Configuration or Dependency Files:** Files like `package.json`, `requirements.txt`, `pom.xml`, `.env`, or Dockerfiles are frequently modified by multiple team members. If two developers add different dependencies or configuration values, conflicts are almost guaranteed. I've seen this in production environments when multiple microservices teams update common library versions.
*   **Line Ending Differences:** Less common with modern Git configurations, but different operating systems (Windows vs. Unix/Linux/macOS) handle line endings differently (`CRLF` vs. `LF`). If not properly configured (e.g., `core.autocrlf`), this can sometimes lead to conflicts, especially in `.gitattributes` or scripts.
*   **Long-Lived Branches:** Branches that exist for a long time without being regularly merged with their target branch (`main` or `develop`) accumulate a significant number of divergent changes. When an eventual merge attempt is made, the sheer volume of differences increases the probability and complexity of conflicts.
*   **File Renames/Deletions While Content is Modified:** If one branch renames or deletes a file, while another branch modifies its content, Git might get confused. It needs your input to understand if the changes should be applied to the renamed file or if the deletion should take precedence.

## Step-by-Step Fix

Resolving a merge conflict can seem daunting at first, but it follows a clear, repeatable process.

1.  **Identify the Conflict:**
    The first step is always to run `git status`. This command will tell you that you are in the middle of a merge and list the files that have conflicts.

    ```bash
    git status
    ```

    You'll see output similar to this:

    ```
    On branch feature/my-new-feature
    You have unmerged paths.
      (fix conflicts and run "git commit")
      (use "git merge --abort" to abandon merge)

    Unmerged paths:
      (use "git add <file>..." to mark resolution)
            both modified:   src/components/MyComponent.js
            both modified:   README.md

    no changes added to commit (use "git add" and/or "git commit -a")
    ```

2.  **Open Conflicting Files:**
    Open each file listed under "Unmerged paths" in your favorite text editor or IDE. Inside these files, Git inserts special markers to highlight the conflicting areas.

    ```
    <<<<<<< HEAD
    console.log("Feature A implementation.");
    function calculateArea(length, width) {
        return length * width;
    }
    =======
    console.log("Bug fix for existing feature.");
    function calculateArea(l, w) {
        // Updated logic for edge cases
        if (l < 0 || w < 0) return 0;
        return l * w;
    }
    >>>>>>> feature/another-feature
    ```

    *   `<<<<<<< HEAD`: Marks the beginning of the changes from the current branch you're merging *into*. (`HEAD` refers to your current branch).
    *   `=======`: Separates the changes from the two branches.
    *   `>>>>>>> <branch-name>`: Marks the end of the changes from the branch you're merging *from*. (`feature/another-feature` in this example).

3.  **Manually Resolve the Conflict:**
    Carefully examine the code between the markers. You need to decide which changes to keep. You have several options:
    *   **Keep "your" changes (from `HEAD`):** Delete the `<<<<<<<`, `=======`, `>>>>>>>` markers and the code from the other branch.
    *   **Keep "their" changes (from the merged branch):** Delete the `<<<<<<<`, `=======`, `>>>>>>>` markers and the code from `HEAD`.
    *   **Combine both:** Integrate parts of both changes, modifying the code to correctly reflect the desired outcome. This is often the most common scenario.
    *   **Write entirely new code:** If neither version is correct, you might need to rewrite the conflicting section.

    After resolution, the file should contain only the final, correct code, with no Git markers. For the example above, a resolution might look like:

    ```javascript
    console.log("Bug fix for existing feature, with new feature logging.");
    function calculateArea(length, width) { // Using descriptive variable names
        // Updated logic for edge cases
        if (length < 0 || width < 0) return 0;
        return length * width;
    }
    ```

4.  **Mark the File as Resolved:**
    Once you've edited a file and removed all conflict markers, you need to tell Git that you've resolved it.

    ```bash
    git add src/components/MyComponent.js
    git add README.md
    ```

    Repeat this for all conflicting files. You can verify your progress with `git status`; resolved files will move from "Unmerged paths" to "Changes to be committed."

5.  **Commit the Merge:**
    After all conflicts are resolved and added, you can complete the merge by committing. Git will pre-populate a commit message for you, usually indicating it's a "Merge branch 'feature/another-feature'". It's good practice to keep this message, possibly adding details about the conflict resolution if it was particularly complex.

    ```bash
    git commit
    ```

    This will open your configured text editor with the merge commit message. Save and close it to complete the commit.

6.  **Optional: Use a Merge Tool:**
    For complex conflicts, especially with many files, a visual merge tool can be invaluable. Git can integrate with tools like KDiff3, Beyond Compare, VS Code's built-in merge editor, or IntelliJ's merge tool. You can initiate these with:

    ```bash
    git mergetool
    ```

    This will open the tool for each conflicting file, allowing you to visually compare and pick changes. After saving and closing the merge tool for a file, Git will automatically `add` that file for you.

7.  **Optional: Abort the Merge:**
    If you get stuck or decide you want to restart the merge process, you can abort it at any time before committing.

    ```bash
    git merge --abort
    ```

    This command will reset your branch to the state it was in *before* you started the merge, discarding any conflict resolution you might have done. I've often used this when I realize the conflict is more complex than anticipated and I need to pull in upstream changes first.

## Code Examples

Here are some concise, copy-paste ready code examples for typical merge conflict scenarios.

**Initial `git status` when a conflict occurs:**

```bash
git status
```

Output:
```
On branch my-feature
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abandon merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   src/data.js
	both modified:   styles/main.css

no changes added to commit (use "git add" and/or "git commit -a")
```

**Content of a conflicting file (`src/data.js`):**

```javascript
const API_URL = "https://api.example.com/v1";

<<<<<<< HEAD
const ITEMS_PER_PAGE = 10; // New pagination setting
function fetchData() {
    // Logic for fetching items with pagination
    console.log("Fetching data with pagination.");
}
=======
const CACHE_DURATION = 3600; // Cache duration in seconds
function fetchData() {
    // Optimized data fetching logic
    console.log("Optimized data fetch initiated.");
}
>>>>>>> develop
```

**Resolving the conflict (manual edit of `src/data.js`):**

```javascript
const API_URL = "https://api.example.com/v1";

const ITEMS_PER_PAGE = 10; // New pagination setting
const CACHE_DURATION = 3600; // Cache duration in seconds

function fetchData() {
    // Combined logic: Fetching data with pagination and optimized caching
    console.log("Fetching data with pagination and caching strategy.");
    // ... further combined logic ...
}
```

**Adding the resolved file:**

```bash
git add src/data.js
git add styles/main.css # If styles/main.css was also conflicted and resolved
```

**Committing the merge:**

```bash
git commit -m "Merge branch 'develop' into my-feature, resolving conflicts"
```

**Using `git mergetool`:**

```bash
git mergetool
```
(This will launch your configured merge tool for each conflicting file.)

**Aborting a merge:**

```bash
git merge --abort
```

## Environment-Specific Notes

While the core Git merge conflict resolution process remains consistent, its implications and typical workflows can vary across different development environments.

*   **Local Development:** This is where merge conflicts are almost exclusively resolved. Modern IDEs like VS Code, IntelliJ IDEA, and others have excellent built-in merge editors that simplify the process. They often highlight changes side-by-side or provide a three-way view (local, remote, merged output) with buttons to accept "Current Change," "Incoming Change," or "Both." This significantly streamlines manual resolution, making `git mergetool` less critical for many developers. For example, VS Code's merge editor is now my go-to for most text-based conflicts.
*   **Cloud CI/CD Pipelines (e.g., GitHub Actions, GitLab CI, Jenkins):** Merge conflicts typically prevent a pull request (or merge request) from being merged into the target branch. The CI/CD pipeline often won't even start a build if the merge fails locally (e.g., when GitHub checks for mergeability). If the conflict is only discovered deeper in the build process (rare for simple merge conflicts, more common for semantic issues), the build will simply fail. The resolution, however, *always* happens on a local developer machine. Once resolved and pushed, the CI/CD pipeline can proceed. It's a key reason why keeping branches up-to-date with `main` is important for fast feedback cycles.
*   **Docker Environments:** If your merge conflict lies within a `Dockerfile`, `docker-compose.yml`, or any files crucial for building or running your Docker containers, resolving it locally is critical before rebuilding your images. A conflicted `Dockerfile` will simply fail the `docker build` command. The same applies to application code; if the merged code introduces syntax errors due to an unresolved conflict, the application inside the container will fail to start or operate correctly. Always resolve, then rebuild (`docker-compose build` or `docker build .`) and retest.
*   **Monorepos:** Monorepos, where multiple projects or services reside in a single repository, can sometimes increase the *frequency* of merge conflicts. This is because changes to shared tooling, foundational libraries, or common configuration files (`.prettierrc`, `tsconfig.json`, build scripts) can impact a wider surface area. While the resolution process itself is the same, developers need to be acutely aware of the broader impact of their changes across services when resolving these conflicts. I've often seen conflicts in a root `package.json` where different teams add new scripts or dependencies.

## Frequently Asked Questions

**Q: Can I prevent merge conflicts entirely?**
**A:** Not entirely, as they are inherent to collaborative development. However, you can significantly reduce their occurrence and complexity. Strategies include:
*   **Feature branches:** Keep feature branches small and short-lived.
*   **Frequent merging/rebasing:** Regularly pull changes from your target branch (e.g., `main`) into your feature branch to stay up-to-date.
*   **Good communication:** Coordinate with teammates about who is working on what files.
*   **Atomic commits:** Make small, focused commits that are easier to merge.

**Q: What happens if I accidentally commit the merge markers (`<<<<<<<`, `=======`, `>>>>>>>`)?**
**A:** If you realize you've committed the markers, your code will likely break, and Git will see those markers as part of your content. You need to undo that commit. The simplest way is to use `git reset --soft HEAD~1` (which will uncommit but keep your changes staged), then fix the files, `git add` them again, and `git commit` properly. If the commit has already been pushed and others have pulled it, you might need `git revert` to create a new commit that undoes the problematic one.

**Q: How do I handle conflicts in binary files (e.g., images, `.docx` files)?**
**A:** Git cannot perform a three-way merge on binary files. When a binary file conflicts, Git will typically list it as "both modified" but won't show markers in the file. You must manually decide which version to keep. You can do this by using `git checkout --ours <filename>` to keep your version, or `git checkout --theirs <filename>` to keep the version from the branch you're merging from. After choosing, `git add <filename>` and then `git commit`.

**Q: Should I always use `git mergetool`?**
**A:** It depends on your preference and the complexity of the conflict. For simple text conflicts in one or two files, manually editing directly in your IDE might be faster. For complex conflicts involving many files or intricate code changes, a visual merge tool often provides a clearer overview and simplifies the decision-making process. Modern IDEs often offer excellent built-in merge editors that serve this purpose well.

**Q: What's the difference between a merge conflict and a rebase conflict?**
**A:** The mechanism for resolving the conflict markers is essentially the same. The main difference lies in *when* and *how many times* conflicts can occur. During a `git merge`, conflicts are presented once for the entire set of changes. During a `git rebase`, Git applies your branch's commits one by one onto the target branch. If a conflict occurs, you resolve it, `git add` the file(s), and then `git rebase --continue`. This process can repeat for *each* of your commits if they conflict with the rebased changes. This makes rebase conflicts potentially more tedious but results in a cleaner, linear history.

## Related Errors

*   [git-detached-head](/errors/git-detached-head.html)
*   [git-push-rejected](/errors/git-push-rejected.html)