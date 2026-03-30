# AWS InvalidClientTokenId: The security token is invalid
> Encountering AWS InvalidClientTokenId means your security token is invalid, often due to expired or malformed credentials; this guide explains how to troubleshoot and fix it.

## What This Error Means

The `InvalidClientTokenId: The security token is invalid` error from AWS signifies a fundamental authentication failure. In simpler terms, AWS doesn't recognize the credentials you're presenting. This isn't a permissions error, meaning it's not about *what* you're allowed to do (authorization), but rather *who* you are (authentication). AWS cannot verify your identity based on the `Access Key ID` and `Secret Access Key` provided. When you hit this, the AWS service you're trying to interact with has received a request signed with an access key ID that it doesn't consider valid, either because it's malformed, expired, or simply doesn't exist.

## Why It Happens

At its core, this error means AWS couldn't match the `AWS_ACCESS_KEY_ID` in your request to a valid, active set of credentials. Every interaction with an AWS service requires a signed request, and that signature relies on a valid access key and secret key pair. If any part of this authentication process goes awry – the keys are wrong, they've expired, or there's a mismatch in how the request is signed – you'll be greeted by `InvalidClientTokenId`. In my experience, this usually points to an issue with how credentials are being managed or retrieved by the client application or CLI.

## Common Causes

This error often crops up in a few predictable scenarios. Understanding these common causes is the first step towards a quick resolution.

