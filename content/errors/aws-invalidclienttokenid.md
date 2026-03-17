# AWS InvalidClientTokenId: The security token is invalid
> Encountering AWS InvalidClientTokenId means your AWS credentials are malformed, expired, or incorrect for the region; this guide explains how to identify and fix the underlying issue.

## What This Error Means

When you encounter the `InvalidClientTokenId: The security token is invalid` error, it signifies a fundamental authentication failure with AWS. This isn't an issue of permissions (authorization), but rather a problem with how you're presenting your identity (authentication) to AWS. Essentially, AWS received your access key ID and potentially a secret access key or session token, but it couldn't validate them against its records.

Think of it like trying to open a locked door with a key that's either the wrong shape, bent, broken, or from a completely different lock. The door recognizes you're trying to use a key, but it simply doesn't fit. In AWS terms, the `ClientTokenId` refers to your `AWS_ACCESS_KEY_ID`. When it's invalid, AWS can't identify who you are or verify the authenticity of your request. This error will stop your CLI commands, SDK calls, or API requests dead in their tracks before any action can even be considered.

## Why It Happens

This error occurs because the credentials provided to AWS through your CLI, SDK, or application simply aren't recognized as valid. AWS processes your request, extracts the `AWS_ACCESS_KEY_ID`, and attempts to match it with a known, active access key within the specified AWS region. If it fails this initial identification step, you get `InvalidClientTokenId`.

In my experience, this usually points to one of a few core problems: the access key ID itself is incorrect, it has expired (for temporary credentials), it's associated with a different AWS account or region, or it's simply inactive. It's a clear signal that the initial handshake failed, indicating a configuration issue rather than a runtime problem with the service you're trying to access.

## Common Causes

Debugging `InvalidClientTokenId` often boils down to systematically checking credential sources. Here are the most common culprits I've encountered:

1.  **Expired Temporary Credentials:** This is, by far, the most frequent cause. If you're using temporary credentials obtained via `aws sts assume-role`, `get-session-token`, or from an instance profile on an EC2 instance, these credentials have a limited lifespan. Once they expire, any subsequent API calls using them will result in `InvalidClientTokenId`.
2.  **Typo or Incorrect `AWS_ACCESS_KEY_ID`:** A simple copy-paste error or a manual typo in your `AWS_ACCESS_KEY_ID` is enough to trigger this. Even a single character difference makes the token invalid.
3.  **Deactivated or Deleted IAM User/Access Key:** If the IAM user associated with the access key has been deleted, or if the specific access key you're using has been deactivated or deleted from the IAM console, it will no longer be valid.
4.  **Region Mismatch:** While less common for the *token ID itself* (which is global), credentials might be generated or expected in a specific region, and if your CLI/SDK is attempting to use them in a different region, this can sometimes lead to issues. More often, this is a symptom of using *expired* temporary credentials that were valid for a specific region.
5.  **Incorrect AWS Profile Configuration:** If you're using named profiles in `~/.aws/credentials` or `~/.aws/config`, and the `profile` argument or `AWS_PROFILE` environment variable points to a non-existent or malformed profile, AWS won't be able to load valid credentials.
6.  **Environment Variable Override:** Sometimes, valid credentials exist in your `~/.aws/credentials` file, but old, incorrect, or expired `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, or `AWS_SESSION_TOKEN` environment variables are set in your shell session, overriding the correct ones.
7.  **Clock Skew (Rare):** Extremely significant clock differences between your client machine and AWS servers can occasionally interfere with the signature validation process for temporary credentials, though modern systems usually handle time synchronization robustly.

## Step-by-Step Fix

Addressing this error requires a methodical approach to checking your credential chain.

1.  **Identify the Credential Source:**
    *   Are you using environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)?
    *   Are you using a shared credentials file (`~/.aws/credentials`) and a profile (`--profile default` or `export AWS_PROFILE=myprofile`)?
    *   Are you relying on an IAM role attached to an EC2 instance, ECS task, or Lambda function?
    *   Are you assuming a role using `aws sts assume-role` and setting temporary credentials?

    Knowing *how* your credentials are being picked up is half the battle. AWS CLI and SDKs follow a specific order of precedence: Environment variables > Shared credentials file > IAM roles for EC2/ECS/Lambda.

2.  **Check Environment Variables First:**
    Run the following commands to inspect your current environment:

    ```bash
    echo $AWS_ACCESS_KEY_ID
    echo $AWS_SECRET_ACCESS_KEY
    echo $AWS_SESSION_TOKEN
    echo $AWS_DEFAULT_REGION
    ```

    *   **Problem:** If any of these are set, especially `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, and they are incorrect or empty, they will override any other configuration.
    *   **Fix:** Unset them if they're wrong or expired, and then retry.
        ```bash
        unset AWS_ACCESS_KEY_ID
        unset AWS_SECRET_ACCESS_KEY
        unset AWS_SESSION_TOKEN
        # Also consider unsetting AWS_DEFAULT_REGION if you suspect a region issue
        # unset AWS_DEFAULT_REGION
        ```

