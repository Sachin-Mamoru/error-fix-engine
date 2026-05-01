# GitHub Actions Error: Resource not accessible by integration
> Encountering 'Resource not accessible by integration' means your workflow's `GITHUB_TOKEN` lacks permissions; this guide explains how to fix it.

## What This Error Means

When your GitHub Actions workflow encounters the "Resource not accessible by integration" error, it signifies a fundamental permissions issue. Specifically, the `GITHUB_TOKEN`, the special token GitHub automatically provides to your workflows, does not have the necessary scope or privileges to perform a requested action.

Think of it this way: your workflow job is an "integration" trying to interact with GitHub's API (e.g., pushing code, creating a release, adding a label to an issue). The `GITHUB_TOKEN` is its credential. If that credential doesn't have the right "keys" for the "door" it's trying to open, you get this error. It's GitHub's security mechanism preventing workflows from accidentally or maliciously performing actions they shouldn't.

## Why It Happens

The `GITHUB_TOKEN` is designed with security in mind, operating on the principle of least privilege. By default, it often comes with a limited set of permissions – typically `read` access for most scopes (like `contents`, `issues`, `pull-requests`). This default prevents workflows from making unwanted changes without explicit permission.

The error arises when a workflow step attempts an operation that requires `write` access (or other specific elevated permissions) for a particular scope, but the `GITHUB_TOKEN` available to that step only has `read` access, or no access at all, for that scope. For example, if your workflow tries to push commits to the repository, it needs `contents: write`. If it tries to create a release, it needs `contents: write` and `releases: write`. Without these explicit grants, the token is denied access to the resource.

## Common Causes

In my experience, this error almost always boils down to one of these scenarios:

1.  **Missing `permissions` block in the workflow file:** The most frequent cause. If your workflow YAML doesn't include a `permissions` block at all, or if it's missing for a specific job, the `GITHUB_TOKEN` will revert to its default, often restrictive, `read`-only access. Many actions, especially those that modify the repository, need more than this.
2.  **Insufficient `permissions` scope:** You might have a `permissions` block, but it's not specific enough. For instance, you declare `permissions: contents: read` when the action actually needs `contents: write` to perform its task, like updating a file or creating a git tag. I've seen this in production when teams try to automate version bumping.
3.  **Repository-level default permissions are too restrictive:** GitHub allows repository administrators to set a default permission level for the `GITHUB_TOKEN` for all workflows within that repository. If this default is set to `read` or even `no permissions` for a critical scope, it can override or interact unexpectedly with job-level permissions if not carefully managed.
4.  **Third-party actions requiring specific permissions:** You're using a community-contributed GitHub Action (e.g., an action to publish to a package registry, or interact with a third-party service via GitHub's API) that implicitly or explicitly requires certain `write` scopes for the `GITHUB_TOKEN` to function correctly. Its documentation should specify these requirements.
5.  **Misunderstanding the scope:** Sometimes, what appears to be a `pull-requests` permission issue is actually a `contents` issue, or vice versa, depending on the exact operation being performed by the action. It pays to consult the action's documentation carefully.

## Step-by-Step Fix

Rectifying "Resource not accessible by integration" is typically a matter of explicitly granting the required permissions to your workflow's `GITHUB_TOKEN`.

1.  **Identify the failing step:**
    *   Go to your GitHub Actions run.
    *   Look for the specific job and step that failed. The error message "Resource not accessible by integration" will usually appear in the logs for that step.
    *   Note down what that step was trying to do (e.g., `actions/checkout` when trying to push, `softprops/action-gh-release` when trying to create a release, etc.). This tells you which scope is likely missing permissions.

2.  **Determine the required permissions:**
    *   Based on the failing step, consider what it's attempting.
        *   **Pushing code, creating tags, committing files:** Requires `contents: write`.
        *   **Creating/updating releases:** Requires `contents: write` (for assets) and `releases: write`.
        *   **Opening/closing/labeling issues:** Requires `issues: write`.
        *   **Creating/updating pull requests:** Requires `pull-requests: write`.
        *   **Managing GitHub Packages:** Requires `packages: write`.
        *   **Setting commit statuses:** Requires `statuses: write`.
    *   **Crucially, consult the documentation for the specific action you are using.** Many actions clearly state the minimum `permissions` required.