### Expired Temporary Credentials
This is, hands down, the most frequent culprit. AWS IAM roles and AWS Security Token Service (STS) calls (like `aws sts assume-role`) provide temporary credentials consisting of an `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and crucially, an `AWS_SESSION_TOKEN`. These credentials have a limited lifespan, typically ranging from 15 minutes to 12 hours. If your application or CLI session tries to use these credentials after their expiration, you'll see `InvalidClientTokenId`. I've seen this in production when an automated script relying on assumed roles wasn't properly refreshing its tokens.

### Incorrect or Malformed Credentials
Typos happen. Copy-pasting errors are common. If your `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` is incorrect, truncated, or contains extra characters (like leading/trailing spaces), AWS won't be able to validate them. This can occur when manually configuring credentials in `~/.aws/credentials`, setting environment variables, or even hardcoding them (which, by the way, is a bad practice you should avoid).

### Wrong Default Region or Explicit Region Mismatch
While credentials themselves aren't region-specific, the services you're trying to access *are*. Sometimes, the `InvalidClientTokenId` error can appear when your credentials are valid, but you're trying to interact with a service in a region where those specific credentials (or the IAM user/role they belong to) don't have access or aren't intended to be used. More commonly, it happens when you provide credentials that are only valid for a specific STS endpoint, and your client is configured to hit a different region's endpoint. Though less direct, I've seen misconfigured regions lead to confusing authentication failures.

### System Clock Skew
AWS requests are cryptographically signed, and part of that signature often includes a timestamp. If your system's clock is significantly out of sync with AWS's servers (even by a few minutes), AWS might reject your request because the timestamp in the signature appears to be in the future or too far in the past. While less common with modern operating systems that synchronize time automatically, it's a subtle cause that can be tricky to diagnose if you're not aware of it.

### IAM User or Role Deleted/Deactivated
If the underlying IAM user or role to which the `AWS_ACCESS_KEY_ID` belongs has been deleted, deactivated, or its access keys have been rotated/deactivated in the AWS console, any attempts to use those older, now-invalid keys will result in this error. This often happens during security cleanups or user offboarding processes.

## Step-by-Step Fix

Troubleshooting `InvalidClientTokenId` requires a systematic approach. Here's how I typically go about resolving it:

1.  **Check Your Active Credentials (AWS CLI First)**
    Start by understanding what credentials your AWS CLI or SDK is currently configured to use.
    ```bash
    aws configure list
    ```
    Look at the `access_key`, `secret_key`, and `region` fields. Pay close attention to the `type` field; if it says `assume-role` or `sso`, you're using temporary credentials, which makes expiration a prime suspect.

2.  **Verify Environment Variables**
    Environment variables (like `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, and `AWS_DEFAULT_REGION`) take precedence over `~/.aws/credentials` and `~/.aws/config`. Check if any are set that might be overriding your intended configuration.
    ```bash
    printenv | grep AWS_
    ```
    If `AWS_SESSION_TOKEN` is present, you are definitely using temporary credentials. Its absence with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` usually means static credentials are in use.

3.  **Inspect `~/.aws/credentials` and `~/.aws/config`**
    Manually open these files and check for:
    *   Typos in `aws_access_key_id` or `aws_secret_access_key`.
    *   Extra spaces around the key values.
    *   The presence of `aws_session_token` if you expect temporary credentials.
    *   Correct `region` settings for your profiles.

    Example of `~/.aws/credentials`:
    ```ini
    [default]
    aws_access_key_id = AKIAIOSFODNN7EXAMPLE
    aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

    [my-temp-profile]
    aws_access_key_id = ASIAV4EXAMPLE2N2K4R32
    aws_secret_access_key = L62YEXAMPLEw4Q+hJ70dEAXPLezT95DPMU
    aws_session_token = IQoJb3JpZ2luX2VjEL...
    ```

4.  **Test with `aws sts get-caller-identity`**
    This is your best friend for credential validation. It attempts to resolve your identity without interacting with any other service.
    ```bash
    aws sts get-caller-identity
    ```
    If this command succeeds, your credentials are valid, and the problem likely lies with the specific service you were trying to access (e.g., region mismatch, service-specific IAM policy issues that *look* like an authentication error but aren't). If it fails with `InvalidClientTokenId`, your credentials are indeed the problem.

5.  **Refresh Temporary Credentials**
    If `aws sts get-caller-identity` points to an issue and `AWS_SESSION_TOKEN` was present (or `aws configure list` showed `type = assume-role`/`sso`), your temporary credentials have likely expired.
    *   If using AWS SSO: Run `aws sso login` again.
    *   If assuming a role: Re-run your `aws sts assume-role` command to generate fresh tokens.
    *   If using an EC2 instance profile: You usually don't need to do anything manually, as the instance profile mechanism handles refresh automatically. If you're seeing this error on EC2, it might indicate an issue with the instance role itself or metadata service access.

6.  **Validate Your System Clock**
    Ensure your system's time is accurate. On Linux, `timedatectl status` can show synchronization status. You might need to synchronize with NTP:
    ```bash
    sudo ntpdate pool.ntp.org # On older systems
    sudo systemctl restart systemd-timesyncd # On systemd-based systems
    ```

7.  **Review IAM Console**
    As a last resort, if all checks point to valid credentials but the issue persists, log into the AWS Management Console with your root account or another administrative user. Navigate to IAM, find the user or role corresponding to the `AWS_ACCESS_KEY_ID` you're using, and verify:
    *   The user/role exists and is active.
    *   The access keys you are using are active and not deactivated. You might need to generate new keys if the old ones are compromised or simply not working.

## Code Examples

Here are some concise examples to help you troubleshoot and correctly configure your environment.

### Listing AWS CLI Configuration
```bash
aws configure list
# Example output for a default profile:
#       Name                    Value             Type    Location
#       ----                    -----             ----    --------
#    profile                <not set>             None    None
# access_key     ****************ABCD shared-credentials-file
# secret_key     ****************WXYZ shared-credentials-file
#     region                us-east-1      config-file    ~/.aws/config
```

### Checking Caller Identity
This command directly uses your current AWS configuration to verify credentials.
```bash
aws sts get-caller-identity
# Example success output:
# {
#     "UserId": "AIDACKCEVSQ6CEXAMPLE:my-cli-session",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/my-cli-user"
# }
# If using an assumed role:
# {
#     "UserId": "AROARWEXAMPLEM2R7X47:my-assumed-role-session",
#     "Account": "123456789012",
#     "Arn": "arn:aws:sts::123456789012:assumed-role/MyRole/my-assumed-role-session"
# }
```

### Setting Environment Variables
This is a common way to temporarily override credentials, useful for testing or in CI/CD pipelines.
```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEL..." # Only if using temporary credentials
export AWS_DEFAULT_REGION="us-west-2"
```

### Python Boto3 Example
When using an AWS SDK like Boto3, the SDK automatically looks for credentials in a specific order (environment variables, `~/.aws/credentials`, EC2 instance profiles).
```python
import boto3
from botocore.exceptions import ClientError

try:
    # This will use credentials configured via CLI, env vars, or instance profile
    s3_client = boto3.client('s3', region_name='us-east-1')
    response = s3_client.list_buckets()
    print("Successfully listed buckets:")
    for bucket in response['Buckets']:
        print(f"  {bucket['Name']}")
