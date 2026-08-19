# GitHub Actions Error: secret not found or empty
> Encountering the "secret not found or empty" error in GitHub Actions means your workflow is trying to use a secret that hasn't been properly defined or is empty; this guide explains how to fix it.

## What This Error Means

When a GitHub Actions workflow fails with the error message "secret not found or empty," it indicates that a secret referenced within your workflow file (e.g., `github-actions.yml`) cannot be resolved at runtime. Specifically, your workflow is attempting to access a variable using the syntax `${{ secrets.MY_SECRET_NAME }}`, but GitHub's Actions runner environment is unable to locate a secret with that exact name, or it found one but its value was empty.

This error is a security measure designed to prevent sensitive information from being exposed or used incorrectly. Instead of failing silently or using a blank value, GitHub Actions explicitly flags this issue, forcing you to address the missing or empty secret. It's a common stumbling block for new and experienced CI/CD practitioners alike, primarily because secret management involves careful configuration outside the workflow file itself.

## Why It Happens

The core reason this error occurs is a mismatch between what your workflow expects and what GitHub provides. GitHub Actions secrets are environment variables that are encrypted and stored outside your public repository code. They are injected into the workflow's runtime environment just before a job starts. This separation is crucial for security, ensuring that sensitive data like API keys, tokens, or credentials are not hardcoded into your version control system.

The "secret not found or empty" error happens because the lookup mechanism fails. When a step in your workflow tries to access `${{ secrets.MY_SECRET_NAME }}`, the Actions runner performs a check across several scopes (repository, organization, environment) to find a secret matching `MY_SECRET_NAME`. If this search yields no result, or if the found secret has an empty string as its value, the workflow aborts with this specific error. In my experience, this usually points to a misconfiguration rather than a flaw in the workflow logic itself.

## Common Causes

Identifying the exact cause of a "secret not found or empty" error often comes down to meticulously checking configuration details. Here are the most common culprits I've encountered in production environments:

1.  **Typographical Error in Workflow File:** This is perhaps the most frequent cause. A simple misspelling in your workflow's `env:` block or `with:` parameters for an action can lead to this. For example, referencing `secrets.API_KEY` when the actual secret name is `API_TOKEN`. Remember, secret names are case-sensitive.
2.  **Secret Not Defined:** The secret simply hasn't been created in the GitHub repository, organization, or environment settings where the workflow is running. It's easy to forget to add a new secret after modifying a workflow.
3.  **Incorrect Scope:** GitHub secrets can be defined at different levels:
    *   **Repository Secrets:** Specific to a single repository.
    *   **Organization Secrets:** Available to multiple repositories within an organization, with configurable access policies (e.g., all repositories, private repositories, selected repositories).
    *   **Environment Secrets:** Specific to a deployment environment (e.g., `production`, `staging`), which jobs must explicitly target.
    If your workflow is trying to access an organization secret that isn't enabled for its repository, or an environment secret when the job isn't targeting that environment, it will fail. I've seen this happen frequently when porting workflows between repos or setting up new environments.
4.  **Empty Secret Value:** Even if a secret exists, if its value was set to an empty string during creation or an update, GitHub Actions will treat it as "not found." The system expects a non-empty string for valid secrets.
5.  **Case Sensitivity Mismatch:** GitHub secrets are strictly case-sensitive. If you define a secret as `MY_SECRET` but your workflow references `my_secret`, it will not be found.
6.  **Restricted Access Policies:** For organization secrets, access can be restricted to specific repositories. For environment secrets, environment protection rules (like required reviewers or waiting timers) might prevent secrets from being injected if the rules haven't been met.
7.  **Branch Protection Rules:** While less direct, certain branch protection rules or environment protection rules might indirectly affect the availability of secrets if they prevent a workflow from running in an environment that holds the necessary secrets.

## Step-by-Step Fix

Addressing the "secret not found or empty" error requires a systematic approach. Follow these steps to diagnose and resolve the issue:

1.  **Identify the Failing Workflow Run:**
    *   Navigate to your repository on GitHub.com.
    *   Click on the "Actions" tab.
    *   Find the workflow run that failed and click on it.
    *   Identify the specific job and step that produced the "secret not found or empty" error message. The error output often clearly states which secret name is missing (e.g., `API_KEY`).

2.  **Verify Secret Name in Workflow File:**
    *   Open the relevant `.github/workflows/*.yml` file.
    *   Locate where the failing secret is referenced. It will look like `${{ secrets.YOUR_SECRET_NAME }}`.
    *   **Crucially, double-check for typos.** Compare the exact spelling and casing of `YOUR_SECRET_NAME` in the workflow against what you *expect* it to be. Any discrepancy, even a single character or case mismatch, will cause the error.
    *   **Example of workflow usage:**
        ```yaml
        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - name: Use My Secret
                run: echo "My secret starts with: ${{ secrets.MY_API_KEY_SECRET | slice(0, 5) }}"
                env:
                  DEPLOY_TOKEN: ${{ secrets.DEPLOYMENT_TOKEN }} # Check this one
        ```
        In this example, if the error pointed to `DEPLOYMENT_TOKEN`, you'd focus on that line.

