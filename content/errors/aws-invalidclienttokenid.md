# AWS InvalidClientTokenId: The security token is invalid
> Encountering AWS InvalidClientTokenId means your security token is invalid; this guide explains how to fix it.

As a Senior DevOps Engineer, I've spent countless hours debugging AWS environments, and the `InvalidClientTokenId` error is one I've come across repeatedly. It's frustrating because it stops you dead in your tracks, preventing any interaction with AWS services. The good news is, despite its seemingly cryptic nature, it's almost always a client-side issue with a clear path to resolution. This guide will walk you through understanding, diagnosing, and fixing this common AWS authentication problem.

## What This Error Means

At its core, `InvalidClientTokenId: The security token is invalid` signifies that the AWS service you're trying to interact with has rejected your authentication credentials. When you make a request to AWS, whether through the CLI, an SDK, or a direct API call, you include a "security token." This token isn't a single item; it's a bundle of information that typically includes your AWS Access Key ID, Secret Access Key, and sometimes an AWS Session Token (for temporary credentials).

AWS uses this information to authenticate your request. When you see `InvalidClientTokenId`, it means that the credentials provided are either:
1.  **Malformed:** There's a typo, an extra space, or some other corruption.
2.  **Expired:** The temporary credentials you're using have passed their validity period.
3.  **Incorrect:** The credentials themselves are valid, but they don't belong to the account or region you're trying to access, or they've been revoked.

It's crucial to understand that this is an authentication error, not an authorization error. AWS isn't saying you *don't have permission* to perform an action (that would typically be `AccessDenied`). Instead, it's saying "I don't even recognize who you are based on these credentials."

## Why It Happens

This error happens because AWS's authentication service (IAM) cannot validate the signature of your request against the provided access key ID. Every AWS API call is cryptographically signed using your secret access key. AWS receives the request, takes your access key ID, retrieves the corresponding secret key it has on file, and attempts to re-sign the request with it. If the signature it generates doesn't match the signature you sent, or if the access key ID doesn't exist, it rejects the request with `InvalidClientTokenId`.

The "security token" in the error message is a generic term referring to the entire set of authentication data you're presenting. This can include:

*   **Permanent IAM User Credentials:** An `AKIA...` Access Key ID and its associated Secret Access Key. These are long-lived and should be treated with extreme care.
*   **Temporary Security Credentials:** Issued by AWS Security Token Service (STS) when you assume an IAM role, use multi-factor authentication (MFA), or federate access. These include an `ASIA...` or `AROA...` Access Key ID, a Secret Access Key, *and* a Session Token. These are time-limited.

In my experience, the vast majority of `InvalidClientTokenId` errors stem from issues with *temporary* credentials, especially their expiration. However, problems with permanent credentials, such as typos or revocation, also lead to this error.

## Common Causes

Let's break down the most frequent culprits behind this error:

