# AWS InvalidClientTokenId: The security token is invalid
> Encountering InvalidClientTokenId means your AWS credentials are malformed, expired, or for the wrong region; this guide explains how to fix it.

## What This Error Means

When you encounter the `InvalidClientTokenId: The security token is invalid` error while interacting with AWS via the CLI or SDK, it means that AWS has rejected the credentials you are providing. This is fundamentally an *authentication* error, not an *authorization* error. Your client (CLI tool, SDK application, script) has attempted to authenticate itself to AWS using an access key ID, and potentially a secret access key and a session token, but AWS has determined that the provided "security token" (which collectively refers to these credentials) is invalid.

In simpler terms, AWS doesn't recognize your identity or believes the method you're using to prove your identity is flawed. It's like presenting a passport that's expired, forged, or belongs to someone else at border control – you won't get in.

## Why It Happens

This error occurs when the AWS service endpoint you're trying to reach cannot validate the access key ID provided in your request. AWS's authentication system checks several factors against the access key ID to determine its validity:

1.  **Existence:** Does an access key with this ID actually exist within your AWS account?
2.  **Format:** Is the access key ID correctly formatted (e.g., `AKIA...`)?
3.  **Status:** Is the access key active, or has it been deactivated or deleted?
4.  **Expiration:** If it's a temporary security token (like those obtained from AWS STS for assumed roles or MFA sessions), has it expired?
5.  **Consistency:** In some edge cases, especially with temporary credentials, there can be regional nuances or inconsistencies if the token was generated in one region but used in another, or if there's a mismatch in the assumed role session context.

In my experience, the vast majority of `InvalidClientTokenId` errors boil down to a mismatch or misconfiguration of these critical pieces of information. It's often a simple oversight that can be frustrating to track down if you don't know where to look.

## Common Causes

Let's break down the typical culprits behind this error:

*   **Typographical Errors:** This is surprisingly common. A single incorrect character in `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` will render the entire credential set invalid. I've seen this happen countless times when copying and pasting credentials manually.
*   **Expired Temporary Credentials:** If you're using AWS STS to assume roles (`aws sts assume-role`) or generating temporary credentials via MFA, these tokens have a limited lifespan (often 1 hour, configurable up to 12 hours). Once expired, any attempt to use them will result in `InvalidClientTokenId`. This is a frequent cause in CI/CD pipelines or local development environments where long-running sessions might unknowingly outlast their token.
*   **Incorrect Environment Variables:** Your shell's environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION`) take precedence over `~/.aws/credentials` and `~/.aws/config`. If these are set incorrectly or are stale, they'll override valid configurations.
*   **Incorrect AWS Configuration Files:** Errors in `~/.aws/credentials` (e.g., malformed lines, wrong profile name, incorrect key) or `~/.aws/config` (e.g., wrong region for a profile) can lead to this issue.
*   **Multiple Credential Sources:** AWS CLI/SDKs follow a specific order of precedence for credentials. If you have credentials defined in multiple places (e.g., environment variables, `~/.aws/credentials`, IAM roles on an EC2 instance), an invalid set from a higher-precedence source will be used, masking a valid set elsewhere.
*   **Credentials Deactivated or Deleted:** An IAM user's access key might have been deactivated or deleted in the AWS console or via IAM API calls. If the key is no longer active, AWS will reject it.
*   **Whitespace Issues:** Leading or trailing whitespace in credential values (especially when copied from a UI or `.env` file) can cause them to be parsed incorrectly.
*   **Region Mismatch (Less Common, but Possible):** While access keys are generally global, temporary session tokens obtained from STS *can sometimes* be tied to a specific region where they were generated, or the service you are trying to reach might itself be region-specific and your credentials might not apply correctly. More often, a region mismatch causes authorization errors or "could not connect" type errors, but it's worth checking.

## Step-by-Step Fix

Here's my go-to troubleshooting process when I hit an `InvalidClientTokenId` error:

1.  **Verify Active Credentials with `aws sts get-caller-identity`**
    This is the quickest way to check if your *currently active* AWS credentials are valid and what identity they represent.
    ```bash
    aws sts get-caller-identity
    ```
    If this command fails with `InvalidClientTokenId`, it confirms your active credentials are the problem. If it succeeds, it tells you which account/user/role your current configuration points to, which can help diagnose if you're authenticating as the *wrong* identity.

