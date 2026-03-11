# AWS AccessDeniedException: User is not authorized
> Encountering `AWS AccessDeniedException` means your IAM entity lacks necessary permissions; this guide explains how to identify and fix it.

## What This Error Means

When you encounter an `AWS AccessDeniedException: User is not authorized` error, it signifies that the AWS Identity and Access Management (IAM) principal (whether it's an IAM user, an IAM role, or a federated user assuming a role) attempting to perform an action does not have the necessary permissions to do so. AWS's security model is based on explicit allow. If there isn't a policy statement explicitly allowing an action on a resource, access is implicitly denied. This error is AWS's way of telling you that your request was blocked at the authorization layer.

It’s crucial to understand that this isn't a network issue or a service availability problem. It's a precise rejection based on the permissions assigned to the identity making the call. The "User" in the error message is a generic term; it refers to the IAM principal, which could be an IAM user, an EC2 instance profile, a Lambda function's execution role, or any other identity.

## Why It Happens

The `AccessDeniedException` occurs because the AWS policy evaluation engine has determined that the requesting principal is not permitted to perform the requested action on the specified resource. AWS evaluates all applicable policies to make this decision. This includes identity-based policies (attached to users, groups, or roles), resource-based policies (attached to S3 buckets, SQS queues, KMS keys, etc.), Permissions Boundaries, and Service Control Policies (SCPs) if you're in an AWS Organization.

The core principle is: **everything is denied by default.** An action is only permitted if there is an explicit `Allow` statement in an applicable policy that matches the action, resource, and principal. If there's an explicit `Deny` statement anywhere in the policy evaluation path that matches, it always overrides any `Allow` statement.

In my experience, this error is often a result of either an overly restrictive policy, an incorrectly targeted policy, or simply a missing permission that seemed obvious but wasn't explicitly granted.

## Common Causes

Identifying the root cause of an `AccessDeniedException` can sometimes feel like detective work. Here are the most common scenarios I've encountered:

1.  **Missing or Incorrect IAM Policy:** This is the most frequent cause. The IAM user or role simply doesn't have an `Allow` statement for the specific action (e.g., `s3:GetObject`) on the target resource (e.g., `arn:aws:s3:::my-bucket/*`). Often, it's a small typo in the action name or resource ARN.
2.  **Resource-Based Policy Restrictions:** Many AWS services (S3, SQS, KMS, Secrets Manager, etc.) allow you to attach policies directly to the resource. If your IAM principal's identity-based policy allows an action, but the resource-based policy explicitly denies it or doesn't allow it, access will be denied. I've spent hours debugging S3 access only to find a bucket policy that implicitly or explicitly blocked cross-account access.
3.  **Permissions Boundaries:** If a Permissions Boundary is set on an IAM user or role, it limits the *maximum* permissions that identity can ever have, even if other attached policies try to grant broader access. The effective permissions are the intersection of the identity-based policies and the permissions boundary.
4.  **Service Control Policies (SCPs) in AWS Organizations:** In multi-account environments managed by AWS Organizations, SCPs can apply `Deny` rules at the Organization Unit (OU) or account level. An SCP's `Deny` takes precedence over any `Allow` in an IAM policy within the account. This is a common pitfall in enterprise settings.
5.  **Temporary Credentials Expiration:** If you're using temporary credentials (e.g., from AWS STS, assumed roles, or `aws configure sso`), they have a limited lifespan. If they expire, you'll receive an `AccessDenied` or similar error because your session is no longer valid.
6.  **Incorrect Principal:** Sometimes, the code or CLI command is being executed by a different IAM principal than you expect. This can happen with instance profiles on EC2, or when local AWS profiles aren't correctly configured or selected.
7.  **Multi-Factor Authentication (MFA) Requirement:** A policy might include a condition requiring MFA for sensitive actions. If MFA is not used when calling the API, access is denied.
8.  **Implicit Deny vs. Explicit Deny:** An implicit deny happens when there's no `Allow` for an action. An explicit deny (a `Deny` statement in *any* applicable policy) always overrides an `Allow`. An explicit deny can be tricky because it can come from an SCP, a permissions boundary, or even a different policy on the same principal or resource.

## Step-by-Step Fix

Fixing an `AccessDeniedException` involves a systematic investigation.

1.  **Identify the Failing Action and Resource:**
    The error message itself, or the stack trace from your SDK, usually gives hints. Look for what specific AWS API call failed (e.g., `s3:GetObject`, `ec2:RunInstances`, `dynamodb:PutItem`) and on which resource (e.g., `arn:aws:s3:::my-bucket/my-object`, `arn:aws:dynamodb:REGION:ACCOUNT:table/my-table`). This is your most important clue.

2.  **Determine the IAM Principal:**
    Confirm which IAM user or role is making the failing request.
    *   **CLI:** Check `aws configure list-profiles` or the `AWS_PROFILE` environment variable.
    *   **SDK:** Look at how credentials are being loaded (environment variables, shared credentials file, IAM role for EC2/ECS/Lambda).
    *   **CloudTrail:** This is the definitive source. See step 3.

3.  **Consult AWS CloudTrail:**
    CloudTrail is your best friend here. It logs every API call made in your AWS account.
    *   Navigate to the CloudTrail console.
    *   Go to "Event history".
    *   Filter by "Event name" (the failing action, e.g., `GetObject`) or "User name" (the IAM principal).
    *   Look for events with `errorMessage` containing "Access Denied" or `errorCode` of `AccessDenied`.
    *   The CloudTrail event will explicitly state the `userIdentity` (who made the call), `eventSource` (which service), `eventName` (which API call), and `responseElements.errorMessage` which often provides more detail than the initial exception. Critically, it will often tell you *which* explicit `Deny` statement was hit, or which `Allow` statement was missing if an explicit `Deny` wasn't present.

    ```bash
    # Example CloudTrail lookup (via CLI, requires CloudTrail permissions)
    aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=GetObject --max-results 5 --query 'Events[*].CloudTrailEvent'
    ```

4.  **Review IAM Policies Attached to the Principal:**
    *   Go to the IAM console -> Users or Roles.
    *   Find the principal identified in step 2.
    *   Examine all attached policies (managed, inline) and group policies.
    *   Look for a missing `Allow` statement for the action and resource identified in step 1.
    *   Check for any `Deny` statements that might be overriding a seemingly correct `Allow`.
    *   Pay attention to `Condition` blocks, which can further restrict when a policy applies. For example, a policy might only allow access if the request comes from a specific IP address.

5.  **Check Resource-Based Policies (if applicable):**
    For services like S3, SQS, KMS, etc., examine the resource's policy directly.
    *   **S3:** Go to the S3 console, select the bucket, then "Permissions" -> "Bucket policy".
    *   **SQS:** Go to the SQS console, select the queue, then "Access policy".
    *   **KMS:** Go to the KMS console, select the key, then "Key policy".
    Again, look for `Deny` statements or missing `Allow` statements that should grant access to your principal.

6.  **Evaluate Permissions Boundaries and SCPs:**
    *   **Permissions Boundaries:** If the principal has a Permissions Boundary, its effective permissions are the intersection of the identity policies and the boundary. Check the boundary policy in IAM.
    *   **SCPs:** If you're in an AWS Organization, check with your Organization administrator to see if any SCPs are applied to your account or OU that could be denying the action. These are harder to self-diagnose without Organization-level permissions.

7.  **Use the IAM Policy Simulator:**
    The IAM Policy Simulator is an invaluable tool.
    *   Go to IAM console -> "Policy simulator".
    *   Select the IAM user or role.
    *   Choose the service and specific action (e.g., `s3`, `GetObject`).
    *   Provide the target resource ARN.
    *   Run the simulation. It will tell you whether the action is allowed or denied and, critically, *which policy statement* caused the outcome. This can pinpoint exactly where the problem lies.

    ```bash
    # Example AWS CLI command for policy simulation
    aws iam simulate-principal-policy \
      --policy-source-arn arn:aws:iam::ACCOUNT_ID:user/MyUser \
      --action-names s3:GetObject \
      --resource-arns arn:aws:s3:::my-bucket/my-object
    ```

8.  **Adjust Policies and Re-test:**
    Once you've identified the missing `Allow` or the problematic `Deny`, modify the relevant policy.
    *   **Principle of Least Privilege:** Always grant only the necessary permissions. Start with minimal permissions and expand only if needed, rather than granting `*`.
    *   **Test meticulously.** If you're modifying policies, test in a non-production environment first.

## Code Examples

Here are some concise examples demonstrating how you might encounter or address `AccessDeniedException` using the AWS CLI and Python SDK.

### AWS CLI (Simulating a Policy Change)

After identifying a missing permission, you'd typically modify a policy. Here's a conceptual example of using the CLI to attach a policy.

```bash
# 1. Create a policy file (e.g., my-s3-read-policy.json)
cat <<EOF > my-s3-read-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-data-bucket",
                "arn:aws:s3:::my-data-bucket/*"
            ]
        }
    ]
}
EOF

# 2. Create the IAM policy
aws iam create-policy \
    --policy-name MyS3ReadAccessPolicy \
    --policy-document file://my-s3-read-policy.json

# 3. Get the ARN of the created policy
POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='MyS3ReadAccessPolicy'].Arn" --output text)

# 4. Attach the policy to an IAM user or role (e.g., 'MyCLIUser')
aws iam attach-user-policy \
    --user-name MyCLIUser \
    --policy-arn $POLICY_ARN

# Or to a role (e.g., 'MyEC2Role')
# aws iam attach-role-policy \
#     --role-name MyEC2Role \
#     --policy-arn $POLICY_ARN

# After attaching, try the action again
# aws s3 ls s3://my-data-bucket/
```

### Python Boto3 SDK (Handling the Exception)

This example shows how to perform an S3 operation and catch the `AccessDeniedException`.

```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
bucket_name = 'my-inaccessible-bucket-12345'
object_key = 'test-file.txt'

try:
    # Attempt to list objects in a bucket
    s3.list_objects_v2(Bucket=bucket_name)
    print(f"Successfully listed objects in {bucket_name}")

    # Attempt to get an object
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    print(f"Successfully retrieved {object_key} from {bucket_name}")
    print(response['Body'].read().decode('utf-8'))

except ClientError as e:
    if e.response['Error']['Code'] == 'AccessDenied':
        print(f"ERROR: Access Denied to bucket '{bucket_name}'.")
        print("Please check IAM permissions for the current principal.")
        print(f"Details: {e}")
    elif e.response['Error']['Code'] == 'NoSuchBucket':
        print(f"ERROR: Bucket '{bucket_name}' does not exist.")
    else:
        print(f"An unexpected error occurred: {e}")
except Exception as e:
    print(f"A general error occurred: {e}")

```

## Environment-Specific Notes

The context in which you encounter `AccessDeniedException` can influence your troubleshooting approach.

*   **Cloud (EC2, Lambda, ECS/EKS):** In these environments, your application assumes an IAM role (via an EC2 instance profile, Lambda execution role, or ECS/EKS task role). The principal identity is the assumed role. Troubleshooting here focuses on the permissions attached to *that role*. Use the CloudTrail events to confirm the role ARN. I've often seen folks forget to update a role's policy after deploying new functionality to a Lambda, leading to runtime `AccessDenied` errors.
*   **Docker Containers:** If your Docker container is running on an EC2 instance, it inherits the instance's IAM role. If it's running locally, it relies on credentials passed via environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) or mounted `~/.aws/credentials` files. Ensure the correct credentials are being exposed to the container. A common mistake is using local developer credentials with full access, then deploying to Docker/EC2 where a more restricted role is in place.
*   **Local Development:** Locally, you're typically using credentials from your `~/.aws/credentials` file, environment variables, or through SSO configuration. The `AWS_PROFILE` environment variable or `--profile` CLI flag determines which credential set is used. Always double-check which profile is active. Sometimes, a temporary credential from an `aws sso login` session might expire, leading to `AccessDenied`, even if the underlying role has the correct permissions. Just re-login to SSO.