1.  **Expired Temporary Credentials:** This is the number one cause. If you've recently assumed an IAM role (e.g., using `aws sso login`, `aws-vault`, or `sts assume-role`) and haven't refreshed your session, your temporary credentials will expire. AWS CLI and SDKs don't automatically refresh these in all scenarios.
2.  **Typographical Errors or Malformed Credentials:** A stray space, an incorrect character, a copied-and-pasted incomplete key, or an invisible character can render credentials invalid. This is common when manually configuring `~/.aws/credentials` or setting environment variables.
3.  **Incorrect AWS Region:** While less direct, if your credentials are valid for `us-east-1` but your CLI/SDK is attempting to interact with a service in `eu-west-1` and you don't have global service permissions or explicit regional access defined, you might encounter this. More often, a region mismatch leads to a different error, but I've seen it contribute to `InvalidClientTokenId` when the context is particularly confused (e.g., an `sts` call to a non-global endpoint).
4.  **Incorrect Environment Variables Precedence:** AWS credentials can be sourced from environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`), shared credentials files (`~/.aws/credentials`), or shared config files (`~/.aws/config`). Environment variables always take precedence. If you have stale or incorrect environment variables set, they will override valid credentials in your files, leading to this error.
5.  **Wrong AWS Profile Used:** If you manage multiple AWS profiles (e.g., `dev`, `staging`, `prod`) and your command explicitly or implicitly uses a profile with invalid or expired credentials, you'll see this error. Forgetting to specify `--profile` or having a default profile misconfigured is a common pitfall.
6.  **System Clock Skew:** Although rare in modern systems, if your local machine's system clock is significantly out of sync with NTP servers and AWS's servers, the cryptographic signature (which includes a timestamp) can appear invalid to AWS.
7.  **Credentials Leaked and Revoked:** If your access keys were compromised, you might have revoked them in the IAM console. Any subsequent attempts to use those revoked keys will result in this error.

## Step-by-Step Fix

Let's systematically troubleshoot and resolve `InvalidClientTokenId`.

### 1. Verify Your Current AWS Identity

The first and most important step is to ask AWS *who it thinks you are*.

```bash
aws sts get-caller-identity
```

**Expected Output (if successful):**

```json
{
    "UserId": "AROA...:your-assumed-role-session-name",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/YourRoleName/your-assumed-role-session-name"
}
```
or
```json
{
    "UserId": "AIDAA...:your-iam-user-name",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-iam-user-name"
}
```

If `aws sts get-caller-identity` *also* returns `InvalidClientTokenId`, then the problem lies with the fundamental credentials your CLI is attempting to use. If it *succeeds*, but a subsequent command fails with the error, then the specific command's context (e.g., `--profile` or region) might be the issue.

### 2. Check Environment Variables

Environment variables take precedence over credentials files. A stale `AWS_ACCESS_KEY_ID` or `AWS_SESSION_TOKEN` is a very common source of this error.

```bash
env | grep AWS
```

Look for variables like `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`, `AWS_DEFAULT_REGION`, and `AWS_REGION`.

If you find suspicious or incorrect variables, unset them:

```bash
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
unset AWS_PROFILE # Only if you suspect it's pointing to a bad profile
# ...and any other AWS-related environment variables you suspect
```
After unsetting, try `aws sts get-caller-identity` again.

### 3. Inspect Your AWS Credentials and Config Files

By default, AWS CLI and SDKs look for `~/.aws/credentials` and `~/.aws/config`.

**`~/.aws/credentials`:**
Open this file and check the profiles you're using.

```ini
[default]
aws_access_key_id = AKIAXXXXXXXXXXXXXXXX
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY_GOES_HERE

[my-dev-profile]
aws_access_key_id = ASIAXXXXXXXXXXXXXXXX # Note ASIA for temporary credentials
aws_secret_access_key = ANOTHER_SECRET_ACCESS_KEY
aws_session_token = FQoDYXdzELL... # Crucial for temporary credentials
```

*   **Look for typos:** Even a single character or an extra space can invalidate keys.
*   **Check for `aws_session_token`:** If you're using temporary credentials (e.g., from an `assume-role` operation), this token *must* be present alongside the `aws_access_key_id` and `aws_secret_access_key`. If it's missing or expired, you'll get `InvalidClientTokenId`.
*   **Verify key format:** Permanent keys start with `AKIA`. Temporary keys (from STS) start with `ASIA` or `AROA`.

**`~/.aws/config`:**
This file defines region, output format, and can link to source profiles for role assumption.

```ini
[default]
region = us-east-1
output = json