3.  **Check Repository Secrets:**
    *   In your repository, go to `Settings > Secrets and variables > Actions`.
    *   Under the "Secrets" tab, look for a secret with the *exact* name identified in Step 2.
    *   **Verify Name:** Ensure the name matches perfectly, including case. `MY_API_KEY` is different from `My_Api_Key`.
    *   **Verify Value:** While you cannot view secret values after they're set, you can update them. If you suspect the secret might be empty, update it with a non-empty value. This is a common oversight where a secret is created but no value is provided.

4.  **Check Organization Secrets (If Applicable):**
    *   If your secret is expected to be an organization-level secret, navigate to your Organization's settings (`github.com/organizations/YOUR_ORG_NAME/settings`).
    *   Go to `Secrets and variables > Actions`.
    *   Again, verify the *exact* name and ensure its access policy allows it to be used by the specific repository where your workflow is running. It might be restricted to "Private repositories" or "Selected repositories."

5.  **Check Environment Secrets (If Applicable):**
    *   If your workflow job is targeting a specific environment (e.g., `environment: production` in your workflow YAML), the secret might be defined within that environment.
    *   In your repository, go to `Settings > Environments`.
    *   Click on the relevant environment (e.g., `production`).
    *   Under "Environment secrets," verify the *exact* secret name.
    *   Ensure the job *is* correctly configured to use this environment in the workflow file.
    *   **Workflow snippet for environment:**
        ```yaml
        jobs:
          deploy_prod:
            runs-on: ubuntu-latest
            environment: production # This line is key for environment secrets
            steps:
              - name: Deploy to Prod
                run: |
                  echo "Secret for prod: ${{ secrets.PROD_API_KEY }}"
        ```
    *   If `PROD_API_KEY` is an environment secret for `production`, the job *must* specify `environment: production`.

6.  **Consider Temporary Debugging (Caution!):**
    *   For **non-sensitive** values or during initial setup, you could temporarily (and **never commit this change!**) replace the secret reference with a hardcoded, non-empty dummy string in your workflow to confirm that the *secret availability* is the problem, not how it's being used by the action. For example, `echo "Debug value: hardcoded-dummy-key"`. This confirms if the workflow logic itself is sound. **Immediately revert this for sensitive data.**

7.  **Re-run the Workflow:**
    *   After making the necessary corrections (fixing typos, adding the secret, updating its value, or adjusting scope), commit your changes (if applicable) and re-run the workflow.

In my experience, 90% of these issues are resolved by carefully comparing the secret name in the workflow file character-by-character with its definition in GitHub's UI.

## Code Examples

Here are common scenarios showing how secrets are referenced in GitHub Actions workflows. These are concise and copy-paste ready examples.

**1. Using a Secret in an `env` Block:**
This is the most common way to make a secret available as an environment variable to all steps within a job or a specific step.

```yaml
name: Example Workflow with Environment Secret
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Authenticate with Service
        # MY_SERVICE_TOKEN must be defined as a repository, organization, or environment secret.
        run: |
          echo "Attempting to authenticate..."
          echo "Token starts with: ${{ secrets.MY_SERVICE_TOKEN | slice(0, 5) }}"
          # In a real scenario, you'd use this token with a CLI or API call
          # For example: auth-cli login --token "${{ secrets.MY_SERVICE_TOKEN }}"
        env:
          SERVICE_AUTH_TOKEN: ${{ secrets.MY_SERVICE_TOKEN }} # Secret made available as ENV variable
          ANOTHER_VAR: "some-value"
```

**2. Using a Secret with `with` Parameters of an Action:**
Many third-party actions accept secrets directly as input parameters.

```yaml
name: Example Workflow with Action Secret
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Deploy to Cloud Provider
        uses: your-org/deploy-action@v1 # Replace with actual action
        with:
          # CLOUD_API_KEY must be defined as a repository, organization, or environment secret.
          api-key: ${{ secrets.CLOUD_API_KEY }}
          region: 'us-east-1'
          target-env: 'production'
      - name: Notify Slack
        uses: rtCamp/action-slack-notify@v2 # Example Slack notification
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }} # Secret for Slack webhook
        with:
          status: success
          message: 'Deployment complete!'
```

**3. Using an Environment-Specific Secret:**
When a job needs a secret defined in a specific GitHub Environment.

```yaml
name: Environment-Specific Deployment
on:
  push:
    branches:
      - main
jobs:
  deploy_production:
    runs-on: ubuntu-latest
    environment: production # This job explicitly targets the 'production' environment
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Deploy application to Production
        run: |
          echo "Deploying with production API Key: ${{ secrets.PROD_DB_PASSWORD | slice(0, 5) }}"
          # Use PROD_DB_PASSWORD which is defined in the 'production' environment secrets
          ./deploy-prod.sh --password "${{ secrets.PROD_DB_PASSWORD }}"
```

