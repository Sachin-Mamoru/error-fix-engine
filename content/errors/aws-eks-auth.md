# AWS EKS You must be logged in to the server (Unauthorized)
> Encountering the "You must be logged in to the server (Unauthorized)" error when accessing AWS EKS clusters means your `kubectl` client lacks proper authentication or authorization to interact with the cluster API, and this guide provides practical steps to resolve it.

## What This Error Means

This error message, "You must be logged in to the server (Unauthorized)", is a direct indication that your `kubectl` client cannot successfully authenticate with your Amazon Elastic Kubernetes Service (EKS) cluster's API server. When you run a `kubectl` command, it attempts to connect and present credentials to the EKS control plane. If the API server responds with an HTTP 401 Unauthorized status, it means the identity you're presenting is either invalid, expired, or simply not recognized by the cluster's authentication mechanism.

It's crucial to understand that this isn't typically a network connectivity issue (like "connection refused"). Instead, it confirms that `kubectl` *reached* the EKS API server, but your attempt to prove who you are (authentication) or what you're allowed to do (authorization) failed. In my experience, this is one of the most common hurdles new users face, and even seasoned engineers sometimes stumble upon it after credentials expire or contexts switch.

## Why It Happens

At its core, `kubectl` authentication with AWS EKS clusters relies on AWS Identity and Access Management (IAM). Unlike a standard Kubernetes cluster where you might use client certificates or service account tokens, EKS integrates with AWS IAM to manage access. Here's the simplified flow:

1.  You run a `kubectl` command (e.g., `kubectl get pods`).
2.  `kubectl` needs an authentication token for the EKS API server. It uses an `exec-plugin` (typically provided by the AWS CLI v2) to generate a temporary, signed token from AWS IAM.
3.  This token is then presented to the EKS API server.
4.  The EKS API server validates the token with AWS IAM.
5.  If valid, the API server maps the underlying IAM principal (user or role) to a Kubernetes user and groups, which are then checked against Kubernetes Role-Based Access Control (RBAC) policies and, crucially, the `aws-auth` ConfigMap within the `kube-system` namespace.

The "Unauthorized" error typically occurs when one of these steps breaks:
*   **Token Generation Failure:** The `exec-plugin` can't generate a valid token because your local AWS credentials are missing, incorrect, or expired.
*   **IAM Identity Mismatch:** The IAM user or role used to generate the token is not mapped within the EKS cluster's `aws-auth` ConfigMap to a Kubernetes user/group, or if it is, it lacks the necessary Kubernetes RBAC permissions.
*   **Incorrect Context:** Your `kubectl` is pointing to the wrong cluster or an invalid configuration.

## Common Causes

Let's break down the most frequent culprits leading to this "Unauthorized" message:

1.  **Expired or Incorrect AWS Credentials:** This is by far the leading cause. AWS temporary credentials (e.g., from an `aws sso login` session, an assumed role, or a CI/CD pipeline) have a limited lifespan. If they expire and you haven't refreshed them, the `aws` CLI can no longer generate a valid EKS authentication token. Similarly, if your `~/.aws/credentials` file is misconfigured or you're using the wrong AWS profile, you'll hit this wall.
2.  **`kubeconfig` is Out-of-Date or Incorrect:** Your local `kubeconfig` file (typically `~/.kube/config`) tells `kubectl` how to connect to your EKS cluster. If this file hasn't been updated recently with the correct EKS cluster details, or if it's pointing to a cluster that no longer exists or has had its endpoint changed, you'll face this issue. Often, I see developers forget to run `aws eks update-kubeconfig` after a cluster is created or after switching AWS regions/accounts.
3.  **IAM User/Role Not Mapped in `aws-auth` ConfigMap:** The EKS cluster's `aws-auth` ConfigMap (residing in the `kube-system` namespace) is the bridge between AWS IAM identities and Kubernetes RBAC. If the specific IAM user or role you're using isn't listed in this ConfigMap, or if it's mapped to a Kubernetes group without sufficient permissions (e.g., not `system:masters` or an equivalent custom role), you'll be unauthorized. The IAM identity that *created* the EKS cluster is automatically granted `system:masters` access, but subsequent users/roles need explicit mapping.
4.  **Incorrect AWS Region:** Your AWS CLI configuration, or the region specified when updating your `kubeconfig`, might not match the region where your EKS cluster resides. If `kubectl` tries to generate a token for a cluster in `us-east-1` but your CLI is configured for `us-west-2`, it will fail.
5.  **`aws CLI` Version or Missing `exec-plugin`:** Modern EKS authentication relies on the `aws` CLI (v2) acting as `kubectl`'s `exec-plugin`. If you have an older version of the AWS CLI or it's not correctly installed/configured in your PATH, `kubectl` won't be able to call it to generate the necessary token. While older setups used `aws-iam-authenticator`, the current standard integrates this directly into the AWS CLI.
6.  **Clock Skew:** A less common but important cause. Significant time differences between your client machine and AWS servers can invalidate temporary authentication tokens, leading to authorization failures.