[profile my-dev-profile]
region = us-west-2
output = json
source_profile = default # For role assumption
role_arn = arn:aws:iam::123456789012:role/MyDevRole
mfa_serial = arn:aws:iam::123456789012:mfa/myuser
```

*   **Region:** Ensure the region configured in your profile matches the region you intend to operate in. While not always the direct cause, a mismatch can sometimes confuse the SDK/CLI enough to manifest this error.
*   **Source Profile/Role ARN:** If you're using `assume-role` via your config, ensure the `source_profile` points to a *valid* profile and the `role_arn` is correct. If the source profile itself has invalid credentials, the `assume-role` call will fail, leading to expired or invalid temporary credentials for the target role.

### 4. Refresh Temporary Credentials

If you're using temporary credentials (which is highly recommended for security), they expire.

*   **AWS SSO:** If you use `aws sso login`, simply run it again:
    ```bash
    aws sso login --profile my-sso-profile
    ```
    This will open a browser for re-authentication and refresh your session.
*   **Manual STS Assume Role/MFA:** If you manually get session tokens, you'll need to rerun that process:
    ```bash
    aws sts get-session-token --serial-number arn:aws:iam::123456789012:mfa/myuser --token-code 123456
    ```
    Then, update your `~/.aws/credentials` with the new `AccessKeyId`, `SecretAccessKey`, and `SessionToken`.
*   **`aws-vault` or similar tools:** These tools usually have a command to refresh or re-login. For `aws-vault`, it typically prompts for MFA when needed or `aws-vault login` will refresh.

### 5. Explicitly Specify Region

To rule out region confusion, always try specifying the region explicitly for commands:

```bash
aws s3 ls --region us-east-1
aws ec2 describe-instances --region eu-west-2
```

This ensures your CLI isn't picking up a default or inferred region that might not align with your credentials or the service you're targeting.

### 6. Check System Clock

Run `date` in your terminal. If the time is wildly off, correct it. This is rare but can cause signature validation failures due to timestamp mismatches.

### 7. Generate New Access Keys (Last Resort)

If you've checked everything above and suspect your *permanent* IAM user keys are genuinely compromised, revoked, or corrupted beyond repair, go to the IAM console:
1.  Navigate to your IAM user.
2.  Go to the "Security credentials" tab.
3.  **Deactivate** or **Delete** the old access key.
4.  **Create new access key**.
5.  **Immediately update** your `~/.aws/credentials` file or environment variables with the new keys.

**Warning:** This should be a last resort for permanent keys, as it will break any applications or scripts relying on the old key.

## Code Examples

Here are some concise examples of how credentials are typically managed and where the error might manifest.

### Python (Boto3)

```python
import boto3
from botocore.exceptions import ClientError

# Example 1: Using default profile (from ~/.aws/credentials or env vars)
try:
    s3_client = boto3.client('s3')
    response = s3_client.list_buckets()
    print("Buckets:", [b['Name'] for b in response['Buckets']])
except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidClientTokenId':
        print(f"ERROR: InvalidClientTokenId. Check your AWS credentials. Details: {e}")
    else:
        raise # Re-raise other errors

# Example 2: Specifying a profile
try:
    s3_client = boto3.client('s3', profile_name='my-dev-profile')
    response = s3_client.list_buckets()
    print(f"Buckets from 'my-dev-profile': {[b['Name'] for b in response['Buckets']]}")
except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidClientTokenId':
        print(f"ERROR with 'my-dev-profile': InvalidClientTokenId. Check its credentials. Details: {e}")
    else:
        raise

# Example 3: Explicitly providing credentials (not recommended for production, better to use profiles/roles)
# Ensure these are real, valid credentials or it will fail
ACCESS_KEY = "AKIA..."
SECRET_KEY = "YOUR_SECRET..."
SESSION_TOKEN = "FQoDYXdzELL..." # Only if using temporary credentials

try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN, # Remove if using permanent keys
        region_name='us-east-1'
    )
    response = s3_client.list_buckets()
    print(f"Buckets from explicit keys: {[b['Name'] for b in response['Buckets']]}")
except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidClientTokenId':
        print(f"ERROR with explicit keys: InvalidClientTokenId. Check these keys. Details: {e}")
    else:
        raise
```

### AWS CLI

```bash
# Get your current caller identity (the best way to check credentials)
aws sts get-caller-identity

# List S3 buckets using the default profile
aws s3 ls

# List S3 buckets using a specific profile
aws s3 ls --profile my-dev-profile

# Configure (or re-configure) your default profile
aws configure
# AWS Access Key ID [****************EXAMPLE]: AKIA...
# AWS Secret Access Key [****************EXAMPLE]: YOUR_SECRET...
# Default region name [us-east-1]: us-east-1
# Default output format [json]: json

# Set credentials directly for a profile (careful with secrets in history!)
aws configure set aws_access_key_id AKIAXXXXXXXXXXXXXXXX --profile new-profile
aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY_GOES_HERE --profile new-profile
aws configure set aws_session_token FQoDYXdzELL... --profile new-profile # Only for temporary
aws configure set region us-east-1 --profile new-profile

