# GitHub Actions Error: secret not found or empty
> Encountering "secret not found or empty" in GitHub Actions means your workflow is trying to use a secret that isn't defined or is inaccessible; this guide explains how to fix it.

As a Full-Stack & DevOps Engineer, I've seen the "secret not found or empty" error in GitHub Actions countless times. It's a common roadblock, especially when setting up new CI/CD pipelines or integrating third-party services. While frustrating, the error message is usually quite direct: your workflow cannot locate a specific secret it needs to operate. This guide will walk you through understanding why this happens and, more importantly, how to systematically resolve it.

## What This Error Means

When your GitHub Actions workflow runs, it often needs access to sensitive information like API keys, database credentials, or access tokens. Instead of hardcoding these values directly into your `.yml` files (which is a massive security risk), GitHub Actions provides a secure way to store and retrieve them using "secrets."

The "secret not found or empty" error means that when a specific step in your workflow attempts to access a secret—referenced via an expression like `${{ secrets.MY_API_KEY }}` or `${{ env.MY_SECRET }}`—the GitHub Actions runner cannot find a corresponding secret named `MY_API_KEY` (or whatever your secret is called) within the scope of that workflow run, or it finds one that has been stored without any value.

Essentially, your workflow is asking for something that isn't there, or is there but is blank, and it's stopping because it can't proceed without it.

## Why It Happens

At its core, this error is almost always a configuration mismatch. The workflow's YAML file specifies a secret name, but GitHub's repository (or organization, or environment) settings do not have a secret configured with that exact name and an associated value that is accessible to the workflow.

I've seen this in production when:
*   A new API key was generated but not added to GitHub Secrets.
*   A team member refactored a workflow, renamed a secret in the YAML, but forgot to update the secret name in GitHub's settings.
*   A workflow was copied from one repository to another, but the target repository didn't have all the necessary secrets configured.
*   Someone explicitly set a secret to an empty string, or accidentally cleared its value while editing.
*   A pull request from a forked repository tried to access secrets it wasn't permitted to use.

Understanding these common scenarios helps pinpoint the actual cause quickly.

## Common Causes

Let's break down the typical reasons you'll encounter this error:

1.  **Typo in Secret Name:** This is arguably the most frequent cause. A simple misspelling in either the workflow YAML file (e.g., `MY_SECRETS` instead of `MY_SECRET`) or in the secret name configured in GitHub's settings will lead to this error. Secret names are case-sensitive.
2.  **Secret Not Created:** The secret simply hasn't been added to your GitHub repository's, organization's, or environment's settings at all. It's a fundamental oversight that's easy to make in a rush.
3.  **Incorrect Secret Scope:** GitHub Actions secrets can be defined at different levels:
    *   **Repository Secrets:** Available to all workflows within a specific repository.
    *   **Organization Secrets:** Available to workflows across multiple repositories within an organization.
    *   **Environment Secrets:** Tied to specific deployment environments (e.g., `staging`, `production`) and only accessible by jobs configured to run in that environment.
    If your workflow is trying to access an environment secret but the job isn't explicitly configured with `environment: YourEnvironmentName`, or an organization secret isn't enabled for your repository, the secret won't be found. Similarly, a workflow running on a `pull_request` event from a *forked* repository cannot access repository secrets for security reasons.
4.  **Secret Value is Empty:** The secret exists, but its value was either left blank during creation or was accidentally cleared during an edit. An empty string is still technically "not found" in the context of being a useful secret.
5.  **Using `secrets` Context Incorrectly:** While less common for "not found," sometimes developers try to access `secrets.MY_SECRET` directly in a generic shell script block (`run: |`) without explicitly passing it as an environment variable or an input to an action. GitHub recommends using the `env:` context for `run` steps or `with:` for actions.
6.  **Branch Protection Rules or Environment Protections:** If you have environment protection rules that require specific branches, manual reviewers, or even specific apps to approve deployments, a secret might not be available until these conditions are met, leading to a "not found" error in intermediate stages.

## Step-by-Step Fix

Here's a systematic approach to debugging and resolving the "secret not found or empty" error:

1.  **Identify the Failing Workflow Run and Secret:**
    *   Navigate to the "Actions" tab in your GitHub repository.
    *   Click on the failed workflow run.
    *   Expand the failing job and step. The error message will usually explicitly state which secret is missing, for example: `The 'MY_API_KEY' secret was not found.` or `secret 'MY_API_KEY' not found`. Note down the exact name of the secret.

