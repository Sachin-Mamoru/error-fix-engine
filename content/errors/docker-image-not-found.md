# Docker pull – image not found (manifest unknown)
> Encountering "Docker pull – image not found (manifest unknown)" means the specified Docker image or tag does not exist in the registry; this guide explains how to identify and fix the underlying issue.

## What This Error Means

When you execute a `docker pull` command and receive the error "image not found (manifest unknown)", it signifies that the Docker client attempted to retrieve metadata about the specified image and tag from a registry, but the registry reported that it could not locate a manifest list or manifest for that particular combination.

In simpler terms, the Docker registry you're interacting with has no record of the image name and tag you provided. It's not just a generic "not found" error; "manifest unknown" specifically indicates that the registry couldn't even find the descriptive information (the manifest) that tells Docker how to pull the image layers. This typically means the image, or at least that specific tag of the image, truly doesn't exist at the requested location or you don't have permission to see it.

## Why It Happens

This error primarily occurs when the Docker client's request for an image cannot be fulfilled by the target registry. The registry, after performing its internal lookup, determines there's no entry corresponding to the image name and tag combination. It's akin to asking for a specific book title and edition at a library, and the librarian reports that no such book exists in their catalog, or that edition was never published.

I've seen this in production when teams migrate images, delete old tags, or simply make a typo during a deployment. The `manifest unknown` part is crucial because it points to an issue at the registry level with the image's existence or visibility, rather than a network connectivity problem (though network issues can sometimes mask the root cause).

## Common Causes

Based on my experience troubleshooting this, here are the most frequent reasons you'll encounter the "image not found (manifest unknown)" error:

1.  **Typographical Errors in Image Name or Tag:** This is by far the most common cause. A simple typo in the image name (`ngnix` instead of `nginx`), an incorrect registry prefix, or a wrong tag (`latestt` instead of `latest`, `v1.2` instead of `1.2.0`) will lead to the registry failing to locate the manifest.
2.  **Incorrect or Missing Tag:** The image exists, but the specific tag you're trying to pull either never existed, was deleted, or you've made a mistake in specifying it. Remember that if you don't specify a tag, Docker defaults to `latest`. If `latest` doesn't exist for that image, you'll get this error. Some images might not use `latest` or might have it pointing to an old, irrelevant version.
3.  **Image Doesn't Exist in the Specified Registry:** You might be trying to pull an image that only exists in a different registry (e.g., trying to pull from Docker Hub when it's an AWS ECR image), or the image itself was never pushed to the registry you're querying.
4.  **Private Repository Access Issues:** If the image is in a private registry (e.g., Docker Hub private repository, Google Container Registry, AWS ECR, Azure Container Registry), and you haven't authenticated correctly, or your credentials have expired, the registry will respond as if the image doesn't exist, preventing access to its manifest. It's a security measure to not reveal information about private images to unauthorized users.
5.  **Image or Tag Was Deleted:** The image or specific tag might have been intentionally or unintentionally removed from the registry. This often happens during cleanup operations or when an image becomes deprecated.
6.  **Network or DNS Issues (Less Common for *Manifest Unknown*):** While less typical for this specific error message (which usually indicates the registry *responded* but found nothing), underlying network connectivity problems or DNS resolution failures could prevent your Docker client from reaching the registry in the first place. However, you'd usually see a different error like "connection refused" or "timeout" in those cases. If the registry *is* reached but returns this error, it's almost always content-related.

## Step-by-Step Fix

Addressing the "image not found (manifest unknown)" error usually involves a systematic check of your `docker pull` command and your environment.

### 1. Verify Image Name and Tag

This is your first and most critical step. Double-check every character.

*   **Syntax:** The standard format is `[registry_hostname/][namespace/]image_name[:tag]`.
*   **Case Sensitivity:** Image names and tags are often case-sensitive. `MyImage` is different from `myimage`.
*   **Tag Existence:** Confirm the tag you're using actually exists. Many images use semantic versioning (e.g., `1.0.0`, `2.3.1`) rather than just `latest`.

**Action:**
Carefully re-read your `docker pull` command. Compare it against the official documentation for the image, or consult your team's image manifest.