## Step-by-Step Fix

Let's walk through the troubleshooting steps to get you back into your EKS cluster.

1.  **Verify Your AWS CLI Configuration and Credentials**
    First, confirm that your AWS CLI is correctly configured and has valid credentials for the AWS account where your EKS cluster lives.

    ```bash
    aws configure list
    aws sts get-caller-identity
    ```

    The `aws sts get-caller-identity` command will show you the IAM user or role currently configured for your AWS CLI. Ensure this is the identity you expect to use.
    If you're using AWS SSO, make sure your session is active:
    ```bash
    aws sso login
    ```
    If your credentials have expired, or `get-caller-identity` fails, you need to refresh them. This might involve setting environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) or re-logging in via SSO.

2.  **Update Your `kubeconfig` for EKS**
    This is often the magical fix. The `aws eks update-kubeconfig` command fetches the latest cluster endpoint and certificate data, and crucially, configures the `exec-plugin` in your `kubeconfig` to use the `aws` CLI for generating EKS authentication tokens.

    **Always specify the cluster name and region:**
    ```bash
    aws eks update-kubeconfig --name <your-cluster-name> --region <your-aws-region>
    ```
    For example:
    ```bash
    aws eks update-kubeconfig --name my-production-cluster --region us-east-1
    ```
    If you manage multiple clusters or profiles, you might want to add an `--alias` to create a more descriptive context name or use `--profile` to specify a particular AWS profile from `~/.aws/credentials`.

3.  **Check Your `kubectl` Context**
    After updating your `kubeconfig`, verify that `kubectl` is now pointing to the correct context.

    ```bash
    kubectl config current-context
    kubectl config get-contexts
    ```
    If the current context isn't the one you expect, switch to the correct one:
    ```bash
    kubectl config use-context <name-from-get-contexts>
    ```