## Frequently Asked Questions

**Q: Why does it say "User is not authorized" when I'm using a Role?**
**A:** The term "User" in the `AccessDeniedException` is a general term for any IAM principal. It applies equally to IAM users, assumed roles, federated identities, and even service-linked roles. The underlying issue is that the identity attempting the action lacks permissions, regardless of its type.

**Q: I updated the policy, but I'm still getting AccessDenied. What gives?**
**A:** IAM policy propagation can take a few seconds, sometimes up to a minute or two, across AWS's distributed system. Wait a short period and try again. If it still fails, double-check that you updated the *correct* policy on the *correct* principal, and that there isn't an explicit `Deny` elsewhere (like an SCP or permissions boundary) that is overriding your `Allow`. CloudTrail and the Policy Simulator are your best tools here.

**Q: Can a resource policy override an IAM user/role policy?**
**A:** Yes, in some cases. Resource policies (like S3 bucket policies or KMS key policies) are evaluated *in addition to* identity-based policies. If a resource policy has an explicit `Deny` statement for your principal, it will override any `Allow` from your identity-based policy. Conversely, if your identity-based policy has no `Allow` but the resource policy explicitly grants access, it might work (depending on the service, e.g., S3). The policy evaluation logic is complex, so always consult the official AWS documentation if unsure.

**Q: How can I prevent this error in my CI/CD pipeline?**
**A:** The best practice is to adhere strictly to the principle of least privilege. Implement automated IAM policy validation checks as part of your CI/CD. Use tools like `iam-policy-validator` or `cfn-guard` to ensure your CloudFormation/Terraform IAM definitions are correct and don't grant excessive permissions. Regularly audit your roles and permissions. I've seen pipelines fail repeatedly because new deployments introduce new resource types without corresponding IAM permission updates.

## Related Errors

- [linux-permission-denied](/errors/linux-permission-denied.html)