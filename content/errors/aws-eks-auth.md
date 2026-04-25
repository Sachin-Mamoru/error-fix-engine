# AWS EKS You must be logged in to the server (Unauthorized)
> Encountering "You must be logged in to the server (Unauthorized)" when interacting with AWS EKS means kubectl cannot authenticate; this guide explains how to fix it.

## What This Error Means

When you see the error `error: You must be logged in to the server (Unauthorized)` after running a `kubectl` command against an AWS EKS cluster, it indicates that your `kubectl` client failed to authenticate with the Kubernetes API server running within your EKS cluster. This isn't necessarily an issue with the cluster itself being down, but rather a problem with how your client is attempting to prove its identity or its authorization once identified. Essentially, the API server rejected your request because it couldn't verify who you are, or because the identity you presented lacks the necessary permissions to access the API. In my experience, this is one of the most common initial hurdles engineers face when setting up `kubectl` for EKS.

## Why It Happens

Interacting with an EKS cluster using `kubectl` involves a multi-layered authentication process that's unique to AWS. Unlike self-managed Kubernetes clusters that might use service account tokens, client certificates, or basic authentication, EKS leverages AWS Identity and Access Management (IAM) for authentication.

Here's the simplified flow:
1.  You run a `kubectl` command.
2.  `kubectl` uses your `kubeconfig` file to determine the cluster context, including the `exec` plugin responsible for EKS authentication.
3.  This `exec` plugin (historically `aws-iam-authenticator`, now often integrated into `kubectl-eks` or `aws` CLI) generates a temporary signed URL using your active AWS credentials.
4.  This signed URL is then used to make an API call to the EKS control plane.
5.  The EKS control plane validates the AWS credentials embedded in the signed URL via AWS STS (Security Token Service).
6.  If the credentials are valid, EKS then checks its internal `aws-auth` ConfigMap within the `kube-system` namespace to map the AWS IAM identity (user or role) to a Kubernetes user or group.
7.  Finally, standard Kubernetes Role-Based Access Control (RBAC) takes over, evaluating the permissions assigned to the mapped Kubernetes user/group.

The "Unauthorized" error typically means the process failed at step 4, 5, or 6:
*   **Step 4/5 (AWS Authentication Failure):** Your AWS credentials are not valid, expired, or don't have permission to `eks:DescribeCluster` or `sts:GetCallerIdentity` for the specified cluster/region.
*   **Step 6 (EKS `aws-auth` Mapping Failure):** Your valid AWS IAM identity is not correctly mapped to a Kubernetes user or group in the `aws-auth` ConfigMap.

I've seen this in production when developers accidentally switched AWS profiles or regions, causing the `kubectl` command to present the wrong AWS identity to the cluster.

## Common Causes

This error generally boils down to a few key areas where the authentication chain breaks:

*   **Incorrect AWS Credentials:** Your AWS CLI is configured with credentials that are expired, incorrect, or belong to an account/IAM entity that doesn't have access to the EKS cluster. This is often the first place I check.
*   **Wrong `kubeconfig` Context:** Your `kubectl` command is attempting to use the wrong cluster context from your `kubeconfig` file, pointing to a different cluster or even a non-EKS cluster where the `exec` plugin isn't relevant.
*   **Outdated or Missing `kubeconfig`:** Your `kubeconfig` file (typically `~/.kube/config`) doesn't contain the correct EKS cluster entry, or it's malformed. For EKS, the `kubeconfig` needs specific `exec` blocks to invoke the AWS authentication helper.
*   **Missing or Misconfigured `aws-iam-authenticator` / `kubectl-eks` Plugin:** The `exec` plugin specified in your `kubeconfig` (usually `aws-iam-authenticator` or the `kubectl-eks` plugin that comes with the AWS CLI) is not installed, not in your PATH, or is an outdated version.
*   **IAM User/Role Not Mapped in `aws-auth` ConfigMap:** Even if your AWS credentials are valid, the specific IAM user or role you're authenticating as might not be present in the EKS cluster's `aws-auth` ConfigMap. This ConfigMap is crucial as it tells EKS which AWS identities map to which Kubernetes RBAC identities.
*   **Network Connectivity Issues:** Less common for "Unauthorized," but a blocked connection to the EKS API endpoint could manifest similarly if the initial handshake fails completely.
*   **AWS STS Permissions:** The IAM user or role you're using might lack the `sts:AssumeRole` or `sts:GetCallerIdentity` permissions required for the authentication plugin to generate the necessary temporary credentials.

## Step-by-Step Fix

Let's systematically troubleshoot this error.