2.  **Inspect Environment Variables**
    Environment variables have the highest precedence. Check if any `AWS_` variables are set that might be interfering.
    ```bash
    env | grep AWS
    ```
    Look for `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, and `AWS_REGION`. If these are set and look suspicious, unset them.
    ```bash
    unset AWS_ACCESS_KEY_ID
    unset AWS_SECRET_ACCESS_KEY
    unset AWS_SESSION_TOKEN # If applicable
    unset AWS_REGION        # If you want to rely on config files
    ```
    Then, re-run `aws sts get-caller-identity`.

3.  **Check `~/.aws/credentials` and `~/.aws/config`**
    If environment variables aren't the issue, the next place to look is your AWS configuration files.
    *   **`~/.aws/credentials`:**
        ```ini
        [default]
        aws_access_key_id = AKIAIOSFODNN7EXAMPLE
        aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

        [my-profile]
        aws_access_key_id = ANOTHEREXAMPLEKEY
        aws_secret_access_key = ANOTHERSECRETEXAMPLE
        aws_session_token = # Only for temporary credentials
        ```
        Ensure the `aws_access_key_id` and `aws_secret_access_key` are correct for the profile you're using (or the `default` profile). Double-check for typos or leading/trailing whitespace. If there's an `aws_session_token`, ensure it hasn't expired (it should be absent for permanent IAM keys).

    *   **`~/.aws/config`:**
        ```ini
        [default]
        region = us-east-1

        [profile my-profile]
        region = eu-west-1
        output = json
        ```
        Verify that the `region` setting in your `config` file matches the region the key was generated in or the region where the target resource resides, if that's a factor. If you're using a named profile, ensure you're specifying it correctly with `--profile my-profile` in your CLI commands or via `AWS_PROFILE` environment variable.

4.  **Rotate Temporary Credentials**
    If you're using `aws sts assume-role` or `get-session-token`, your temporary credentials will expire. You need to re-run the command that generates them.
    ```bash
    # Example of re-assuming a role
    unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
    eval $(aws sts assume-role \
        --role-arn arn:aws:iam::123456789012:role/MyRole \
        --role-session-name MySession \
        --duration-seconds 3600 | jq -r '.Credentials | "export AWS_ACCESS_KEY_ID=\(.AccessKeyId)\nexport AWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)\nexport AWS_SESSION_TOKEN=\(.SessionToken)\nexport AWS_SESSION_EXPIRATION=\(.Expiration)"')
    ```
    Then, re-run `aws sts get-caller-identity` to confirm.

5.  **Check IAM Console (Last Resort for Permanent Keys)**
    If you've checked everything local and are using a permanent IAM user access key:
    *   Log into the AWS Management Console.
    *   Navigate to IAM.
    *   Go to "Users" and select the user whose access key you're using.
    *   Click on the "Security credentials" tab.
    *   Find the Access Key ID you're using. Ensure its "Status" is "Active". If it's "Inactive," you'll need to make it active or generate a new one. If you suspect it might be compromised, deactivate it and create a new one.

6.  **Review Application/SDK Configuration**
    If the error is coming from an application using an AWS SDK (e.g., Boto3 in Python, AWS SDK for JavaScript), check how it's loading credentials. The SDKs follow a similar precedence chain. Ensure your application isn't hardcoding old credentials or pointing to an incorrect profile.

## Code Examples

Here are some concise, copy-paste ready examples for credential management.

### Setting Environment Variables (Bash)

```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
# Only for temporary credentials (e.g., from assume-role)
export AWS_SESSION_TOKEN="FQoGZXIvYXdzEJ///////////////////////////w=="
export AWS_REGION="us-east-1" # Or your target region
```

### Unsetting Environment Variables (Bash)

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_REGION
```

### Using `aws configure` to Set Defaults

This command interactively prompts you for credentials and region, saving them to `~/.aws/credentials` and `~/.aws/config` under the `[default]` profile.

```bash
aws configure
# AWS Access Key ID [****************EXAMPLE]: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key [****************EXAMPLEKEY]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name [us-east-1]: us-east-1
# Default output format [json]: json
```

### Checking Current Identity with AWS CLI

```bash
aws sts get-caller-identity
```

### Python Boto3 Example (Implicit Credential Loading)

Boto3 automatically looks for credentials in environment variables, `~/.aws/credentials`, and IAM roles (on EC2/ECS/Lambda).