### 2. Check the Target Registry

Are you pulling from the correct registry? Docker Hub is the default. If your image is hosted elsewhere (e.g., ECR, GCR, ACR, or a private company registry), you *must* specify the full registry path.

**Action:**
Ensure your `docker pull` command includes the full registry hostname if it's not Docker Hub.
*   **Example (Docker Hub):** `docker pull nginx:latest`
*   **Example (AWS ECR):** `docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0`
*   **Example (Google Container Registry):** `docker pull gcr.io/my-project/my-app:v1.0`

### 3. Authenticate to Private Registries

If the image is in a private repository, you need to be logged in. An unauthenticated `pull` will often result in a `manifest unknown` error for private images, as the registry won't even reveal its existence without proper credentials.

**Action:**
Log in to the respective registry.

```bash
# For Docker Hub or generic private registries
docker login

# For AWS ECR (using AWS CLI helper)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# For Google Container Registry (gcloud helper)
gcloud auth configure-docker

# For Azure Container Registry
az acr login --name myacrregistry
```

After logging in, retry the `docker pull` command. If it still fails, verify your credentials or permissions for that registry. I've frequently encountered this in CI/CD pipelines where service accounts might have restricted permissions.

### 4. Search for the Image (or List Tags)

If you're unsure about the exact image name or available tags, you can try searching or using registry-specific tools.

**Action:**
*   **Docker Hub:**
    ```bash
    docker search my-image-name
    ```
    This helps confirm the base image name. To check available tags, you'd typically need to visit the image's page on Docker Hub (e.g., `hub.docker.com/r/library/nginx/tags`).
*   **Other Registries:** Most cloud providers have a web UI to browse images and tags. For example, in ECR, you can navigate to your repository and see all pushed tags. Some registries also expose API endpoints or CLI commands to list tags.

### 5. Clear Docker Cache (Less Common for this Error)

While `manifest unknown` usually points to the image not existing on the *registry*, a corrupted local cache can, in rare cases, lead to odd behavior. This is a low-probability fix for this specific error but can be part of a broader troubleshooting sequence.

**Action:**
```bash
docker system prune --all --force
```
**Caution:** This command will remove *all* stopped containers, unused networks, dangling images, and *all* build cache. Use with care.

### 6. Consult Upstream Documentation

If you're pulling a third-party image, refer to its official documentation. They will specify the correct image name, registry, and recommended tags. For internal images, consult your team's documentation or contact the image maintainer.

## Code Examples

Here are some concise, copy-paste ready examples showcasing correct usage and common scenarios.

### Correct `docker pull` from Docker Hub

```bash
docker pull nginx:1.21.6
docker pull ubuntu:latest
docker pull busybox
```
*(Note: `latest` is implied if no tag is specified, like `busybox`)*

### Correct `docker pull` from a Private Registry

```bash
# Example for AWS ECR
# First, log in (replace with your account ID and region)
# aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-internal-app:production

# Example for Google Container Registry
# First, log in: gcloud auth configure-docker
docker pull gcr.io/my-gcp-project/microservice-api:v2.5

# Example for a generic private registry
# First, log in: docker login registry.example.com
docker pull registry.example.com/team/data-processor:stable
```

### Searching for Images

```bash
# Search for images on Docker Hub
docker search postgres
```

### Common Typo Leading to Error

```bash
# This will likely fail with "manifest unknown" if the tag doesn't exist
docker pull my-custom-image:lastest

# Corrected command
docker pull my-custom-image:latest
```

## Environment-Specific Notes

The context in which you encounter this error can influence how you troubleshoot it, especially regarding authentication and image discovery.

### Cloud Registries (AWS ECR, Google Container Registry, Azure Container Registry)

*   **Authentication:** This is often the biggest difference. You usually don't use `docker login` directly with a username/password you set. Instead, you'll use cloud provider-specific CLI tools (`aws ecr get-login-password`, `gcloud auth configure-docker`, `az acr login`) which generate temporary credentials or configure Docker's authentication helper.
*   **IAM Permissions:** Even if you're logged in, your AWS IAM user/role, GCP service account, or Azure Service Principal needs explicit `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`, `ecr:GetRepositoryPolicy`, `ecr:DescribeImages` (for ECR) or equivalent permissions for the specific repository to pull images. I've often seen `manifest unknown` when a CI/CD pipeline's service account doesn't have `Pull` permissions on a new repository.
*   **Regionality:** Ensure your image is pushed to and pulled from the correct region (e.g., `us-east-1` for ECR).

