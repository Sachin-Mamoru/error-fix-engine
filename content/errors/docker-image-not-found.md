# Docker pull – image not found (manifest unknown)
> Encountering "Docker pull – image not found (manifest unknown)" means the specified Docker image or tag does not exist in the registry; this guide explains how to identify and resolve the issue.

## What This Error Means

When you execute a `docker pull` command and receive the error `manifest unknown`, it signifies that the Docker daemon attempted to retrieve the image's "manifest" from the specified registry, but the registry reported that it could not find this manifest. An image manifest is essentially a JSON document that describes the image, including its layers, architecture, operating system, and often refers to other manifests for different platforms (e.g., `amd64`, `arm64`).

In simpler terms, this error is the registry's way of saying: "I looked for an image named exactly that, with that tag, and I couldn't find its blueprint." It doesn't mean your Docker client is misconfigured; it means the target image doesn't exist at the location and with the identifier you provided.

## Why It Happens

This error primarily occurs because the image or tag you're trying to pull either genuinely does not exist, or Docker cannot correctly locate it in the intended registry. It’s fundamentally an identity issue – Docker is trying to find something that isn't where it expects it to be, or isn't named what it's looking for. In my experience, it's often a simple oversight rather than a deep technical problem.

## Common Causes

Identifying the root cause is the first step to a quick resolution. Here are the most frequent culprits I've encountered:

1.  **Typos in Image Name or Tag:** This is by far the most common reason. A slight misspelling in the image name (e.g., `ngnix` instead of `nginx`) or tag (e.g., `lates` instead of `latest`, `v1.0` instead of `1.0.0`) will lead to this error.
2.  **Incorrect Tag Specified:** The image might exist, but the specific tag you're requesting does not. For instance, an application might be versioned `1.2.3` but you attempt to pull `v1.2.3`. Or perhaps a `latest` tag was updated, and you're trying to pull a now-deprecated tag.
3.  **Image or Tag Deleted from Registry:** Sometimes, older image tags are pruned from registries to save space, or an entire image repository might be removed. If the image was pulled manually by an administrator or through an automated cleanup policy, it simply won't be there anymore.
4.  **Private Registry Authentication Issues:** If the image is hosted on a private registry (e.g., Docker Hub private repositories, AWS ECR, Google Container Registry, Azure Container Registry), you must be authenticated. If you haven't run `docker login` or your credentials have expired, Docker won't be able to access the private image manifests.
5.  **Incorrect Registry Path:** You might be trying to pull an image that's in a private registry but forgetting to specify the full registry URL (e.g., `my-app/image` instead of `my-registry.example.com/my-app/image`). Docker defaults to Docker Hub if no registry is specified.
6.  **Network Connectivity Problems:** Less common, but if your machine cannot establish a connection to the Docker registry (due to firewall rules, DNS issues, proxy configuration, or general network outages), it won't be able to fetch the manifest.
7.  **Architecture Mismatch (Less Common):** If an image is specifically built for a different architecture (e.g., `arm64`) and your Docker client tries to pull it without a suitable multi-architecture manifest, or if you're trying to force a specific architecture that doesn't exist for a given tag, you might see this error.

## Step-by-Step Fix

Here's a systematic approach to troubleshoot and resolve the "manifest unknown" error:

1.  **Double-Check Image Name and Tag for Typos:**
    *   This is your first and often most effective step. Carefully compare the image name and tag in your command with the expected name and tag. Pay close attention to case sensitivity, hyphens, underscores, and versioning schemes (e.g., `v1.0` vs `1.0.0`).
    *   **Example:** You tried `docker pull myorg/my-app:v1.0`, but the correct tag is `myorg/my-app:1.0.0`.

2.  **Verify Image Existence in the Registry:**
    *   **For Docker Hub (public images):** Open a web browser and navigate to `hub.docker.com`. Use the search bar to find the image. Once you've found the repository, check the "Tags" tab to see all available tags and ensure the one you're looking for exists.
    *   **For Private Registries:** Log in to your private registry's web interface (e.g., AWS ECR console, GCR console, your company's Harbor instance) and verify the image repository and specific tag exist.

3.  **Ensure Proper Authentication (for Private Registries):**
    *   If the image is in a private registry, you need to authenticate your Docker client.
    *   Run `docker login <registry-url>`. For Docker Hub, this is `docker login`. For AWS ECR, it often involves a more complex command like `aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<your-region>.amazonaws.com`.
    *   After logging in, try the `docker pull` command again.

4.  **Specify the Full Registry Path:**
    *   If you're pulling from a registry other than Docker Hub, you *must* include the full registry domain.
    *   **Incorrect:** `docker pull my-app/backend:latest` (assumes Docker Hub)
    *   **Correct:** `docker pull myregistry.example.com/my-app/backend:latest`

5.  **Check Network Connectivity:**
    *   Confirm your machine can reach the registry.
    *   `ping` the registry URL (e.g., `ping hub.docker.com` or `ping myregistry.example.com`).
    *   If you're behind a corporate proxy, ensure your Docker daemon and client are configured to use it correctly. This often involves setting `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` environment variables for the Docker daemon process or configuring them in `/etc/docker/daemon.json`.