1.  **Verify Your AWS CLI Configuration and Identity**
    First, ensure your AWS CLI is configured correctly and you're using the intended AWS identity.
    ```bash
    # Check your active AWS CLI profile
    aws configure list

    # Confirm the AWS identity you're currently using
    aws sts get-caller-identity
    ```
    Ensure the `Account` and `Arn` from `get-caller-identity` match the expected AWS account and IAM user/role that *should* have access to your EKS cluster. If this is incorrect, set the right profile using `export AWS_PROFILE=your-profile-name` or `aws configure`.

2.  **Ensure `kubeconfig` is Correct and Updated**
    For EKS, the recommended way to generate or update your `kubeconfig` is using the AWS CLI. This command automatically sets up the `exec` plugin for authentication.

    ```bash
    # Update your kubeconfig for the specific EKS cluster and region
    # Replace 'my-cluster-name' with your EKS cluster's name
    # Replace 'us-west-2' with your EKS cluster's region
    aws eks update-kubeconfig --name my-cluster-name --region us-west-2

    # If you want to specify a non-default kubeconfig file path:
    # aws eks update-kubeconfig --name my-cluster-name --region us-west-2 --kubeconfig /path/to/my/custom/kubeconfig
    ```
    This command will add or update the cluster entry in your `~/.kube/config` (or the path you specify). It also ensures the `exec` block pointing to the `aws-iam-authenticator` or `kubectl-eks` plugin is correctly configured.

3.  **Verify `kubectl` Context**
    After updating `kubeconfig`, make sure `kubectl` is actually using the correct context.
    ```bash
    # List all available contexts
    kubectl config get-contexts

    # Switch to the correct context if needed. The name is usually
    # arn:aws:eks:REGION:ACCOUNT_ID:cluster/CLUSTER_NAME
    kubectl config use-context arn:aws:eks:us-west-2:123456789012:cluster/my-cluster-name
    ```
    The `update-kubeconfig` command usually sets the context automatically, but it's good to double-check.

4.  **Check `aws-iam-authenticator` / `kubectl-eks` Plugin Installation**
    The `exec` plugin needs to be installed and accessible in your system's PATH.
    *   If you're using `aws-iam-authenticator` directly:
        ```bash
        which aws-iam-authenticator
        aws-iam-authenticator version
        ```
        If it's not found or outdated, install/update it.
    *   If you're using the newer AWS CLI v2 `kubectl-eks` plugin:
        ```bash
        aws eks get-token --cluster-name my-cluster-name # Test the plugin directly
        # You should see token details if it's working
        ```
        The `update-kubeconfig` command should configure `kubectl` to use whichever is appropriate based on your AWS CLI version. Ensure your AWS CLI is up-to-date.

5.  **Examine the EKS `aws-auth` ConfigMap**
    This is often the culprit if your AWS credentials and `kubeconfig` are otherwise correct. The `aws-auth` ConfigMap maps AWS IAM entities to Kubernetes RBAC.
    ```bash
    kubectl get configmap aws-auth -n kube-system -o yaml
    ```
    Look for the `mapUsers` and `mapRoles` sections. Your IAM user or the role you are assuming must be listed there, mapped to a Kubernetes `username` and `groups`.
    For example, if you are `arn:aws:iam::123456789012:user/daniel.kovacs`, you'd expect to see:
    ```yaml
    # ...
    data:
      mapUsers: |
        - userarn: arn:aws:iam::123456789012:user/daniel.kovacs
          username: daniel.kovacs
          groups:
            - system:masters
    # ...
    ```
    If your entry is missing or incorrect, you need to update this ConfigMap. The safest way is often through `eksctl` or infrastructure-as-code tools like Terraform or CloudFormation. Manual edits with `kubectl edit cm aws-auth -n kube-system` are possible but risky, as syntax errors can lock you out.

6.  **Verify IAM Permissions**
    Ensure the IAM user or role you are using has the necessary permissions. At a minimum, it needs `eks:DescribeCluster` and permission to perform STS actions like `sts:GetCallerIdentity` for the `aws-iam-authenticator` to function. For full admin access, it would typically be mapped to `system:masters` in the `aws-auth` ConfigMap.

    *   **Common EKS access policy:** `AmazonEKSClusterPolicy` for cluster management (though `system:masters` mapping provides full control *within* K8s).
    *   **STS permissions:** `sts:GetCallerIdentity` for the principal, and `sts:AssumeRole` if cross-account access or role assumption is involved.

## Code Examples

Here are some concise, copy-paste ready examples for critical checks:

**1. Check Current AWS Identity:**
```bash
aws sts get-caller-identity
```

**2. Update `kubeconfig` for an EKS Cluster:**
```bash
aws eks update-kubeconfig --name my-production-cluster --region us-east-1
```

**3. List and Use `kubectl` Contexts:**
```bash
# List all contexts
kubectl config get-contexts

# Switch to a specific EKS context (replace with your cluster's context name)
kubectl config use-context arn:aws:eks:us-east-1:123456789012:cluster/my-production-cluster
```

**4. Inspect the `aws-auth` ConfigMap:**
```bash
kubectl get configmap aws-auth -n kube-system -o yaml
```
*Expected output snippet demonstrating a user mapping:*
```yaml
apiVersion: v1
data:
  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/my-dev-user
      username: my-dev-user
      groups:
        - system:authenticated
        - custom-dev-group
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/my-dev-role
      username: my-dev-role
      groups:
        - custom-dev-group
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
# ... rest of metadata
```

## Environment-Specific Notes

The troubleshooting steps remain similar, but the source of the AWS credentials and `kubeconfig` can vary:

*   **Local Development Environment:**
    *   **Credentials:** Typically sourced from `~/.aws/credentials` or environment variables like `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`. Ensure these are correctly set and not expired.
    *   **`kubeconfig`:** Usually `~/.kube/config`. Ensure it's not overridden by `KUBECONFIG` environment variable if you're not expecting it.

*   **CI/CD Pipelines (e.g., GitHub Actions, GitLab CI, Jenkins):**
    *   **Credentials:** Often provided via temporary credentials assumed by an IAM role (e.g., OIDC for GitHub Actions, service account roles for Jenkins running in Kubernetes, or directly set as environment variables). Ensure the IAM role has the necessary permissions (`sts:AssumeRole` and `eks:DescribeCluster`). I've seen this in production when the CI/CD role didn't have the `sts:AssumeRoleWithWebIdentity` permission necessary for OIDC.
    *   **`kubeconfig`:** Usually generated dynamically within the pipeline using `aws eks update-kubeconfig`. Ensure the correct cluster name and region are passed. The `kubectl-eks` plugin also needs to be available in the CI/CD runner's environment.

*   **EC2 Instances within the same AWS account:**
    *   **Credentials:** Best practice is to attach an IAM instance profile to the EC2 instance. This provides temporary credentials automatically. Ensure the instance profile's associated role has the necessary permissions to interact with EKS.
    *   **`kubeconfig`:** Typically generated on the instance itself. The `aws eks update-kubeconfig` command will automatically use the instance's IAM role for authentication.

## Frequently Asked Questions

**Q: What if I'm using an EC2 instance role to access EKS?**
A: Ensure the EC2 instance's IAM role has permissions like `eks:DescribeCluster` and that this role is mapped in the EKS cluster's `aws-auth` ConfigMap under `mapRoles`. `aws eks update-kubeconfig` run on the EC2 instance will use the instance's role automatically.

**Q: How do I check if `aws-iam-authenticator` or the `kubectl-eks` plugin is installed and working?**
A: For `aws-iam-authenticator`, run `which aws-iam-authenticator` and `aws-iam-authenticator version`. For the `kubectl-eks` plugin, it's part of the AWS CLI v2; you can test its functionality by running `aws eks get-token --cluster-name YOUR_CLUSTER_NAME --region YOUR_REGION`.

**Q: Can network firewalls cause this "Unauthorized" error?**
A: While possible, network issues more typically result in `connection refused` or `timeout` errors. An "Unauthorized" error specifically implies the API server received your request but rejected it based on authentication/authorization. However, if an outbound firewall prevents your client from reaching AWS STS or the EKS control plane to generate the token, it could indirectly lead to this error.

**Q: My `kubeconfig` looks correct, my AWS credentials are fine, what else could it be?**
A: In this scenario, the `aws-auth` ConfigMap is almost always the answer. Double-check that your exact IAM user or role ARN is mapped to the correct Kubernetes groups (e.g., `system:masters` for admin access) in the `mapUsers` or `mapRoles` sections of the `aws-auth` ConfigMap in the `kube-system` namespace.

**Q: Why do I need `aws-iam-authenticator` or the `kubectl-eks` plugin if `kubectl` is already installed?**
A: `kubectl` itself doesn't inherently understand AWS's IAM authentication mechanism. These plugins act as an `exec` credential provider, dynamically fetching temporary, signed AWS credentials that the EKS API server can validate against IAM, bridging the gap between Kubernetes RBAC and AWS IAM identities.

## Related Errors
*(none)*