3.  **Verify Shared Credentials and Config Files:**
    Examine `~/.aws/credentials` and `~/.aws/config`.

    *   Open `~/.aws/credentials` and confirm the `aws_access_key_id` under your active profile (e.g., `[default]` or `[myprofile]`) is correct and hasn't been accidentally modified. Check for leading/trailing spaces or typos.
    *   Open `~/.aws/config` and ensure your profile's `region` is set correctly. While less direct for `InvalidClientTokenId`, an incorrect region can sometimes lead to follow-on issues if temporary tokens are region-bound.

4.  **Test Your Current Identity:**
    Try to fetch your current identity. If your credentials are truly invalid, this command will also fail with the same error, but it's a good sanity check.

    ```bash
    aws sts get-caller-identity
    ```
    If this fails, your AWS credentials are not valid in the context you're running this command.

5.  **Re-Assume Roles for Temporary Credentials:**
    If you're using temporary credentials from an `assume-role` operation, they *will* expire. The solution is to re-assume the role.

    ```bash
    # Example command to assume a role
    aws sts assume-role --role-arn arn:aws:iam::123456789012:role/MyTempRole --role-session-name MySession

    # The output will contain new temporary credentials.
    # You'll need to export these into your environment or configure your CLI/SDK to use them.
    # For example, using `jq` to parse and export:
    # eval $(aws sts assume-role --role-arn arn:aws:iam::123456789012:role/MyTempRole --role-session-name MySession | \
    #   jq -r '.Credentials | "export AWS_ACCESS_KEY_ID=\(.AccessKeyId)\nexport AWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)\nexport AWS_SESSION_TOKEN=\(.SessionToken)\nexport AWS_SESSION_EXPIRATION=\(.Expiration)"')
    ```

6.  **Generate New Access Keys (Last Resort):**
    If you've exhausted all other options and suspect your access key has been deactivated, deleted, or you just can't track down the issue, consider generating a new access key for your IAM user in the AWS IAM console.
    *   Go to IAM -> Users -> [Your User] -> Security Credentials tab.
    *   Deactivate the old key and create a new one. Update your `~/.aws/credentials` file or environment variables with the new key ID and secret. **Remember to never hardcode keys in code.**

7.  **Explicitly Set Region:**
    If you're still having issues, ensure your region is explicitly set and correct.

    ```bash
    export AWS_DEFAULT_REGION="us-east-1" # Or your desired region
    # Or for a specific command:
    aws s3 ls --region us-east-1
    ```

## Code Examples

Here are some concise, copy-paste ready examples for common scenarios:

**1. Verifying and Clearing Environment Variables (Bash):**

```bash
# Check existing credentials
echo "AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID"
echo "AWS_SECRET_ACCESS_KEY: (present if not empty)"
echo "AWS_SESSION_TOKEN: $AWS_SESSION_TOKEN"
echo "AWS_DEFAULT_REGION: $AWS_DEFAULT_REGION"

# Clear potentially problematic environment variables
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
unset AWS_DEFAULT_REGION
unset AWS_PROFILE # Useful if you want to fall back to default profile
```

**2. Configuring AWS CLI (for persistent credentials):**

```bash
# Run this to set up your default profile interactively
aws configure

# Or for a named profile
aws configure --profile mydevprofile

# Example content for ~/.aws/credentials:
# [default]
# aws_access_key_id = AKIAIOSFODNN7EXAMPLE
# aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Example content for ~/.aws/config:
# [default]
# region = us-east-1
# output = json
#
# [profile mydevprofile]
# region = us-west-2
# output = json
```

**3. Python Boto3 Example (demonstrating credential usage order):**

```python
import os
import boto3
from botocore.exceptions import ClientError

# --- Scenario 1: Relying on default credential chain (env vars, ~/.aws/credentials) ---
# This is the most common and recommended approach
try:
    s3_client_default = boto3.client('s3')
    print("Attempting to list S3 buckets using default credentials:")
    response = s3_client_default.list_buckets()
    for bucket in response['Buckets']:
        print(f"  - {bucket['Name']}")
except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidClientTokenId':
        print(f"Error (Default): InvalidClientTokenId. Check your environment variables or ~/.aws/credentials.")
    else:
        print(f"Error (Default): {e}")

# --- Scenario 2: Explicitly providing credentials (less common, usually for specific cases) ---
# Note: Hardcoding credentials is generally NOT recommended for production.
# This example is for demonstration of how explicit credentials are used.
# Let's use intentionally wrong credentials to demonstrate the error.
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIMINTENTIONALLYINVALID' # Mismatched or non-existent
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fake_secret_key_that_is_also_wrong_for_this_example'

try:
    s3_client_explicit = boto3.client('s3', region_name='us-east-1')
    print("\nAttempting to list S3 buckets using explicit (and likely invalid) environment variables:")
    response = s3_client_explicit.list_buckets()
    for bucket in response['Buckets']:
        print(f"  - {bucket['Name']}")
except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidClientTokenId':
        print(f"Error (Explicit): InvalidClientTokenId. The provided credentials are bad.")
    else:
        print(f"Error (Explicit): {e}")

# Clean up environment variables if they were set for this example
del os.environ['AWS_ACCESS_KEY_ID']
del os.environ['AWS_SECRET_ACCESS_KEY']
```