3.  **Add or update the `permissions` block in your workflow YAML:**
    *   The `permissions` block can be defined at two levels:
        *   **Workflow level:** Applies to all jobs in the workflow. Less granular, potentially over-privileged.
        *   **Job level:** Applies only to a specific job. **This is generally the recommended and more secure approach.** I always advise defining permissions at the job level.

    *   Open your workflow `.yml` file (e.g., `.github/workflows/your-workflow.yml`).
    *   Locate the `job` that is failing.
    *   Add a `permissions` block under the job definition, specifying only the necessary `write` scopes.

    ```yaml
    jobs:
      my_failing_job:
        runs-on: ubuntu-latest
        permissions: # <--- Add this block
          contents: write # <--- Grant write permission for contents
          pull-requests: write # <--- Add other required permissions here
          issues: write
          # ... and so on for other scopes
        steps:
          - name: Checkout repository
            uses: actions/checkout@v4
            with:
              fetch-depth: 0 # Needed if you're pushing subsequent commits/tags
          - name: My action that needs write access
            run: |
              echo "Performing write operation..."
              # ... (e.g., git commit, git push, gh release create)
    ```

    *   Alternatively, you can specify `read-all` or `write-all`, but these are less secure and should be used with caution:

    ```yaml
    jobs:
      my_job_with_all_permissions:
        runs-on: ubuntu-latest
        permissions: write-all # <--- Grants all available write permissions. Use sparingly!
        steps:
          # ...
    ```

4.  **Review Repository Default Permissions (if necessary):**
    *   If adding job-level permissions doesn't resolve the issue, or if you suspect a broader configuration problem, check your repository's default settings.
    *   Navigate to your repository on GitHub.com.
    *   Go to `Settings` -> `Actions` -> `General`.
    *   Scroll down to "Workflow permissions".
    *   Ensure "Read and write permissions" is selected, or at least that "Read repository contents and packages permissions" is selected if you only need `read`. More importantly, if you have `write` permissions defined at the job level, the repository default should not explicitly deny them. Generally, job-level overrides repository-level, but misconfigurations can happen.

5.  **Commit and Re-run:**
    *   Commit your changes to the workflow file.
    *   Push the changes, which will trigger a new workflow run (or manually re-run the failed workflow).
    *   Observe the logs for the previously failing step. It should now pass.

## Code Examples

Here are some concise, copy-paste ready examples for common scenarios:

### Example 1: Pushing a version tag or updated `CHANGELOG.md`

If your workflow updates a file, commits it, and pushes it back to the repository, or creates a git tag, it needs `contents: write`.

```yaml
# .github/workflows/bump-version.yml
name: Bump Version

on:
  push:
    branches:
      - main

jobs:
  update_and_push:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Essential for pushing commits or tags
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Needed to fetch full history for subsequent pushes

      - name: Configure Git
        run: |
          git config user.name "GitHub Actions Bot"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Make changes and commit
        run: |
          echo "Updated content $(date)" >> README.md
          git add README.md
          git commit -m "Docs: Update README with build date"

      - name: Push changes
        run: git push origin main
```

### Example 2: Creating a GitHub Release

For workflows that create releases, you'll need `contents: write` (to upload release assets) and `releases: write`.

```yaml
# .github/workflows/create-release.yml
name: Create Release

on:
  push:
    tags:
      - 'v*' # Trigger on new tags like v1.0.0

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write # For uploading release assets
      releases: write # For creating the release itself
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build artifact (example)
        run: |
          echo "My super artifact!" > my_artifact.txt

      - name: Create Release
        uses: softprops/action-gh-release@v1
        if: startsWith(github.ref, 'refs/tags/')
        with:
          files: my_artifact.txt
          body: |
            This is a new release from GitHub Actions.
            See changes in the `my_artifact.txt` file.
```

### Example 3: Commenting on an Issue or Pull Request

If your workflow needs to add comments to issues or PRs, it requires `issues: write` or `pull-requests: write` respectively.

```yaml
# .github/workflows/pr-commenter.yml
name: PR Commenter

on:
  pull_request_target:
    types: [opened]

jobs:
  greet_new_pr:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write # Required to comment on a pull request
    steps:
      - name: Post welcome comment
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '👋 Thanks for opening this pull request!'
            })
```