6.  **Inspect Docker Daemon Logs (Advanced):**
    *   If all else fails, checking the Docker daemon logs (`journalctl -u docker` on Linux systems using systemd) might reveal more detailed error messages or connectivity issues that aren't apparent from the client output. I've seen this in production when network segmentation or proxy issues were silently failing.

## Code Examples

Here are some common scenarios and their fixes, ready to copy-paste.

**1. Correcting a Typo in a Tag:**

```bash
# Initial attempt with a typo
docker pull myorg/my-image:lates
# Error: Error response from daemon: manifest unknown: manifest unknown

# Corrected tag
docker pull myorg/my-image:latest
```

**2. Logging into a Private Docker Registry (General Example):**

```bash
# Login to a custom registry
docker login myregistry.example.com
# You will be prompted for Username and Password.
# Once successful, retry your pull.

# Example with AWS ECR (requires AWS CLI configured)
# For specific region and account ID
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Then, pull the image using its full ECR URI
docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app/backend:v1.0
```

**3. Listing Available Tags (Public Docker Hub Image - using `docker search` and web UI):**

While `docker search` can show repositories, it doesn't list all tags. For comprehensive tag listing, the web UI is best. For programmatically listing tags, you'd typically query the registry API (which is more complex and varies by registry).

```bash
# Use docker search to find repositories (doesn't list specific tags)
docker search nginx

# Example output might be:
# NAME                               DESCRIPTION                                     STARS     OFFICIAL   AUTOMATED
# nginx                             Official build of Nginx.                          18131     [OK]
# ...

# To find specific tags, you'd generally go to hub.docker.com/r/library/nginx/tags
# or for a custom registry, use its specific API or UI.
```

## Environment-Specific Notes

The "manifest unknown" error can manifest differently or require specific considerations depending on your environment.

*   **Local Development:**
    *   On your local machine, this error is almost always due to a typo in the image name or tag, or simply forgetting to `docker login` to a private registry.
    *   Ensure your `~/.docker/config.json` file contains valid credentials for any private registries. If you're switching between multiple private registries, ensure you've logged into the correct one recently.

*   **CI/CD Pipelines (e.g., Jenkins, GitLab CI, GitHub Actions):**
    *   This is a very common place to encounter "manifest unknown."
    *   **Authentication:** CI/CD runners typically don't have interactive logins. You must ensure that the CI/CD job has the necessary credentials injected (e.g., environment variables, `docker login` using tokens/secrets, or using specific cloud provider helpers like `aws ecr get-login-password`).
    *   **Image Path:** Verify that the image path in your CI/CD configuration (e.g., `Dockerfile`, deployment YAML, build script) precisely matches what's in the registry. Automated scripts can sometimes generate incorrect paths or tags.
    *   **Network Access:** Ensure the CI/CD runner's network security group or firewall rules allow outbound connections to the Docker registry's IP range or domain.

*   **Cloud Environments (e.g., Kubernetes, AWS ECS, Azure ACI, Google GKE):**
    *   When deploying containers to orchestration platforms, this error often appears in the pod/task logs as an `ImagePullBackOff` event or similar.
    *   **Kubernetes:**
        *   **`imagePullSecrets`:** For private registries, Kubernetes needs `imagePullSecrets` configured in your Pod/Deployment manifest to provide credentials. The `image` path in your deployment must match the full registry URL.
        *   **Service Account Permissions (for ECR/GCR/ACR):** If using cloud provider registries like ECR, GCR, or ACR, ensure the Kubernetes Node's IAM role (for EKS, GKE) or the Pod's Service Account (with IRSA on EKS, Workload Identity on GKE) has permissions to pull from the respective registry.
        *   **Typos:** Still, check for typos in the image name and tag within your Kubernetes YAML manifests.
    *   **AWS ECS:**
        *   **Task Role Permissions:** The ECS Task IAM Role must have `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`, and `ecr:BatchCheckLayerStatus` permissions for the ECR repository.
        *   **Repository URI:** Ensure the `image` field in your task definition uses the correct, full ECR repository URI (e.g., `123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest`).
    *   **Azure Container Instances (ACI):**
        *   For private registries, you typically specify `imageRegistryCredentials` in your ACI deployment.

## Frequently Asked Questions

*   **Q: What does "manifest unknown" specifically refer to?**
    *   **A:** It refers to the image manifest, which is a JSON document describing the image's layers and metadata. The error means the registry couldn't find this specific manifest for the image name and tag you provided.

*   **Q: How can I view all available tags for a Docker image?**
    *   **A:** The most reliable way is to check the web interface of the Docker registry (e.g., `hub.docker.com` for public images, or your private registry's console). Some registries offer API endpoints you can query with `curl` to list tags, but these vary. `docker search` only lists repositories, not individual tags.

*   **Q: I'm getting "manifest unknown" in a Kubernetes cluster. What should I check first?**
    *   **A:** First, verify the exact image name and tag in your Kubernetes YAML manifest for any typos. If it's a private image, confirm that `imagePullSecrets` are correctly configured and referenced, or that the associated IAM role/Service Account has permissions to pull from the registry (for cloud provider registries like ECR/GCR).

*   **Q: Could a firewall or network issue cause this error?**
    *   **A:** Yes. If your machine or container runtime cannot establish a network connection to the Docker registry host, it won't be able to retrieve the image manifest, leading to this error. Check `ping` to the registry domain and any relevant firewall rules.

## Related Errors
*(none)*