2.  **Check for Typos (Workflow YAML vs. GitHub Settings):**
    *   Open your workflow `.yml` file (e.g., `.github/workflows/main.yml`) and locate where the secret is referenced (e.g., `MY_API_KEY: ${{ secrets.MY_API_KEY }}`).
    *   Carefully compare the secret name in your YAML file with the secret name you expect in GitHub's settings. Pay close attention to capitalization and underscores. They must match exactly.
    *   Example: If your YAML has `secrets.API_KEY`, but your GitHub secret is `APIKEY`, you'll get this error.

3.  **Verify Secret Existence and Value in GitHub Settings:**
    *   Go to your repository on GitHub.
    *   Click on **Settings** (usually in the top navigation bar).
    *   In the left sidebar, click on **Secrets and variables > Actions**.
    *   Under the "Secrets" tab, look for the secret name you identified in Step 1.
    *   **Is it there?** If not, you need to add it. Click "New repository secret."
    *   **Does it have a value?** If it's present, click the "Update" button next to it. Even if you don't change the name, re-entering or confirming the value (even a single character change and then back) can sometimes fix weird state issues, or ensure it's not empty.

4.  **Check Secret Scope and Permissions:**
    *   **Repository Secret:** If you intend for it to be a repository secret, ensure it's listed under `Repository secrets` and not `Organization secrets` or an `Environment secret` by mistake.
    *   **Organization Secret:** If it's an organization secret, go to `Organization Settings > Secrets and variables > Actions`. Verify that the secret exists there and that its "Visibility" settings include your specific repository.
    *   **Environment Secret:** If the secret is meant for a specific environment (e.g., `Staging`, `Production`):
        *   In your workflow YAML, ensure the job accessing the secret has `environment: YourEnvironmentName` defined.
            ```yaml
            jobs:
              deploy_staging:
                runs-on: ubuntu-latest
                environment: Staging # This job uses secrets defined for the 'Staging' environment
                steps:
                - name: Deploy app
                  env:
                    STAGING_TOKEN: ${{ secrets.DEPLOY_TOKEN }} # This 'DEPLOY_TOKEN' must be in 'Staging' environment settings
                  run: |
                    echo "Deploying to staging with token..."
            ```
        *   Then, navigate to `Repository Settings > Environments > YourEnvironmentName`. Check if the secret is listed under "Environment secrets." If not, add it there.
    *   **Forked Repository PRs:** Remember, `pull_request` events from forked repositories cannot access repository secrets. If this is your scenario, consider using `pull_request_target` (with extreme caution and review) or exploring alternative secure credential handling for untrusted code.

5.  **Re-run the Workflow:**
    *   After verifying and correcting the secret configuration, go back to your workflow run and click "Re-run all jobs" or "Re-run failed jobs." This will trigger the workflow with the updated secret settings.

## Code Examples

Here are some common ways secrets are used in GitHub Actions and how they should be structured:

**1. Passing a Secret as an Environment Variable to a Script:**
This is the most common pattern. The `env:` block makes the secret available within the `run:` script block as a standard environment variable.

```yaml
jobs:
  build_and_deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Authenticate with external service
        env:
          MY_API_KEY: ${{ secrets.MY_API_KEY }} # This line makes MY_API_KEY available
          SERVICE_URL: 'https://api.example.com' # Other environment variables can be defined here too
        run: |
          echo "Connecting to ${SERVICE_URL}..."
          curl -H "Authorization: Bearer ${MY_API_KEY}" "${SERVICE_URL}/data"
          # The MY_API_KEY variable is accessible within this 'run' block.
```

**2. Passing a Secret as an Input to a Reusable Action:**
Many GitHub Actions expect secrets as inputs using the `with:` keyword.

```yaml
jobs:
  publish_package:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to private registry
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }} # Passed as 'password' input to the action
          registry: my.private.registry.com

      - name: Publish to registry
        run: |
          docker push my.private.registry.com/my-app:latest
```

**3. Using Environment-Specific Secrets:**
When you need different secrets for different deployment stages.