# Unset environment variables (if you suspect them)
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE
```

## Environment-Specific Notes

The `InvalidClientTokenId` error can manifest differently or have different underlying causes depending on your execution environment.

### Local Development

This is where you'll most frequently encounter the error, primarily due to:
*   **Manual configuration mistakes:** Typos in `~/.aws/credentials` or `~/.aws/config`.
*   **Expired temporary credentials:** Especially if you use `aws sso login` or `aws-vault` and forget to refresh your session after a day.
*   **Conflicting environment variables:** I've seen many cases where `AWS_ACCESS_KEY_ID` was set in a `.bashrc` or `.zshrc` from an old project and overridden current, valid credentials.
*   **Multiple terminal windows:** One window might have different environment variables set than another, leading to inconsistent behavior.

**Recommendation:** Always start your debugging by checking `env | grep AWS` and then `aws sts get-caller-identity`. Use credential management tools like `aws-vault` or `aws sso login` to streamline temporary credential management.

### Docker Containers

When your application runs inside a Docker container, credentials can be handled in several ways, each with its own pitfalls:

*   **Environment variables:** Credentials might be passed into the container via `docker run -e` flags or `environment` sections in `docker-compose.yml`. If these are stale or incorrect, the container will fail.
*   **Mounted `~/.aws` directory:** Less common but possible. If `~/.aws` is mounted from the host, ensure the host's credentials are correct.
*   **IAM Roles for tasks/pods:** In ECS, EKS, or other container orchestration services, the preferred method is to assign an IAM role to the task definition or Kubernetes service account. If you're getting `InvalidClientTokenId` in a container that *should* be using a role, it implies:
    *   The role isn't correctly assigned to the task/pod.
    *   The container's application isn't correctly configured to *assume* the role or fetch credentials from the instance metadata service.
    *   Someone hardcoded explicit (now invalid) credentials inside the container image or startup script, overriding the IAM role.

**Recommendation:** For Docker, check the Dockerfile, `docker-compose.yml`, and task definitions (ECS/EKS) for how AWS credentials are being injected. Avoid hardcoding credentials directly into container images.

### Cloud (EC2, ECS, EKS, Lambda, etc.)

In most AWS services like EC2 instances, ECS tasks, EKS pods, or Lambda functions, the best practice is to use **IAM roles attached to the compute resource**. This eliminates the need for explicit credentials. If you see `InvalidClientTokenId` in these environments:

*   **EC2 Instance:** Verify that the IAM instance profile is correctly attached to the EC2 instance and that the EC2 instance has network access to the AWS STS endpoint (typically `sts.<region>.amazonaws.com`).
*   **Lambda Function:** Check the execution role assigned to the Lambda function. This role is what the Lambda service assumes to execute your function. Ensure it has the necessary permissions. If your function is calling *another* AWS service, it uses its assigned execution role. If the function is configured to `assume-role` into *another* role, that secondary role's credentials might be the problem.
*   **ECS/EKS:** Similar to EC2, ensure the task/pod has an IAM role assigned to it (either via Task Role in ECS or IAM Roles for Service Accounts in EKS). If an application within a task/pod is trying to use hardcoded credentials instead of the assigned role, those hardcoded credentials are likely expired or invalid.

**Recommendation:** Always favor IAM roles over explicit credentials in the cloud. If you get this error, verify the role attachment and ensure no hardcoded credentials are taking precedence.

## Frequently Asked Questions

### Q: Is `InvalidClientTokenId` an AWS service outage?
A: No, almost never. This error means AWS is successfully receiving your request but cannot authenticate it. It's nearly always an issue with the credentials you're providing, not with the AWS service itself.

### Q: Can network issues or a firewall cause this error?
A: Generally, no. Network issues would typically result in connection timeouts or different types of network errors, not an authentication error like `InvalidClientTokenId`. If AWS cannot even receive your request, it can't tell you the token is invalid.

### Q: How long do temporary AWS credentials last?
A: The duration varies. `aws sts get-session-token` can issue credentials valid for up to 36 hours. `aws sts assume-role` can issue credentials for up to 12 hours. `aws sso login` typically issues credentials for a period configured by your SSO administrator, often 1-8 hours. Always assume they will expire and refresh them regularly.

### Q: I'm using `aws configure` to set my keys, but I still get the error. Why?
A: Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`) take precedence over `~/.aws/credentials` and `~/.aws/config`. If you have outdated or incorrect environment variables set, they will override whatever you set with `aws configure`. Always check `env | grep AWS` first.

### Q: Does MFA affect this error?
A: Yes. If your IAM user or role requires MFA for an action, and you're attempting to use temporary credentials that were generated *without* an MFA token (or the MFA session has expired), you will often receive `InvalidClientTokenId` when trying to assume a role or perform certain actions. The "token" being invalid here means your entire authentication context (including MFA status) is not sufficient or expired.

## Related Errors

- [openai-401](/errors/openai-401.html)