4.  **Verify IAM Permissions and `aws-auth` ConfigMap**
    If the previous steps didn't resolve the issue, it's highly likely a problem with how your IAM identity is mapped within the EKS cluster. The user or role you are using must be listed in the `aws-auth` ConfigMap.

    **This step requires an *already authorized* user** (e.g., the original cluster creator or someone with `system:masters` access) to execute. If you are the original creator and still hitting "Unauthorized," re-check steps 1-3.

    First, inspect the `aws-auth` ConfigMap:
    ```bash
    kubectl get configmap aws-auth -n kube-system -o yaml
    ```
    Look for `mapUsers` and `mapRoles` sections. Your `aws sts get-caller-identity` output (from step 1) should correspond to an entry here.

    **Example `mapUsers` entry:**
    ```yaml
    apiVersion: v1
    data:
      mapUsers: |
        - userarn: arn:aws:iam::123456789012:user/dev-user
          username: dev-user
          groups:
            - system:masters
    kind: ConfigMap
    metadata:
      name: aws-auth
      namespace: kube-system
    ```

    If your IAM user/role is missing or incorrectly configured, the *authorized* user can add it. The easiest way for this is often using `eksctl` (if you're using it to manage your clusters) or directly editing the ConfigMap (with extreme caution).

    **Using `eksctl` to add an IAM user (recommended if `eksctl` is used):**
    ```bash
    eksctl create iamidentitymapping \
      --cluster <your-cluster-name> \
      --region <your-aws-region> \
      --arn arn:aws:iam::<your-account-id>:user/your-iam-username \
      --username your-kubernetes-username \
      --group system:masters # Or a more restrictive group
    ```
    **Using `eksctl` to add an IAM role:**
    ```bash
    eksctl create iamidentitymapping \
      --cluster <your-cluster-name> \
      --region <your-aws-region> \
      --arn arn:aws:iam::<your-account-id>:role/your-iam-role-name \
      --username your-kubernetes-username \
      --group system:masters
    ```
    Replace placeholders like `<your-cluster-name>`, `<your-aws-region>`, `<your-account-id>`, `your-iam-username`, `your-iam-role-name`, and `your-kubernetes-username`. Remember, `system:masters` grants full administrative access. For production, I generally recommend mapping to more specific RBAC roles.

5.  **Ensure `aws CLI` (v2) is Installed and Up-to-Date**
    The `exec-plugin` for EKS authentication is now integrated into the AWS CLI version 2. If you're using an older version or it's not correctly installed, the token generation will fail.
    Check your version:
    ```bash
    aws --version
    ```
    Ensure it's at least `aws-cli/2.x.x`. If not, upgrade it.

## Code Examples

Here are some ready-to-use code snippets for common tasks:

**1. Refreshing your `kubeconfig` and setting context:**

```bash
# Replace with your cluster name and region
EKS_CLUSTER_NAME="my-prod-cluster"
AWS_REGION="us-west-2"

# Update your kubeconfig. This will add/update a context in ~/.kube/config
aws eks update-kubeconfig --name "${EKS_CLUSTER_NAME}" --region "${AWS_REGION}"

# Optionally, if you have multiple profiles configured in ~/.aws/credentials
# aws eks update-kubeconfig --name "${EKS_CLUSTER_NAME}" --region "${AWS_REGION}" --profile my-dev-profile

# Verify current context (should now be your EKS cluster)
kubectl config current-context

# Test access
kubectl get nodes
```

**2. Checking your active AWS IAM identity:**

```bash
aws sts get-caller-identity
```

**3. Inspecting the EKS `aws-auth` ConfigMap:**
(Requires an authorized user to run this command successfully)

```bash
kubectl get configmap aws-auth -n kube-system -o yaml
```

**4. Adding an IAM user mapping to `aws-auth` using `eksctl`:**
(Requires `eksctl` to be installed and an authorized user)

```bash
# Replace with your details
EKS_CLUSTER_NAME="my-prod-cluster"
AWS_REGION="us-west-2"
IAM_USER_ARN="arn:aws:iam::123456789012:user/dev-user-bob"
K8S_USERNAME="bob" # This is the Kubernetes username that will be mapped
K8S_GROUPS="system:masters" # Or a more specific group like 'developers'

eksctl create iamidentitymapping \
  --cluster "${EKS_CLUSTER_NAME}" \
  --region "${AWS_REGION}" \
  --arn "${IAM_USER_ARN}" \
  --username "${K8S_USERNAME}" \
  --group "${K8S_GROUPS}"

# After adding, dev-user-bob should be able to run `aws eks update-kubeconfig` and then `kubectl get nodes`
```

## Environment-Specific Notes

The "Unauthorized" error can manifest differently or require specific considerations based on your environment.

*   **Local Development:**
    *   **Multiple AWS Profiles:** I've seen this frequently. Ensure you are explicitly using the correct AWS profile via `export AWS_PROFILE=my-profile` or by adding `--profile my-profile` to your `aws eks update-kubeconfig` command. Your `~/.aws/credentials` and `~/.aws/config` files are critical here.
    *   **Expired MFA:** If your IAM user requires MFA, ensure your SSO session or temporary credentials obtained via `aws sts get-session-token` (with MFA) are fresh.

*   **CI/CD Pipelines (e.g., Jenkins, GitLab CI, GitHub Actions):**
    *   **IAM Roles for Service Accounts (IRSA):** Best practice is to use IRSA or a dedicated IAM role for the CI/CD agent. Ensure this specific role has `eks:DescribeCluster` and `eks:UpdateKubeconfig` permissions and, most importantly, is mapped in the EKS cluster's `aws-auth` ConfigMap.
    *   **Temporary Credentials:** Pipelines often use temporary credentials. Verify that the credentials obtained by the pipeline's execution role haven't expired before `kubectl` commands are run. Time differences between the CI/CD agent and AWS services can also cause issues.

*   **Docker Containers:**
    *   **Credential Passing:** If you're running `kubectl` inside a Docker container, you must ensure AWS credentials are correctly passed into the container. This can be via environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) or by mounting the `~/.aws` directory into the container. Without these, the `aws` CLI inside the container cannot generate the EKS token.

*   **EC2 Instances (IAM Roles):**
    *   If you're running `kubectl` on an EC2 instance, it will automatically use the IAM role attached to the instance profile. Ensure this instance role has the necessary permissions (`eks:DescribeCluster` and `eks:UpdateKubeconfig`) and is mapped in the EKS cluster's `aws-auth` ConfigMap. This is a very clean way to manage access, but it still requires the `aws-auth` mapping.

*   **Multi-Account Setups:**
    *   When accessing an EKS cluster in a different AWS account, you'll typically assume a role in the target account. Ensure your `kubeconfig` update command (`aws eks update-kubeconfig`) is configured to use the assumed role's credentials (e.g., via a profile that assumes a role). The *assumed role itself* must be mapped in the target cluster's `aws-auth` ConfigMap.

## Frequently Asked Questions

**Q: Why does `aws sts get-caller-identity` work, but `kubectl get nodes` still fails with "Unauthorized"?**
**A:** `aws sts get-caller-identity` successfully verifies your local AWS credentials. This means you can talk to the AWS API. However, `kubectl get nodes` requires two things: valid AWS credentials to generate an EKS token *and* for the IAM identity associated with those credentials to be explicitly mapped to a Kubernetes user/group within the EKS cluster's `aws-auth` ConfigMap, with sufficient RBAC permissions. Your AWS credentials might be perfect, but the EKS cluster just doesn't know who you are in its Kubernetes context.

**Q: I'm using `eksctl` to manage my clusters. Is `aws eks update-kubeconfig` still necessary?**
**A:** `eksctl` typically updates your `kubeconfig` automatically when you create or interact with clusters (e.g., `eksctl get clusters` or `eksctl create cluster`). However, if you're experiencing this "Unauthorized" error, explicitly running `aws eks update-kubeconfig --name <cluster-name> --region <region>` can sometimes resolve issues by forcing a refresh and ensuring the correct `exec-plugin` configuration is in place. It's a good first diagnostic step regardless of whether you primarily use `eksctl`.

**Q: Can I use an IAM user without granting them `system:masters` access?**
**A:** Absolutely, and it's highly recommended for production environments following the principle of least privilege. Instead of `system:masters`, you can map IAM users or roles to custom Kubernetes RBAC roles. First, define your custom `Role` or `ClusterRole` and `RoleBinding` or `ClusterRoleBinding` within Kubernetes, then map the IAM identity in `aws-auth` to a Kubernetes group that is bound to your custom role. This allows fine-grained control over what specific users or roles can do within the cluster.

**Q: My `kubeconfig` keeps getting overwritten or becomes messy with multiple clusters. How do I manage this?**
**A:** `aws eks update-kubeconfig` by default adds or updates the context in `~/.kube/config`. To manage multiple clusters more cleanly:
1.  Use the `--alias` flag: `aws eks update-kubeconfig --name clusterA --region us-east-1 --alias my-dev-clusterA` and `aws eks update-kubeconfig --name clusterB --region us-west-2 --alias my-prod-clusterB`. This creates distinct context names.
2.  Use separate `kubeconfig` files: Generate `kubeconfig` files into different locations (e.g., `aws eks update-kubeconfig --name my-cluster --region us-east-1 --kubeconfig ~/.kube/config-my-cluster`). Then, specify which file to use with the `KUBECONFIG` environment variable (e.g., `KUBECONFIG=~/.kube/config-my-cluster kubectl get nodes`) or by merging them.

## Related Errors
*(none)*