```python
import boto3

try:
    # This will use the default credentials found in the environment
    sts_client = boto3.client('sts')
    response = sts_client.get_caller_identity()
    print("Successfully authenticated:")
    print(f"User ID: {response['UserId']}")
    print(f"Account: {response['Account']}")
    print(f"ARN: {response['Arn']}")
except Exception as e:
    print(f"Error authenticating: {e}")
```

## Environment-Specific Notes

The source and management of AWS credentials can vary significantly between environments.

*   **Local Development:** Here, you'll most commonly rely on `~/.aws/credentials` (managed by `aws configure` or manually) and environment variables. If you use tools like `aws-vault` or IDE integrations, ensure they are correctly configured and refreshed. I often run into this when switching between multiple client accounts or profiles, forgetting to `export AWS_PROFILE` for the correct one.
*   **Docker Containers:** When running AWS CLI or SDK within a Docker container, you have a few options:
    *   **Environment Variables:** Pass `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc., as environment variables using `-e` flags or in your `docker-compose.yml`.
    *   **Mounting `~/.aws`:** You can mount your host's `~/.aws` directory into the container. Be cautious with this for security reasons in shared environments. `docker run -v ~/.aws:/root/.aws ...`
    *   **IAM Roles (for EC2/ECS/EKS hosts):** If your Docker container is running on an EC2 instance or within an ECS/EKS cluster, the best practice is to assign an IAM role to the host or task definition. The containerized application will then automatically assume this role, removing the need for explicit credentials. If you're seeing `InvalidClientTokenId` in a container with a task role, it often means the application is trying to *override* the role with bad explicit credentials.
*   **CI/CD Pipelines (e.g., GitHub Actions, GitLab CI, Jenkins):** Credentials in CI/CD are typically managed as secrets.
    *   **Environment Variables:** Secrets are injected as environment variables into the build/deploy job. Always ensure these secrets are fresh and correctly mapped. For example, in GitHub Actions, you'd define `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as repository secrets.
    *   **IAM Roles / OIDC:** Increasingly, CI/CD platforms support OpenID Connect (OIDC) to directly assume IAM roles without long-lived access keys. This is the most secure method. If you're setting this up, ensure the OIDC provider configuration, trust policy on the IAM role, and the role ARN in your CI/CD workflow are all accurate. An `InvalidClientTokenId` here might indicate a problem in the initial token exchange for the role.
*   **Cloud Instances (EC2, Lambda, ECS Tasks):** For applications running directly on AWS services, the gold standard is to use **IAM roles**. Assign an appropriate IAM role to your EC2 instance profile, Lambda function, or ECS task definition. The AWS SDK/CLI will automatically pick up these credentials from the instance metadata service. If you encounter `InvalidClientTokenId` in such an environment, it usually means:
    1.  No IAM role is assigned.
    2.  The application is *explicitly configured* with incorrect hardcoded or environment variable credentials, overriding the (non-existent or valid) IAM role.
    3.  The application is attempting to assume *another* role using explicit, invalid credentials.

## Frequently Asked Questions

*   **Q: Is `InvalidClientTokenId` an authorization or an authentication error?**
    **A:** It is strictly an *authentication* error. It means AWS couldn't verify *who you are*, not that you don't have *permission* to perform an action. An authorization error would typically manifest as `AccessDeniedException`.

*   **Q: Can a region mismatch cause this error?**
    **A:** While less common than for `AccessDeniedException`, it can. Specifically, temporary credentials from AWS STS can sometimes be implicitly tied to the region where they were generated, or a service might behave differently depending on the region. Always ensure your configured region matches your intent.

*   **Q: My credentials are correct, but I still get the error. What else could it be?**
    **A:** Double-check for invisible characters (like whitespace) when copying/pasting. Ensure you don't have conflicting environment variables or AWS profiles active. If using an SDK, verify how it's loading credentials – it might be picking up an unexpected source. Finally, re-check the IAM console to ensure the key hasn't been deactivated or deleted by another administrator.

*   **Q: How can I prevent `InvalidClientTokenId` errors in the future?**
    **A:** Prioritize using **IAM roles** for applications running on AWS infrastructure (EC2, Lambda, ECS, EKS). For CI/CD, leverage OIDC integration with IAM roles. On local development, use tools like `aws-vault` or `aws-sso-cli` to manage and refresh temporary credentials automatically, minimizing the use of long-lived access keys. Always rotate temporary credentials promptly when they expire.

## Related Errors
(none)