except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidClientTokenId':
        print(f"ERROR: InvalidClientTokenId encountered. Your AWS credentials are invalid or expired.")
        print(f"Details: {e}")
    else:
        print(f"An unexpected AWS error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# You can also explicitly pass credentials, though generally not recommended
# s3_client = boto3.client(
#     's3',
#     aws_access_key_id='YOUR_ACCESS_KEY',
#     aws_secret_access_key='YOUR_SECRET_KEY',
#     aws_session_token='YOUR_SESSION_TOKEN', # Optional for temporary credentials
#     region_name='us-east-1'
# )
```

## Environment-Specific Notes

The context in which you encounter `InvalidClientTokenId` can significantly influence the troubleshooting steps.

### Local Development
On your local machine, the AWS CLI and SDKs primarily source credentials from:
1.  **Environment Variables**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`. These take highest precedence. Check your shell's profile (e.g., `.bashrc`, `.zshrc`) or current session.
2.  **`~/.aws/credentials` file**: This is where `aws configure` stores static credentials or profiles.
3.  **`~/.aws/config` file**: Used for region, output format, and profile definitions, including `source_profile` for chained credentials or `sso_start_url` for AWS SSO.
When troubleshooting locally, always check these sources in order. If you're using AWS SSO, ensure your SSO session hasn't expired (`aws sso login`).

### Docker Containers
Running AWS commands within a Docker container adds another layer. Credentials can be passed in a few ways:
1.  **Environment Variables**: The most common and often cleanest method.
    ```bash
    docker run -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
               -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
               -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
               -e AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
               my_aws_cli_image aws s3 ls
    ```
2.  **Mounting `~/.aws` volume**: You can mount your host's `.aws` directory into the container.
    ```bash
    docker run -v ~/.aws:/root/.aws:ro my_aws_cli_image aws s3 ls --profile my-profile
    ```
    Be cautious with this method, especially in production, as it can expose credentials. Ensure correct user permissions within the container for the mounted volume.
3.  **IAM Roles (for containers running on EC2/ECS/EKS)**: The most secure approach. The container inherits the IAM role attached to the underlying EC2 instance (for ECS EC2 launch type) or the task definition (for ECS Fargate, EKS pod roles). If `InvalidClientTokenId` appears here, it usually means:
    *   No IAM role is assigned to the task/pod/instance.
    *   The IAM role exists but is misconfigured or has been deleted.
    *   The container cannot reach the EC2 instance metadata service (IMDS) to retrieve temporary credentials, possibly due to network configuration or a proxy.

### Cloud Environments (EC2, ECS, Lambda, EKS)
In cloud compute environments, the primary and recommended method for providing AWS credentials is via **IAM Roles**.
*   **EC2 Instances**: An instance profile with an IAM role is attached to the EC2 instance. The AWS SDKs and CLI automatically retrieve temporary credentials from the instance metadata service (IMDS). If you see `InvalidClientTokenId` on EC2, check that an instance role *is* attached and has not been removed or misconfigured.
*   **AWS Lambda Functions**: Each Lambda function is assigned an execution role. This error would be highly unusual directly from Lambda's execution, as the service manages the role's credentials. If it occurs, it points to a misconfiguration of the Lambda function's IAM role itself, or code within the Lambda is *attempting* to use hardcoded or external credentials that are failing, rather than its execution role.
*   **ECS Tasks / EKS Pods**: These also leverage IAM roles, either via task execution roles for ECS or IAM Roles for Service Accounts (IRSA) for EKS. Similar to EC2, verify the correct role is associated and accessible. For EKS, ensure the IRSA configuration (Service Account, annotation, OIDC provider) is correct.

## Frequently Asked Questions

**Q: Is `InvalidClientTokenId` a permissions error?**
**A:** No, it is an *authentication* error, not a permissions (authorization) error. It means AWS couldn't verify *who* you are, regardless of *what* permissions you might have. A permissions error would typically be `AccessDeniedException`.

**Q: How can I tell if my AWS credentials are temporary?**
**A:** Temporary credentials always include an `AWS_SESSION_TOKEN` in addition to the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. If you see this token in your environment variables or `~/.aws/credentials` file, your credentials are temporary and will expire.

**Q: Can a firewall or proxy cause this error?**
**A:** Indirectly. If a firewall or proxy prevents your application or CLI from reaching the AWS Security Token Service (STS) endpoint (e.g., `sts.amazonaws.com` or a region-specific STS endpoint) to *obtain* or *refresh* temporary credentials, then subsequent attempts to use expired tokens would result in `InvalidClientTokenId`. However, the error itself isn't a direct network connectivity problem to the target service but an authentication failure.

**Q: What's the best way to prevent this error?**
**A:** For applications and services running on AWS (EC2, ECS, Lambda, EKS), always use IAM roles for credentials. This eliminates managing keys manually and handles credential rotation automatically. For human users, leverage AWS SSO (Single Sign-On) for managed temporary credentials. Avoid storing static `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` directly in code or long-lived environment variables.

**Q: Does Multi-Factor Authentication (MFA) play a role here?**
**A:** MFA is typically required to *obtain* temporary credentials (e.g., when logging in via SSO or using `aws sts get-session-token`). If you fail the MFA step, you won't get the credentials in the first place. Once you have the temporary credentials, the `InvalidClientTokenId` error would mean those *obtained* credentials have expired or are malformed, not that MFA itself is failing.

## Related Errors
*(None)*