In all these examples, `secrets.MY_SERVICE_TOKEN`, `secrets.CLOUD_API_KEY`, `secrets.SLACK_WEBHOOK`, and `secrets.PROD_DB_PASSWORD` are placeholders for the actual secret names you would define in your GitHub repository, organization, or environment settings.

## Environment-Specific Notes

While the core concept of GitHub Actions secrets remains consistent, there are subtle differences in how they are managed or perceived across different GitHub environments:

*   **GitHub.com (Cloud):** This is the most common scenario. Secrets are managed directly through the GitHub web UI (`Settings > Secrets and variables > Actions` for repository secrets, or equivalent paths for organization/environment secrets). The steps outlined in the "Step-by-Step Fix" section primarily apply to this environment. Access to organization secrets is governed by the organization owner's policies. Environment secrets offer an additional layer of control, including protection rules like required reviewers, which can delay or block workflow runs and thus the injection of secrets until conditions are met.

*   **GitHub Enterprise Server (GHES):** For self-hosted instances of GitHub Enterprise, the principles are largely the same. However, administrators of the GHES instance have more granular control over global settings, secret policies, and runner configurations. In a GHES setup, you might encounter additional restrictions or default behaviors set by your enterprise's IT team. For instance, specific types of secrets might be disallowed, or certain naming conventions enforced. When troubleshooting on GHES, it's wise to consult with your GHES administrator if the standard fixes don't apply, as they might have specific configurations affecting secret visibility or injection.

*   **Local Development with `act` or Similar Tools:** When developing or testing GitHub Actions workflows locally using tools like `act` (which emulates the GitHub Actions runner), secrets are not automatically available from your GitHub repository. You need to provide them explicitly. For `act`, this typically involves:
    *   Using a `.env` file in your local directory (e.g., `MY_SECRET=my-local-value`).
    *   Passing secrets via command-line flags (e.g., `act -s MY_SECRET=my-local-value`).
    *   Using an external secrets provider configuration.
    The "secret not found or empty" error during local testing usually means you've forgotten to map the required secrets to your local `act` run. This is a common point of confusion as the local testing environment doesn't automatically inherit the cloud-based secret store. I've often seen engineers troubleshoot a production workflow issue only to realize they forgot to emulate the full secret environment locally.

Regardless of the environment, the underlying cause is always that the secret name referenced in the workflow is not being found or contains an empty value within the scope of the running job.

## Frequently Asked Questions

**Q: Are GitHub secrets case-sensitive?**
**A:** Yes, absolutely. `MY_API_KEY` is treated as a completely different secret from `my_api_key`. When you define a secret and when you reference it in your workflow, the casing must match exactly. This is one of the most common causes of the "secret not found" error, in my experience.

**Q: Can an organization secret override a repository secret with the same name?**
**A:** No. If a secret with the same name exists at multiple levels (organization, repository, environment), GitHub Actions prioritizes them. The order of precedence, from highest to lowest, is: **Environment secrets > Repository secrets > Organization secrets**. This means a repository secret will override an organization secret of the same name, and an environment secret (if the job targets that environment) will override both repository and organization secrets.

**Q: What if my secret *is* defined, but I'm still getting the error?**
**A:** This usually points to one of a few subtle issues:
1.  **Typo or Extra Spaces:** Re-check the secret name in your workflow and in GitHub settings for any hidden characters, leading/trailing spaces, or subtle typos you might have missed (e.g., `MY_SECRET ` vs `MY_SECRET`).
2.  **Empty Value:** Confirm the secret's value is not empty. While you can't view it, you can update it to ensure it's populated.
3.  **Scope Mismatch:** Ensure the secret is defined in the correct scope (repository, organization, or a specific environment) and that your workflow job is correctly configured to access that scope (e.g., `environment: my-env`).
4.  **Access Policies:** For organization or environment secrets, verify that the repository or job has the necessary permissions to access them.

**Q: How do I confirm a secret's value without exposing it in logs?**
**A:** GitHub's security model prevents direct viewing or logging of secret values. If you need to verify if a secret has a value or what its first few characters are (for debugging, **only for non-sensitive parts!**), you can use string manipulation in a `run` step. For instance, `echo "Secret starts with: ${{ secrets.MY_SECRET | slice(0, 5) }}"`. This will print the first 5 characters (or fewer if the secret is shorter) while still redacting the full secret. For highly sensitive secrets, rely on careful entry and confirmation by the person who set it.

**Q: Why does my workflow fail with "secret not found" on a specific branch but work on `main`?**
**A:** This scenario often indicates that the secrets are tied to branch protection rules or environments that are only applied to `main` or specific release branches. For instance, if your `main` branch has an associated deployment environment (`production`) that holds specific secrets, and you try to run the *same* workflow on a feature branch without that environment defined or accessible, the environment-specific secrets won't be found, leading to this error. Check your environment configurations and branch protection rules.

## Related Errors