### Local Development Environments (Docker Desktop/Engine)

*   **Default Registry:** Docker Desktop defaults to Docker Hub. If you're working with private registries, ensure you've performed `docker login` for each required registry.
*   **`~/.docker/config.json`:** This file stores your authentication tokens. Inspect it if you suspect credential issues.
*   **Network Proxies:** If you're behind a corporate proxy, Docker might need specific proxy configurations to reach external registries. This could manifest as connectivity issues before even getting to `manifest unknown`.

### CI/CD Pipelines (Jenkins, GitLab CI, GitHub Actions, Azure DevOps)

*   **Service Accounts/Principals:** Authentication here is almost always managed by service accounts, API keys, or temporary credentials. Ensure these accounts have the necessary permissions to pull from the target registry.
*   **Environment Variables:** Image names, tags, and registry URLs are often passed via environment variables. Typos or incorrect variable values are a common culprit.
*   **Credential Helpers:** CI/CD runners often use credential helpers (like `docker-credential-ecr-login` or similar for other cloud providers) which need to be correctly installed and configured in the pipeline's execution environment.
*   **Caching:** Some CI/CD systems cache Docker images. While this won't cause `manifest unknown` directly, it's worth noting if you're trying to pull a *new* version of an image after fixing the manifest issue.

### Kubernetes Environments

*   **`ImagePullBackOff`:** In Kubernetes, this error typically manifests as an `ImagePullBackOff` status for a Pod. The underlying event will often show "manifest unknown."
*   **ImagePullSecrets:** For private images, Kubernetes needs `imagePullSecrets` configured in the Pod or ServiceAccount. If these secrets are missing, incorrect, or don't have permission to the image, the `kubelet` will fail to pull the image and report `manifest unknown`.
*   **Typo in Pod/Deployment Spec:** Just like in the CLI, a typo in the `image:` field of your Pod, Deployment, or DaemonSet specification is a frequent cause.

## Frequently Asked Questions

**Q: Can network issues cause "manifest unknown"?**
**A:** While network issues can prevent your Docker client from reaching the registry entirely (leading to connection errors or timeouts), if the registry is reachable and *responds* with "manifest unknown," it almost always means the image or tag does not exist or you lack permission to see it. It's not a generic network connectivity error in that specific response.

**Q: How can I check what tags are available for an image?**
**A:** For Docker Hub images, visit `hub.docker.com/r/<image_owner>/<image_name>/tags`. For cloud registries (ECR, GCR, ACR), use their respective web console or CLI tools (`aws ecr describe-images`, `gcloud container images list-tags`). The `docker search` command only shows base image names, not specific tags.

**Q: I'm pulling a private image that I *know* exists. Why am I still getting this error?**
**A:** This strongly points to an authentication or authorization issue. Ensure you've logged into the registry correctly (`docker login` or equivalent cloud CLI command) and that your credentials have the necessary permissions to pull from that specific repository. Check for expired tokens or revoked access.

**Q: Does `docker build` ever cause this error?**
**A:** No, `docker build` itself does not cause "manifest unknown." This error occurs when the `docker client` attempts to *pull* an image from a registry. If your `Dockerfile` uses a `FROM` instruction with an image that doesn't exist, the *build process* will initiate a `docker pull` for that base image, and *that pull* operation would then fail with "manifest unknown."

**Q: What's the difference between "image not found" and "manifest unknown"?**
**A:** In the context of the Docker client, "image not found (manifest unknown)" is a very specific error message. You generally won't see a standalone "image not found" from the registry in this scenario. The "manifest unknown" part clarifies that the registry could not find the manifest list or manifest for the requested image/tag, meaning it has no metadata for it. It's a more precise way of saying the image, as requested, isn't there.

## Related Errors
*(none)*