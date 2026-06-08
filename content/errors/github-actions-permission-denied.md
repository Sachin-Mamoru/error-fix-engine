# GitHub Actions Error: Resource not accessible by integration
> Encountering "GitHub Actions Error: Resource not accessible by integration" means the GITHUB_TOKEN used by your workflow lacks the necessary permissions to perform an action; this guide explains how to fix it.

## What This Error Means

When you encounter the "Resource not accessible by integration" error in your GitHub Actions workflow, it signifies a permissions issue. Specifically, the `GITHUB_TOKEN` that GitHub Actions automatically generates for each workflow run does not have the necessary scope or permissions to perform a specific operation. "Integration" refers to the GitHub Actions runner itself, which, when executing your workflow, acts on your behalf using this temporary token. The "resource" could be anything from pushing code to the repository, creating a pull request, interacting with packages, or reading sensitive repository settings.

In my experience, this error usually pops up when an action tries to do something beyond the `GITHUB_TOKEN`'s default read-only access or when a specific interaction requires an explicit `write` permission that hasn't been granted. It's GitHub's way of enforcing the principle of least privilege, preventing unintended or malicious actions if your workflow is compromised.

## Why It Happens

The core reason this error occurs lies with the `GITHUB_TOKEN` and its carefully controlled permissions. GitHub generates a unique `GITHUB_TOKEN` for each workflow run. This token is short-lived and automatically expires when the job finishes. By default, for security, this token has limited permissions, usually read-only access to repository contents and metadata.

If any step in your workflow, whether it's a built-in action, a custom script, or a third-party action from the Marketplace, attempts an operation that requires elevated permissions (like pushing changes, creating releases, or commenting on issues), and those permissions haven't been explicitly granted to the `GITHUB_TOKEN`, the "Resource not accessible by integration" error will occur. It's a security mechanism designed to ensure that your CI/CD pipelines only perform actions you've explicitly authorized.

## Common Causes

I've seen this error manifest in a few common scenarios in production environments:

1.  **Insufficient Default `GITHUB_TOKEN` Permissions:** This is the most frequent cause. By default, the `GITHUB_TOKEN` often has `contents: read` permissions. If your workflow needs to `write` to the repository (e.g., push commits, create a branch, merge a PR), create releases, manage issues, or publish packages, these explicit `write` permissions are required.
2.  **Third-Party Actions Requiring Elevated Privileges:** Many popular community actions (e.g., for creating pull requests, deploying artifacts, or interacting with GitHub Pages) need more than just read access. For instance, an action that creates or updates a pull request will need `pull-requests: write` permissions. If you simply add such an action without adjusting permissions, it will fail.
3.  **Repository-Level Default Permissions Override:** GitHub allows repository administrators to set default permissions for the `GITHUB_TOKEN` across all workflows in that repository. If these defaults are set to be very restrictive (e.g., "Read repository contents permission"), it can override the more permissive defaults GitHub might otherwise provide and lead to this error for actions that previously worked.
4.  **Organization-Level Policies:** Similar to repository settings, organization owners can enforce default permissions for all repositories under their organization. If an organization-wide policy sets a restrictive default, it will propagate down and can cause this error.
5.  **Sensitive Resource Access:** The error can also appear if your workflow tries to access protected branches, repository secrets, or other sensitive settings that require administrative access, and the `GITHUB_TOKEN` is not configured with the appropriate `administration` scope (which is rarely granted by default).
6.  **OIDC Token Generation:** If your workflow attempts to generate an OIDC token for authentication with cloud providers, it requires `id-token: write` permission. Without this, the OIDC token generation will fail, which can manifest as a "Resource not accessible" type error downstream.

## Step-by-Step Fix

Rectifying this error primarily involves granting the `GITHUB_TOKEN` the specific permissions it needs. Here's how I typically approach it:

1.  **Identify the Failing Step:**
    *   Go to your workflow run logs in GitHub Actions.
    *   Locate the specific job and step that failed. The error message "Resource not accessible by integration" will be clearly visible, often accompanied by details about *which* resource or action was denied. This context is crucial. For example, it might say `Could not resolve to a Node with the global ID of 'MDxxxxx'` or `resource not accessible by integration for 'contents'`.

