# AWS AccessDeniedException: User is not authorized
> Encountering AWS AccessDeniedException means your IAM user or role lacks the required permissions for the requested action; this guide explains how to fix it.

## What This Error Means

The `AWS AccessDeniedException: User is not authorized` error is one of the most fundamental and common issues you'll encounter when interacting with AWS. At its core, it signifies that the identity attempting to perform an action – whether it's an IAM user, an assumed IAM role, or a federated identity – does not have the necessary permissions explicitly granted to complete the requested operation on the specified resource. AWS operates on an explicit deny model, meaning that unless an action is explicitly *allowed*, it is implicitly *denied*. This error is AWS's way of enforcing its security posture, preventing unauthorized access to your resources.

## Why It Happens

AWS security is built on the principle of least privilege, where identities are granted only the minimum permissions required to perform their tasks. This error typically occurs because the identity's permissions model does not align with the action it is attempting. There are several layers where permissions are evaluated, and a `Deny` at any layer will result in this error. Understanding these layers is key to effective troubleshooting.

The permission evaluation logic in AWS is comprehensive. When an identity makes a request, AWS checks all applicable policies to determine if the action is allowed. These policies can include:

*   **Identity-based policies:** Attached directly to an IAM user, group, or role.
*   **Resource-based policies:** Attached to a resource itself (e.g., S3 bucket policies, SQS queue policies, KMS key policies).
*   **Session policies:** Temporary inline policies passed when assuming a role or federating.
*   **Permission boundaries:** Set on an IAM user or role to define the maximum permissions that identity can ever have.
*   **Service Control Policies (SCPs):** Applied at the AWS Organizations level, they define the maximum permissions for accounts within an Organization.
*   **VPC Endpoint policies:** Control access to AWS services via a VPC endpoint.

If any policy explicitly denies an action, or if no policy explicitly allows it, you'll encounter `AccessDeniedException`.

## Common Causes

In my experience, encountering this error usually boils down to a few frequent scenarios:

1.  **Missing IAM Policy or Incorrect Policy Actions:** This is by far the most common cause. The IAM user or role simply lacks an `Allow` statement for the specific action (e.g., `s3:GetObject`, `ec2:DescribeInstances`, `lambda:InvokeFunction`) they are trying to perform. Often, a policy might be attached, but it's too restrictive (e.g., allows `s3:ListBucket` but not `s3:GetObject`).
2.  **Incorrect Resource ARN in Policy:** Even with the correct action, the `Resource` ARN specified in the IAM policy might be wrong, too narrow, or missing altogether. For instance, allowing `s3:GetObject` on `arn:aws:s3:::my-bucket/*` but trying to access a bucket named `my-other-bucket`.
3.  **Explicit Deny Statement:** An explicit `Deny` statement in *any* policy (identity, resource, SCP, permission boundary) will always override an `Allow` statement. I've seen this in production when an SCP was silently blocking an action that was otherwise allowed by an IAM role.
4.  **Role Trust Policy Issues:** When trying to assume an IAM role (e.g., using `sts:AssumeRole`), the role's trust policy must explicitly allow the requesting principal (user or other role) to assume it. If this trust policy is misconfigured, you'll get an `AccessDeniedException` when trying to assume the role.
5.  **MFA Requirement Not Met:** If a policy has a condition requiring Multi-Factor Authentication (MFA) to be present, and the request is made without MFA, an `AccessDeniedException` will occur.
6.  **Permission Boundary Restrictions:** A permission boundary attached to an IAM user or role can limit the maximum permissions that identity can have, even if an attached identity policy attempts to grant broader access. The effective permissions are the intersection of the identity policy and the permission boundary.
7.  **Service Control Policies (SCPs):** In AWS Organizations, SCPs can restrict permissions for all IAM users and roles in member accounts. If an SCP denies an action, no identity-based or resource-based policy in that account can override it.
8.  **Incorrect CLI/SDK Configuration:** The CLI or SDK might be configured to use the wrong AWS profile, region, or account, leading it to assume an identity that genuinely doesn't have permissions in the *intended* account or region.

## Step-by-Step Fix

Troubleshooting `AccessDeniedException` requires a systematic approach. Here’s how I typically go about it:

1.  **Identify the Exact Action and Resource:**
    *   Carefully read the error message. It usually provides crucial details like the `User ARN`, the `Action` being attempted (e.g., `s3:GetObject`), and the `Resource ARN` it's trying to access. This information is your primary lead.
    *   *Example Error Message Snippet:* `User: arn:aws:iam::123456789012:user/my-user is not authorized to perform: s3:GetObject on resource: arn:aws:s3:::my-bucket/path/to/object.txt`

2.  **Identify the Principal (Current Identity):**
    *   Confirm which IAM user or role you are currently operating as. This is critical because you might *think* you're one identity, but your CLI/SDK is configured for another.
    *   Run the following command:
        ```bash
        aws sts get-caller-identity
        ```
    *   This will return the ARN of the user or assumed role making the call, along with the Account ID. Verify this matches your expectation. If you're assuming a role, the ARN will typically look like `arn:aws:iam::ACCOUNT_ID:assumed-role/ROLE_NAME/SESSION_NAME`.

3.  **Use the IAM Policy Simulator (Highly Recommended):**
    *   Navigate to the IAM console, then select **Policy Simulator** from the left navigation pane.
    *   **Select the IAM Entity:** Choose the user or role identified in Step 2.
    *   **Select Actions:** Input the exact action(s) identified in Step 1 (e.g., `s3:GetObject`).
    *   **Specify Resource ARNs:** Provide the exact resource ARN(s) from Step 1.
    *   **Run Simulation:** The simulator will show you which policies allow or deny the action and why. It's incredibly powerful for pinpointing the exact policy statement causing the issue, including explicit denies or permission boundary effects.

4.  **Review Applicable Policies:**
    *   **Identity-based Policies:**
        *   In the IAM console, navigate to the user or role identified in Step 2.
        *   Examine the "Permissions" tab. Look for attached policies. Does any policy contain an `Allow` statement for the `Action` on the `Resource`? Is there an explicit `Deny`?
    *   **Resource-based Policies:**
        *   If the resource is one that supports resource policies (e.g., S3 bucket, SQS queue, KMS key, Lambda function), navigate to that resource's console page.
        *   Check its permissions or policy tab. Is there an explicit `Deny` for your principal? Is there an `Allow` that *should* be there but isn't? In my experience, forgetting to add an external account to an S3 bucket policy is a frequent culprit for cross-account access issues.
    *   **Trust Policies (for Roles):** If you're assuming a role, check the "Trust relationships" tab of that role in the IAM console. Ensure your user or role is listed in the `Principal` element of the `Allow` statement.

5.  **Check Organization SCPs and Permission Boundaries:**
    *   If you're in an AWS Organization, consult your AWS administrator to check for any SCPs that might be denying the action. SCPs are applied at the root or OU level and can silently block actions across an entire account.
    *   Similarly, check if a permission boundary is attached to the IAM user or role. This will be visible on the IAM user/role details page.

6.  **Add or Modify Policies:**
    *   Based on the findings from the Policy Simulator and policy reviews, create a new IAM policy or modify an existing one to grant the necessary permissions.
    *   **Principle of Least Privilege:** Grant only the specific actions required for the specific resources, rather than broad `*` permissions.
    *   **Example Policy Snippet (to allow S3 object access):**
        ```json
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
                        "arn:aws:s3:::my-bucket-name",
                        "arn:aws:s3:::my-bucket-name/*"
                    ]
                }
            ]
        }
        ```
    *   Attach this policy to the IAM user, group, or role. If it's a resource policy, add it directly to the resource.

7.  **Retest the Action:** Once changes are made, re-attempt the action that previously failed.

## Code Examples

Here are some concise, copy-paste ready examples relevant to troubleshooting `AccessDeniedException`:

**1. Checking your current AWS CLI identity:**

```bash
aws sts get-caller-identity
```

*Expected output:*
```json
{
    "UserId": "AIDACKCELA6K3EAXG6W3L",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/ethan.calloway"
}
```
Or, if you've assumed a role:
```json
{
    "UserId": "AROAJM2F3A4Y56B7T8C90:my-session",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:assumed-role/DevRole/my-session"
}
```

**2. Example IAM Policy for S3 read access (to add or modify):**

This policy grants permissions to list objects in a specific bucket and retrieve individual objects from it.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::my-source-bucket-name"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::my-source-bucket-name/*"
        }
    ]
}
```

**3. Example IAM Policy for EC2 instance description (to add or modify):**

This policy allows viewing information about EC2 instances, which is often a basic requirement for many tools.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeRegions",
                "ec2:DescribeAvailabilityZones"
            ],
            "Resource": "*"
        }
    ]
}
```
*Note*: `Resource: "*"` is common for `Describe` actions as they are often read-only and don't operate on specific ARNs.

