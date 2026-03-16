# AWS EKS You must be logged in to the server (Unauthorized)
> Encountering the "You must be logged in to the server (Unauthorized)" error with AWS EKS means `kubectl` cannot authenticate to your cluster; this guide explains how to fix it through a structured troubleshooting process.

## What This Error Means

When you run `kubectl` commands against an AWS EKS cluster and receive the message "error: You must be logged in to the server (Unauthorized)", it indicates that your `kubectl` client, after attempting to connect to the Kubernetes API server, was rejected due to insufficient or incorrect authentication. This is an HTTP 401 Unauthorized status coming directly from the API server. It essentially means the API server doesn't recognize your identity or doesn't grant your identity permission to perform *any* action, not even to list basic resources. This isn't a networking issue where the server is unreachable; rather, it's a security gatekeeper actively denying access.

## Why It Happens

The core of this error lies in the authentication flow between your client machine and the EKS cluster's Kubernetes API server. Unlike a vanilla Kubernetes cluster where you might use a service account token or client certificates directly, EKS leverages AWS IAM for authentication. When you run `kubectl`, it relies on the `aws-cli` (or previously `aws-iam-authenticator`) to generate a temporary, signed URL (a pre-signed URL) that proves your AWS IAM identity. This identity is then presented to the EKS control plane. If this handshake fails at any point, or if the presented identity isn't recognized or authorized by the cluster, you'll hit this "Unauthorized" wall.

In my experience, this usually boils down to a mismatch: the identity `kubectl` is trying to use doesn't match what the EKS cluster expects or has permissions for.

## Common Causes

Several factors can lead to this "Unauthorized" error. Understanding these can quickly narrow down your troubleshooting scope:

1.  **Missing or Expired AWS Credentials:** `kubectl` indirectly uses your AWS CLI credentials (`~/.aws/credentials` or environment variables) to authenticate with EKS. If these are missing, expired, or incorrect, the authentication process will fail before `kubectl` even talks to EKS. This is particularly common when using temporary credentials (e.g., from SSO or assuming roles) that have a short expiry.
2.  **Incorrect `kubeconfig` Context:** Your `kubeconfig` file (typically `~/.kube/config`) can contain multiple cluster configurations and contexts. If `kubectl` is configured to use the wrong context, it might be trying to connect to a different cluster, or a cluster where the associated authentication details are outdated or invalid.
3.  **`aws-auth` ConfigMap Misconfiguration:** EKS uses a special `aws-auth` ConfigMap in the `kube-system` namespace to map AWS IAM users and roles to Kubernetes RBAC roles and groups. If your IAM identity (user or role) is not correctly listed in this ConfigMap, or if there's a typo, the EKS cluster won't recognize your AWS identity and deny access. This is a very frequent culprit, especially after cluster creation or when onboarding new team members.
4.  **Region Mismatch:** Your `aws-cli` configuration or environment variables might be set to a different AWS region than where your EKS cluster resides. `kubectl` will then try to authenticate to EKS in the wrong region, leading to an authentication failure.
5.  **Outdated AWS CLI or `kubectl`:** The underlying authentication mechanism for EKS has evolved. If your `aws-cli` (especially if you're still on v1) or `kubectl` is significantly outdated, it might not support the current EKS authentication protocol, leading to issues. `aws-cli` v2 is recommended as it includes the necessary `eks get-token` functionality.
6.  **IAM Permissions:** Even if your IAM user/role is correctly mapped in `aws-auth`, it still needs the necessary IAM permissions to *generate* the authentication token. Specifically, the `eks:DescribeCluster` and `eks:AccessCluster` permissions are crucial.
7.  **Multiple AWS Accounts/Profiles:** If you frequently switch between AWS accounts or use different profiles, it's easy for `kubectl` to pick up credentials for the wrong account, leading to an authentication error with the target EKS cluster.
8.  **VPC Endpoint Policies (Less Common but Possible):** If you're using VPC endpoints for EKS, overly restrictive endpoint policies could prevent your IAM principal from accessing the EKS API. However, this typically manifests as more of a "connection refused" or timeout if the policy is blocking traffic completely, rather than "unauthorized." For "Unauthorized," it implies the connection was made, but the identity was rejected.

## Step-by-Step Fix

Here's a structured approach to troubleshoot and resolve the "Unauthorized" error. I've often seen this sequence effectively resolve the issue for myself and my teams.

### 1. Verify Your AWS CLI Authentication

First, ensure your `aws-cli` is correctly configured and authenticated to the AWS account where your EKS cluster resides.

1.  **Check `aws-cli` configuration:**
    ```bash
    aws configure list
    ```
    This shows your active profile, region, and output format. Ensure the region matches your EKS cluster's region.
2.  **Verify your current IAM identity:**
    ```bash
    aws sts get-caller-identity
    ```
    This command returns the ARN of the IAM user or role currently configured for your `aws-cli`. Make sure this is the identity you expect to be using for EKS and that it belongs to the correct AWS account. If you're using a specific profile, you might need `aws sts get-caller-identity --profile your-profile-name`.

    *If `aws sts get-caller-identity` fails or shows an unexpected identity, your core AWS authentication is broken. Fix your AWS credentials (e.g., `aws configure` or set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` environment variables) before proceeding.*

### 2. Update Your `kubeconfig`

The `kubeconfig` file might be outdated or incorrect. EKS clusters dynamically generate temporary authentication tokens, and your `kubeconfig` needs to be able to request these.

1.  **Update `kubeconfig` using `aws-cli`:**
    ```bash
    aws eks update-kubeconfig --name <YOUR_CLUSTER_NAME> --region <YOUR_CLUSTER_REGION>
    ```
    Replace `<YOUR_CLUSTER_NAME>` and `<YOUR_CLUSTER_REGION>` with your actual cluster details. This command automatically adds or updates the cluster entry in your `kubeconfig` (`~/.kube/config` by default) and ensures it uses the `aws-cli` to generate authentication tokens. If you manage multiple AWS profiles, add `--profile <YOUR_AWS_PROFILE>` to this command.

    *After running this, `kubectl` should automatically use the newly configured context for that cluster. If you have multiple contexts, you might need to explicitly switch.*

### 3. Verify `kubeconfig` Context

Ensure `kubectl` is actually using the correct cluster context.

1.  **List available contexts:**
    ```bash
    kubectl config get-contexts
    ```
    Look for your cluster's context. The `*` indicates the currently active context.
2.  **Switch to the correct context (if needed):**
    ```bash
    kubectl config use-context arn:aws:eks:<YOUR_CLUSTER_REGION>:<YOUR_ACCOUNT_ID>:cluster/<YOUR_CLUSTER_NAME>
    ```
    Or use the simpler context name that `update-kubeconfig` usually creates, which is `arn:aws:eks:<region>:<account-id>:cluster/<cluster-name>`.

### 4. Review IAM Permissions

The IAM user or role identified by `aws sts get-caller-identity` needs specific permissions to interact with EKS and its API server.

1.  **Check IAM Policy:** Ensure the IAM user or role has at least the following permissions:
    *   `eks:DescribeCluster`
    *   `eks:AccessCluster` (implicitly granted by `eks:DescribeCluster` for `kubeconfig` generation, but good to verify explicit access if issues persist).
    *   `sts:GetServiceBearerToken` (for the `eks get-token` mechanism).
    *   `ec2:DescribeRegions` (often part of general AWS console access policies).

    These permissions are typically included in managed policies like `AmazonEKSClusterPolicy` or `AmazonEKSWorkerNodePolicy`, but for a user/role managing EKS, custom policies might be needed.

### 5. Check the `aws-auth` ConfigMap

This is often the trickiest part, especially for new clusters or when adding new users/roles. The `aws-auth` ConfigMap in the `kube-system` namespace maps AWS IAM identities to Kubernetes RBAC groups.

1.  **Retrieve the `aws-auth` ConfigMap:**
    ```bash
    kubectl get configmap aws-auth -n kube-system -o yaml
    ```
    *If this command itself returns "Unauthorized", it means you're not even allowed to read the `aws-auth` ConfigMap, indicating a deeper authentication problem. In this scenario, you'll need to use an identity that *does* have access (e.g., the cluster creator's IAM identity, or an administrative role) to inspect and modify it. Alternatively, if no one has access, you might need to use the AWS Console to manually add a new IAM role/user mapping.*

2.  **Inspect the `mapUsers` and `mapRoles` sections:**
    Look for your IAM user ARN or IAM role ARN under `mapUsers` or `mapRoles`.
    *   **`mapUsers` Example:**
        ```yaml
        apiVersion: v1
        data:
          mapUsers: |
            - userarn: arn:aws:iam::123456789012:user/daniel.kovacs
              username: daniel.kovacs
              groups:
                - system:masters
        # ...
        ```
    *   **`mapRoles` Example:**
        ```yaml
        apiVersion: v1
        data:
          mapRoles: |
            - rolearn: arn:aws:iam::123456789012:role/EKSAdminRole
              username: EKSAdminRole
              groups:
                - system:masters
        # ...
        ```
    Ensure your `userarn` or `rolearn` exactly matches the output of `aws sts get-caller-identity`. The `username` can be arbitrary but should be unique. The `groups` entry (e.g., `system:masters`) determines the Kubernetes RBAC permissions. For initial access, `system:masters` grants superuser privileges.

3.  **Update the `aws-auth` ConfigMap (if necessary):**
    If your identity is missing or incorrect, you'll need to update this ConfigMap. The safest way is to edit it:
    ```bash
    kubectl edit configmap aws-auth -n kube-system
    ```
    Add or modify the `mapUsers` or `mapRoles` section. Be extremely careful with YAML syntax, as an invalid file will prevent future updates. If you're managing this via IaC (Terraform, CloudFormation), update your code and apply it.

### 6. Ensure `kubectl` and `aws-cli` are Up-to-Date

Outdated tools can cause compatibility issues.
*   **`kubectl`:** Aim for a version that is within one minor version of your EKS cluster's Kubernetes version.
    ```bash
    kubectl version --client
    ```
*   **`aws-cli`:** Ensure you're using `aws-cli` v2.
    ```bash
    aws --version
    ```
    If you're on v1, consider upgrading to v2, as it natively includes the `eks get-token` functionality previously provided by `aws-iam-authenticator`.

### 7. Troubleshoot Advanced Scenarios

*   **Temporary Credentials/SSO:** If you're using AWS SSO or assuming roles, ensure your temporary credentials are valid and haven't expired. You might need to re-authenticate via `aws sso login` or re-assume your role.
*   **Proxy Settings:** If you are behind a corporate proxy, ensure your `kubectl` and `aws-cli` are configured to use it (e.g., `HTTPS_PROXY` environment variable). However, this would more likely lead to connection timeouts than "Unauthorized."
*   **Environment Variables:** Double-check `AWS_PROFILE`, `AWS_REGION`, `KUBECONFIG` environment variables, as these can override default settings and lead to unexpected behavior.

## Code Examples

These are concise, ready-to-copy-paste commands for quick verification and fixes.

**1. Check current AWS identity:**
```bash
aws sts get-caller-identity --output json
```

**2. Update `kubeconfig` for an EKS cluster:**
```bash
aws eks update-kubeconfig --name my-production-cluster --region us-east-1 --profile my-dev-profile
```
*(Replace `my-production-cluster`, `us-east-1`, and `my-dev-profile` with your actual values.)*

**3. List and switch `kubectl` contexts:**
```bash
kubectl config get-contexts
kubectl config use-context arn:aws:eks:us-east-1:123456789012:cluster/my-production-cluster
```
*(The context name is typically the full ARN, but can be customized.)*

**4. View the `aws-auth` ConfigMap:**
```bash
kubectl get configmap aws-auth -n kube-system -o yaml
```

**5. Edit the `aws-auth` ConfigMap (use with caution):**
```bash
kubectl edit configmap aws-auth -n kube-system
```

## Environment-Specific Notes

The "Unauthorized" error can manifest slightly differently depending on your operating environment.

*   **Cloud (CI/CD Pipelines):** When encountering this in a CI/CD pipeline (e.g., GitLab CI, GitHub Actions, Jenkins), the issue is almost always related to the IAM role attached to the runner or the credentials configured for the pipeline step.
    *   **Solution:** Ensure the IAM role associated with your CI/CD agent has the necessary `eks:*` permissions and is correctly mapped in the `aws-auth` ConfigMap of your target EKS cluster. If using OIDC, verify the IAM role's trust policy correctly trusts the OIDC provider (e.g., `token.actions.githubusercontent.com`). I've spent countless hours debugging pipelines only to find a missing `mapRoles` entry or an incorrectly configured trust policy.
*   **Docker Containers:** If you're running `kubectl` within a Docker container, the container needs access to your AWS credentials and `kubeconfig`.
    *   **Solution:** You'll typically mount `~/.aws` and `~/.kube` into the container. For example: `docker run -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube my-kubectl-image kubectl get nodes`. Ensure the `AWS_PROFILE` or other credential environment variables are correctly passed or set within the container.
*   **Local Development Machine:** This is the most common scenario, covered extensively in the "Step-by-Step Fix" section. The key here is managing potentially multiple AWS profiles, SSO sessions, and `kubeconfig` files.
    *   **Solution:** Always explicitly set `AWS_PROFILE` or use the `--profile` flag with `aws-cli` commands, and ensure your `KUBECONFIG` environment variable points to the correct `kubeconfig` file if you're not using the default `~/.kube/config`. Running `aws sts get-caller-identity` and `kubectl config current-context` repeatedly during troubleshooting is a good habit.

## Frequently Asked Questions

**Q: I get "connection refused" instead of "Unauthorized". Is it the same issue?**
**A:** No, "connection refused" is a fundamentally different error. It means your client couldn't even establish a TCP connection to the Kubernetes API server. This typically points to networking issues (firewall, security groups), incorrect API endpoint in your `kubeconfig`, or the API server itself being down or inaccessible. This guide specifically addresses the "Unauthorized" error, where a connection *was* made but authentication failed.

**Q: How do I manage multiple AWS accounts or profiles when working with EKS?**
**A:** Use the `AWS_PROFILE` environment variable (e.g., `export AWS_PROFILE=my-dev-profile`) or the `--profile` flag with `aws-cli` commands (e.g., `aws eks update-kubeconfig --profile my-dev-profile ...`). When running `kubectl`, it will implicitly use the credentials associated with the profile configured in your `kubeconfig` or the active `AWS_PROFILE`.

**Q: Do I need `aws-iam-authenticator` installed separately anymore?**
**A:** For `aws-cli` v2, no. `aws-cli` v2 includes the `eks get-token` command which replaces the functionality of `aws-iam-authenticator`. If you're on `aws-cli` v1, you might still need it, but upgrading to v2 is highly recommended.

**Q: Can this error be caused by a firewall on my machine?**
**A:** Unlikely for "Unauthorized." A firewall blocking outbound connections would typically result in a "connection timed out" or "connection refused" error, as the `kubectl` client wouldn't even be able to reach the EKS API server. "Unauthorized" means the connection was successful, but the server rejected your credentials.

**Q: How can I verify which IAM identity `kubectl` is *actually* using?**
**A:** `kubectl` doesn't directly show the IAM identity it's using. Instead, you verify this by checking your `aws-cli`'s active configuration (`aws configure list`) and the `aws sts get-caller-identity` output for your active profile. The `aws eks update-kubeconfig` command then configures `kubectl` to use this active AWS identity.

## Related Errors

- [kubernetes-connection-refused](/errors/kubernetes-connection-refused.html)