```yaml
jobs:
  deploy_to_production:
    runs-on: ubuntu-latest
    environment: Production # This links the job to the 'Production' environment secrets
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to production server
        uses: some-deploy-action@v1
        with:
          host: prod.example.com
          api_token: ${{ secrets.PROD_DEPLOY_TOKEN }} # This secret must be defined in the 'Production' environment settings
```

## Environment-Specific Notes

The "secret not found or empty" error can manifest differently or have unique considerations depending on your overall infrastructure.

*   **Cloud Providers (AWS, Azure, GCP):**
    When integrating with cloud services, you might be using an external secret manager (e.g., AWS Secrets Manager, Azure Key Vault, Google Secret Manager). In this scenario, GitHub Actions would typically use OpenID Connect (OIDC) to assume an IAM role (AWS), workload identity (GCP), or federated credentials (Azure) that has permissions to *fetch* secrets from these external services. If you get a "secret not found" error, it could mean:
    *   The OIDC configuration is incorrect, and GitHub Actions can't even assume the necessary role.
    *   The assumed role/identity lacks permissions to read the *specific* secret from the external manager.
    *   The secret fetch operation itself (e.g., a custom script or action to retrieve the secret) is failing, and thus the secret isn't being injected into the GHA workflow as expected. I've often seen this when the external secret name in the fetch script doesn't match the actual secret name in Key Vault.

*   **Docker Builds:**
    If your workflow builds Docker images, you might need to pass secrets into the build context (e.g., for `apt` keys, private package registry credentials). The `docker build` command has options like `--secret` (with BuildKit) or `--build-arg`. If a secret needed for the build process isn't correctly passed or mounted, the build will fail, potentially with a similar "credential not found" or "authentication failed" error, rather than a GHA-level "secret not found." Ensure your Dockerfile and `docker build` command are properly set up to consume secrets securely, avoiding `--build-arg` for sensitive info.

*   **Local Development:**
    GitHub Actions secrets are inherently tied to the GitHub platform. You won't typically encounter this *exact* error during local development unless you're using a tool to simulate GitHub Actions locally. However, a common parallel scenario is when developers rely on `.env` files for local environment variables. When transitioning to CI/CD, these `.env` variables *must* be correctly mirrored as GitHub Secrets. I've frequently seen teams forget to port a critical variable from their `.env.production` file into a GitHub Environment secret, leading to deployment failures. Always ensure your local environment variables have corresponding, securely stored secrets in GitHub Actions.

## Frequently Asked Questions

**Q: Can I see the value of a secret in GitHub Actions logs?**
**A:** No, and this is a critical security feature. GitHub Actions automatically redacts (masks) any secret values from the workflow logs. If you try to `echo` a secret, it will appear as `***` or similar in the log output. This prevents accidental exposure of sensitive data.

**Q: How do I share secrets between repositories in the same organization?**
**A:** You can use Organization-level secrets. Go to `Organization Settings > Secrets and variables > Actions`, create the secret there, and then specify which repositories can access it. This is ideal for shared API keys or tokens used across multiple projects.

**Q: What if I need different secret values for different environments (e.g., staging vs. production)?**
**A:** Use GitHub Environments. You can define environments (e.g., "Staging," "Production") under `Repository Settings > Environments`. Within each environment, you can then add environment-specific secrets. Your workflow jobs can then specify `environment: Staging` to ensure they only access the secrets relevant to that environment.

**Q: My workflow is triggered by a pull request from a fork. Why can't it access repository secrets?**
**A:** For security reasons, workflows triggered by `pull_request` events from *forked* repositories do not have access to repository secrets. This prevents malicious contributors from submitting a PR that tries to exfiltrate your secrets. If you need to access secrets for PRs from forks, you must use the `pull_request_target` event (which runs in the context of the *base* repository) but be extremely cautious about what code you execute from the untrusted fork within this context.

**Q: The secret *is* defined, and I've checked for typos, but I'm still getting the error. What else could it be?**
**A:** Double-check the casing of the secret name in both your workflow and the GitHub settings; secret names are case-sensitive. Also, verify that the secret truly has a non-empty value. Sometimes, even if it appears to be set, re-saving the secret (e.g., deleting and recreating, or just updating its value to confirm it's not blank) can resolve caching or state issues that might be preventing GitHub from recognizing it.

## Related Errors

*   [openai-401](/errors/openai-401.html)
*   [gemini-401](/errors/gemini-401.html)