2.  **Determine the Required Permissions:**
    *   **For custom scripts/API calls:** If you're writing a script that interacts with the GitHub API, consult the GitHub REST API documentation for the specific endpoint your script is hitting. Each endpoint lists the required OAuth scopes (which map directly to `GITHUB_TOKEN` permissions).
    *   **For Marketplace Actions:** Check the documentation for the third-party action you are using. Reputable actions usually explicitly state the `permissions` they require in their README.
    *   **Common Needs:**
        *   `contents: write` (for pushing commits, creating files, merging branches)
        *   `pull-requests: write` (for creating/updating pull requests)
        *   `packages: write` (for publishing packages)
        *   `releases: write` (for creating/updating releases)
        *   `issues: write` (for creating/updating issues)
        *   `id-token: write` (for OpenID Connect (OIDC) authentication)

3.  **Adjust Workflow Permissions (Most Common Fix):**
    *   You can set permissions at the **workflow level** (applies to all jobs in the workflow) or at the **job level** (applies only to that specific job). Job-level permissions always override workflow-level permissions for that particular job.
    *   Open your workflow `.yml` file.
    *   Add a `permissions` block, specifying the required scopes:

    ```yaml
    # At the workflow level (applies to all jobs in this workflow)
    name: My CI/CD Workflow
    on: push
    
    permissions:
      contents: write # Grant write permission to repository contents
      pull-requests: write # Grant write permission for pull requests
      # You can specify 'read' for other scopes if needed, e.g.,
      # issues: read
      # packages: read
    
    jobs:
      build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Create or update PR
            uses: peter-evans/create-pull-request@v6 # This action requires pull-requests: write
    
      release:
        runs-on: ubuntu-latest
        permissions: # Job-level permissions override workflow-level for this job
          contents: write # Required for creating release assets
          releases: write # Required for creating releases
        steps:
          - uses: actions/checkout@v4
          - name: Create a GitHub Release
            run: |
              echo "Creating release..."
              # Some release logic here
    ```

    *   **Caution with `permissions: write-all`:** While `permissions: write-all` grants maximum access, it is generally discouraged due to the principle of least privilege. Always aim for the minimum necessary permissions. Use `read-all` if you want all read permissions, and then override specific scopes with `write` as needed.