## Environment-Specific Notes

The way credentials and permissions are managed can vary significantly depending on your operating environment.

*   **AWS CLI / Local Development:**
    *   **Credentials Files:** The AWS CLI and SDKs prioritize credentials from environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`), then the `~/.aws/credentials` file, and then the `~/.aws/config` file (for profiles). Ensure the correct profile is being used, either via the `AWS_PROFILE` environment variable or the `--profile` flag in CLI commands. A common mistake is assuming the default profile is active when another one should be used.
    *   **Region:** Also verify the `AWS_REGION` environment variable or `--region` flag. Actions on resources are often region-specific.
    *   Use `aws configure list` to see the currently active configuration.

*   **Cloud Environments (EC2, ECS, Lambda, EKS):**
    *   **IAM Roles:** In these environments, identities typically derive their permissions from an attached IAM role.
        *   **EC2:** An instance profile is associated with an IAM role. Ensure the EC2 instance has the correct instance profile attached, and that the role itself has the necessary policies.
        *   **Lambda:** A Lambda function's "Execution role" dictates what it can do. Verify this role has the required permissions. I've often seen `AccessDenied` for Lambda functions trying to access S3 or DynamoDB because the execution role was created with minimal permissions and never updated.
        *   **ECS/EKS:** Tasks running on ECS or pods on EKS often use Task Roles (ECS) or Service Account Roles (EKS with IRSA) to grant permissions. Ensure these roles are correctly configured and attached.
    *   **Implicit vs. Explicit:** In cloud environments, credentials are automatically managed via the instance/task metadata service. You don't usually set explicit `AWS_ACCESS_KEY_ID` environment variables. The `AccessDeniedException` directly points to the *role's* missing permissions.

*   **Docker Containers:**
    *   If you're running AWS CLI or SDK within a Docker container, you need to ensure credentials are provided to the container.
    *   **Environment Variables:** You can pass `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc., as environment variables using `-e` in `docker run`.
    *   **Volume Mounts:** Mount your `~/.aws` directory from the host into the container (e.g., `-v ~/.aws:/root/.aws` or `~/.aws:/home/appuser/.aws`) so the container can access your shared credentials and config files.
    *   **IAM Roles:** If your Docker container is running on an EC2 instance or ECS task, it will automatically inherit the permissions of the underlying IAM role, assuming the SDK/CLI inside the container uses the default credential provider chain.

## Frequently Asked Questions

**Q: Why am I getting `AccessDeniedException` even though my IAM user has `AdministratorAccess`?**
**A:** This is often due to an explicit `Deny` statement from a higher-level policy. Check for Service Control Policies (SCPs) in AWS Organizations, or a resource-based policy (e.g., an S3 bucket policy) that explicitly denies your action or principal. Permission boundaries can also restrict `AdministratorAccess` to a subset of permissions.

**Q: How can I debug this error if I don't have IAM permissions to use the Policy Simulator or view all policies?**
**A:** If you're restricted, you'll need to work with an AWS administrator. Provide them with the full error message, including the `Action` and `Resource` ARN, and your `sts get-caller-identity` output. They can then use the Policy Simulator or review logs/policies on your behalf.

**Q: Can a resource policy override an IAM user's policy?**
**A:** Yes. An explicit `Deny` in *any* policy, including a resource policy, will always take precedence over an `Allow` in an identity-based policy. Conversely, an `Allow` in a resource policy can grant access to a principal even if their identity-based policies do not. The combination of all `Allow` and `Deny` statements determines the final permission.

**Q: I'm using an AWS SSO profile or `aws-vault`. Could that be the issue?**
**A:** Yes. Ensure your SSO session or `aws-vault` credentials are still valid and haven't expired. You might need to re-authenticate (e.g., `aws sso login` or `aws-vault login`). Old or expired temporary credentials are a common source of `AccessDenied` errors when using these tools.

**Q: The error mentions a specific service (e.g., `kms:Decrypt`), but I'm just trying to read an S3 object. What gives?**
**A:** This indicates that the S3 object you're trying to access is encrypted, likely with an AWS Key Management Service (KMS) key. In addition to `s3:GetObject` permission, your identity needs `kms:Decrypt` permission on the specific KMS key used to encrypt the S3 object. Check the S3 object's properties to identify the KMS key ARN.

## Related Errors