## Environment-Specific Notes

The source and handling of AWS credentials vary significantly by environment, which directly impacts how you'll debug `InvalidClientTokenId`.

### Local Development

This is where `InvalidClientTokenId` is most common.
*   **Credential Files:** You're typically using `~/.aws/credentials` and `~/.aws/config`. Ensure the correct profile is active, either by `export AWS_PROFILE=mydevprofile` or by passing `--profile mydevprofile` to `aws` commands.
*   **Environment Variables:** It's very easy to accidentally set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your shell, or via a `.env` file, and forget about them. These take precedence and can mask correct configurations elsewhere.
*   **Temporary Sessions:** If you `assume-role` frequently, ensure your script or workflow correctly refreshes and exports the new temporary credentials each time they expire. I've often seen this when developers leave a terminal open for too long after assuming a role.

### Cloud Environments (EC2, ECS, Lambda)

In these environments, the preferred method for authentication is **IAM roles for service accounts/instances**. If you get `InvalidClientTokenId` here, it usually means:
*   **Explicit Credentials are Being Used:** Your application or a script is *explicitly* trying to use hardcoded credentials or environment variables that are incorrect or expired, *even though* an IAM role is attached. The application isn't falling back to the instance profile or task role because it found explicit credentials first.
*   **Role Not Attached/Configured:** Less common for `InvalidClientTokenId` (more likely `AccessDenied` or a network error), but if the instance profile/task role isn't correctly associated, the SDK might then search for other credentials and fail if none are found, *or* if it *does* find old, invalid explicit credentials.
*   **Temporary Credentials from Role Assumption Expired:** If your application assumes another role *from* an EC2 instance, the temporary credentials obtained from that assumption will expire. The application needs to be designed to refresh these.

### Docker Containers

Docker adds another layer of isolation.
*   **Mounting `~/.aws`:** You can mount your local `~/.aws` directory into the container. Ensure the permissions are correct and the default profile or the specified profile is valid.
    ```bash
    docker run -v ~/.aws:/root/.aws:ro my-aws-app
    ```
*   **Environment Variables:** Passing credentials via environment variables is common:
    ```bash
    docker run \
      -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
      -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
      -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
      my-aws-app
    ```
    The key here is ensuring the *host's* environment variables are correctly populated *before* the `docker run` command executes.
*   **IAM Roles for Container Orchestrators:** If running on ECS, EKS, or other platforms, you should leverage IAM roles for tasks/pods. This abstracts credential management away from the container image itself.

## Frequently Asked Questions

**Q: Is `InvalidClientTokenId` a permissions error?**
**A:** No, it is not. This error means AWS could not *authenticate* you (identify who you are) because the security token (your access key ID) was invalid. A permissions error (`AccessDenied`) occurs *after* successful authentication, when AWS determines you don't have the necessary rights to perform the requested action.

**Q: Why does this error appear intermittently?**
**A:** Intermittent `InvalidClientTokenId` errors almost always point to the use of temporary credentials (e.g., from `aws sts assume-role` or an instance profile) that are expiring. Your application or script might work immediately after refreshing credentials, but fail a few hours later when they time out. Another common cause is different execution environments loading different sets of credentials (e.g., your IDE uses one, your terminal uses another).

**Q: Can a network issue cause `InvalidClientTokenId`?**
**A:** Generally, no. A network issue (like a firewall block or DNS problem) would typically result in a connection timeout or a "host unreachable" error. `InvalidClientTokenId` specifically means that your request *reached* AWS, and AWS processed the authentication header but found the token invalid.

**Q: I'm sure my keys are correct in `~/.aws/credentials`. What else could it be?**
**A:** Check environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) as they take precedence. Also, ensure you're using the correct profile (`--profile myprofile` or `AWS_PROFILE`) and that the `AWS_ACCESS_KEY_ID` for that profile is indeed valid and active in the IAM console. Finally, if you're using temporary credentials from an assumed role, they might have simply expired.

**Q: Does the region affect `InvalidClientTokenId`?**
**A:** The `AWS_ACCESS_KEY_ID` itself is a global identifier, so it's not strictly region-dependent for basic identification. However, the *context* in which it's used (especially for temporary credentials or certain service endpoints) can lead to issues. An incorrectly set `AWS_DEFAULT_REGION` or explicit `--region` might cause a service-specific issue or prevent the correct credential provider chain from functioning, sometimes surfacing as `InvalidClientTokenId` if the underlying token is tied to a specific region or if the SDK can't correctly locate a regional STS endpoint. It's good practice to ensure your region is correctly configured.

## Related Errors