4.  **Adjust Repository Default Permissions (If workflow changes aren't enough or for consistency):**
    *   Navigate to your repository on GitHub.
    *   Go to **Settings** -> **Actions** -> **General**.
    *   Scroll down to "Workflow permissions".
    *   You can select "Read and write permissions" as a default, or "Restrict default GITHUB_TOKEN permissions" and then configure specific default permissions for scopes like `contents`, `issues`, `pull-requests`, etc.
    *   **Note:** Changing repository defaults affects all workflows *that do not explicitly define a `permissions` block*. If a workflow *does* define `permissions`, its explicit definition takes precedence.

5.  **Adjust Organization Default Permissions (For organization-wide consistency):**
    *   If you're an organization owner, you can set default workflow permissions at the organization level.
    *   Go to your **Organization Settings** -> **Actions** -> **General**.
    *   Similar to repository settings, you can configure default `GITHUB_TOKEN` permissions for all repositories in the organization.

## Code Examples

Here are common ways to declare permissions in your GitHub Actions workflows:

### Workflow-level permissions

Applies to all jobs in the workflow.

```yaml
name: Workflow with Global Write Permissions
on:
  push:
    branches:
      - main

permissions:
  contents: write # Allows writing to the repo, useful for pushing changes
  pull-requests: write # Allows creating/updating pull requests
  issues: write # Allows creating/updating issues
  # id-token: write # Required for generating OIDC tokens

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Make a change and push
        run: |
          echo "Date: $(date)" > current_date.txt
          git config user.name "GitHub Actions Bot"
          git config user.email "actions@github.com"
          git add current_date.txt
          git commit -m "Update current date [skip ci]"
          git push
```

### Job-level permissions

Overrides workflow-level permissions for a specific job. Useful for granting elevated permissions only where absolutely necessary.

```yaml
name: Job-Specific Permissions Workflow
on: [push]

permissions:
  contents: read # Default to read-only for security

jobs:
  read_only_job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: List files (read-only)
        run: ls -la

  write_job:
    runs-on: ubuntu-latest
    permissions: # This job needs write access
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - name: Create a Pull Request (requires pull-requests: write)
        uses: peter-evans/create-pull-request@v6
        with:
          title: "Automated PR from CI"
          body: "This PR was created by a GitHub Actions workflow."
          commit-message: "Automated change"
          branch: "automated-branch"
          base: "main"
          delete-branch: true
```

### Granular Permissions for OIDC

When using OpenID Connect (OIDC) to authenticate with cloud providers (AWS, Azure, GCP), the `id-token: write` permission is crucial.

```yaml
name: OIDC Authentication Example
on: [push]

permissions:
  id-token: write # Required for OIDC token generation
  contents: read # Typically still need read access

jobs:
  deploy-to-aws:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
          aws-region: us-east-1
      - name: Deploy application
        run: |
          # AWS CLI commands to deploy
          aws s3 cp my-app s3://my-bucket/
```

## Environment-Specific Notes

While the core concept of `GITHUB_TOKEN` permissions remains consistent, how you manage and debug them can have slight nuances across different environments.

*   **GitHub.com (Cloud):** This is the most common environment. The default `GITHUB_TOKEN` permissions are generally `contents: read` and some `metadata: read`. All the `permissions` block configurations directly apply. Repository and organization-level settings are managed via the GitHub web UI.
*   **GitHub Enterprise Server (GHES):** If you're running GitHub Actions on a GHES instance, the enterprise administrator might have set enterprise-wide default permissions that are stricter or different from GitHub.com. Always check with your GHES admin if you're encountering persistent issues that don't seem to be resolved by workflow or repository settings. The `GITHUB_TOKEN` behavior itself is the same, but the default baseline might vary. Upgrades to GHES instances can sometimes reset or change default permissions, which I've seen cause unexpected failures post-upgrade.
*   **Local Development / Docker:** The "Resource not accessible by integration" error is specific to the GitHub Actions runtime environment and the `GITHUB_TOKEN`. When you're developing locally or running parts of your CI/CD pipeline in Docker containers *outside* of GitHub Actions (e.g., using `act` to simulate runners), the `GITHUB_TOKEN` isn't present in the same way. You'd typically use a Personal Access Token (PAT) for local GitHub API interactions. This means the error won't appear during local testing, reinforcing the need to rigorously test your `permissions` configuration in your actual GitHub Actions workflows. The problem surfaces only when the workflow runs on GitHub's infrastructure, using the auto-generated, permission-constrained token.

## Frequently Asked Questions

**Q: Can I just use `permissions: write-all` to avoid this error?**
**A:** While `permissions: write-all` would likely solve the error by granting maximum permissions, it is generally **not recommended** for security reasons. It violates the principle of least privilege, making your workflow potentially vulnerable if a third-party action or a script within it is compromised. Always strive to grant only the specific permissions (`contents: write`, `pull-requests: write`, etc.) that your workflow absolutely needs.

**Q: My workflow used to work, but now it's failing with this error. What changed?**
**A:** This often indicates a change in the default permissions. Possible culprits include:
    *   A repository administrator changed the default workflow permissions in **Repository Settings > Actions > General**.
    *   An organization owner changed the default workflow permissions at the organization level.
    *   A new step or action was added to your workflow that requires permissions not previously needed.
    *   A third-party action you're using was updated and now requires additional permissions or has changed its internal GitHub API calls.

**Q: What's the difference between setting `permissions` at the workflow level versus the job level?**
**A:** Workflow-level `permissions` apply to all jobs within that workflow by default. Job-level `permissions` override any workflow-level settings specifically for that particular job. Use workflow-level for permissions common to most jobs, and job-level for jobs that need specific, potentially elevated, or more restricted permissions. This allows for fine-grained control and helps adhere to the principle of least privilege.

**Q: Do I need to create a Personal Access Token (PAT) for every action that needs write access?**
**A:** No, in almost all cases, you should use the built-in `GITHUB_TOKEN` and explicitly grant it the necessary `permissions` in your workflow file. Creating and managing PATs is more complex and poses a higher security risk (PATs have long lifetimes and broad scopes if not managed carefully). A PAT is typically only considered as a last resort for scenarios where `GITHUB_TOKEN` cannot fulfill the requirement, such as interacting with resources in *another* repository.

**Q: Why do I sometimes see "Bad credentials" instead of "Resource not accessible"?**
**A:** "Bad credentials" usually means the token itself is invalid, expired, or malformed. "Resource not accessible" means the token *is* valid, but it simply lacks the authorization (permissions) to perform a specific action on a specific resource. This distinction is helpful for debugging.

## Related Errors
*(none)*