## Environment-Specific Notes

The "Resource not accessible by integration" error is highly specific to the GitHub Actions execution environment and the `GITHUB_TOKEN` mechanism.

*   **GitHub.com (Cloud):** This is where you'll most frequently encounter and fix this error. The default permissions for `GITHUB_TOKEN` on GitHub.com are deliberately conservative, requiring explicit grants for `write` operations. The fix described above applies directly here.
*   **GitHub Enterprise Server (GHES):** GHES environments behave very similarly to GitHub.com in this regard. The `GITHUB_TOKEN` still operates under the principle of least privilege. While your GHES administrators might have configured different default permissions at the enterprise or organization level, the mechanism for overriding or specifying permissions in your workflow YAML remains the same. The `permissions` block is your primary tool.
*   **Self-hosted Runners:** Even if you're using a self-hosted runner with extensive access to its underlying host system, the `GITHUB_TOKEN`'s permissions still apply to any interactions with the GitHub API. This error isn't about the runner's local filesystem access; it's about the token's authority to make API calls to GitHub itself. So, the solution is identical for self-hosted runners.
*   **Local Development/Testing:** This error is specific to GitHub Actions workflows running within GitHub's infrastructure. You won't encounter "Resource not accessible by integration" when developing or testing locally. When interacting with the GitHub API locally, you'd typically use a Personal Access Token (PAT), which has its own granular permission scopes (configured during PAT creation). If you're seeing a similar "permission denied" error locally, it's likely a PAT scope issue, not a `GITHUB_TOKEN` issue.

## Frequently Asked Questions

**Q: I used `permissions: write-all`, but my workflow still failed. Why?**
**A:** While `write-all` grants the maximum possible permissions to the `GITHUB_TOKEN`, it might still not be enough if the underlying issue isn't strictly about the `GITHUB_TOKEN`'s scope. Common reasons for `write-all` not fixing it include:
1.  **Branch Protection Rules:** Even with `write-all`, if a branch is protected against direct pushes (requiring pull requests or specific status checks), the `GITHUB_TOKEN` might not be able to bypass these.
2.  **Separate Authentication:** The action might be trying to use a different authentication method (e.g., a custom Personal Access Token stored in `secrets.MY_CUSTOM_TOKEN`) which has *its own* insufficient permissions, not the `GITHUB_TOKEN`.
3.  **Organization/Enterprise Policies:** Overriding policies at higher organizational levels could be in play, though this is less common for `GITHUB_TOKEN` specifically.

**Q: Should I use `secrets.GITHUB_TOKEN` in my workflow scripts?**
**A:** No, the `GITHUB_TOKEN` is automatically available to your workflow context. You should not refer to it as `secrets.GITHUB_TOKEN`. If you need to use it in a script (e.g., with `gh` CLI or `github` context in `github-script` action), you'd typically use `github.token` or simply let the `gh` CLI pick it up by default. The `permissions` block in your YAML directly configures the implicit `GITHUB_TOKEN`.

**Q: My workflow still fails after adding permissions. What should I check next?**
**A:**
1.  **Review the action's documentation carefully:** Are you sure you've included *all* the permissions it needs? Some complex actions might require several.
2.  **Double-check the YAML indentation:** YAML is sensitive to whitespace. A misaligned `permissions` block won't be parsed correctly.
3.  **Look for other error messages:** Is there a *different* error message now? Sometimes, fixing one permission issue reveals another, or an entirely separate problem.
4.  **Is it truly `GITHUB_TOKEN`?** If you're manually providing a `token:` input to an action using a secret (e.g., `token: ${{ secrets.MY_PAT }}`), then the `permissions` block for `GITHUB_TOKEN` is irrelevant. You need to check the scopes of `MY_PAT`.

**Q: Is `permissions: write-all` a good practice?**
**A:** Generally, no. While convenient, `permissions: write-all` grants your workflow comprehensive `write` access across almost all scopes. This significantly increases the blast radius if your workflow or a third-party action within it is compromised. Best practice dictates granting only the minimum necessary permissions for each specific job (e.g., `contents: write`, `issues: write`). I rarely use `write-all` in production, preferring explicit grants for security.

## Related Errors
*   [linux-permission-denied](/errors/linux-permission-denied.html)