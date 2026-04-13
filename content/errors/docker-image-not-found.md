# Docker pull – image not found (manifest unknown)
> Encountering "Docker pull – image not found (manifest unknown)" means the specified Docker image or tag does not exist in the registry; this guide explains how to fix it.

## What This Error Means

When you encounter the `docker pull – image not found (manifest unknown)` error, it signifies that the Docker daemon, after attempting to communicate with a Docker registry (like Docker Hub, Amazon ECR, Google Container Registry, or a private registry), could not locate the specific image manifest for the image name and tag you provided.

In simpler terms, Docker successfully connected to the registry, but when it asked for the blueprint (the "manifest") of the image you requested, the registry responded that it didn't have one for that exact name and tag. Docker images are composed of layers, and the manifest is essentially an index or table of contents for these layers, along with other metadata like architecture and operating system. If this manifest can't be found, the image doesn't exist at that reference point.

This error is distinct from network connectivity issues (e.g., "connection refused" or "timeout"), which would indicate Docker couldn't even *reach* the registry. Here, the registry itself is confirming the absence of the requested image.

## Why It Happens

The fundamental reason this error occurs is a mismatch between the image reference (repository name and tag) you're using in your `docker pull` command and what actually exists in the target Docker registry. Docker is very particular about exact image paths and tags. Even a single character difference or an incorrect case can lead to this "manifest unknown" response.

From my experience, this usually boils down to the request pointing to something that either never existed, was deleted, or is inaccessible due to misconfiguration. It's often a case of "the registry said 'I don't know that image/tag,' not 'I can't talk to you.'"

## Common Causes

Understanding the common culprits can significantly speed up troubleshooting:

1.  **Typo in Image Name or Tag:** This is, hands down, the most frequent cause. A simple spelling mistake in the repository name (e.g., `ubntu` instead of `ubuntu`) or an incorrect tag (e.g., `v1.0-release` instead of `v1.0.0-release`) will prevent Docker from finding the manifest. Image names and tags are often case-sensitive.
2.  **Incorrect or Non-Existent Image Tag:** Every Docker image has tags, with `latest` being the default if none is specified. If you try to pull `my-app:dev` and no tag named `dev` exists, or the `latest` tag isn't what you expect, you'll hit this error. Sometimes, specific version tags are deprecated or removed by image publishers. I've seen this in production when a build pipeline relied on an ephemeral tag that was cleaned up.
3.  **Image Not Pushed or Deleted from Registry:** The image you're trying to pull might have been built locally but never pushed to the remote registry, or it might have been pushed and subsequently deleted by an automated cleanup policy or a manual action.
4.  **Private Registry or Repository, Not Logged In:** If the image resides in a private repository (e.g., a private Docker Hub repository, AWS ECR, GCP GCR, Azure ACR, or a self-hosted registry), and your Docker client is not authenticated with appropriate credentials, the registry will not reveal the image's existence, leading to an "image not found" error, often with "manifest unknown" specifics.
5.  **Wrong Registry Specified or Implied:** By default, `docker pull` looks for images on Docker Hub. If your image is in a different registry (e.g., `my-private-registry.com/my-image`), you *must* specify the full registry path. Omitting it will cause Docker to look for `my-image` on Docker Hub, where it won't be found.
6.  **Network Issues (Less Common for this Specific Error):** While "manifest unknown" generally implies successful communication with the registry, highly restrictive firewalls, incorrect proxy settings, or DNS resolution problems *before* reaching the registry could, in rare cases, manifest in ways that prevent the initial manifest lookup. However, direct "connection refused" or "timeout" errors are more typical for network blocks.

## Step-by-Step Fix

Here’s a methodical approach to resolving the "manifest unknown" error:

1.  **Verify Image Name and Tag:**
    *   **Double-check for typos:** Carefully compare the image name and tag in your `docker pull` command against the correct reference. Even subtle differences in case (`MyApp` vs `my-app`) can matter.
    *   **Consult documentation:** If you're pulling a third-party image, refer to their official documentation or repository page for the exact image name and available tags.
    *   **Example:** If you're trying `docker pull myorg/myproject:v1.2.3`, ensure `v1.2.3` is the exact tag. It might be `1.2.3` or `v1.2.3-release`.

2.  **Check Available Tags in the Registry:**
    *   **Use the registry's web UI:** Most major registries (Docker Hub, ECR, GCR, ACR) provide a web interface where you can browse repositories and their available tags. This is often the quickest way to confirm an image's existence and correct tags.
    *   **Use registry-specific CLIs:** Cloud providers offer CLIs (e.g., `aws ecr describe-images`) to list available images and tags in your repositories.
    *   **Public images (Docker Hub example):** For public images on Docker Hub, you can sometimes use `curl` to list tags (though this is a bit advanced for basic troubleshooting and may require `jq` for parsing):
        ```bash
        curl -s "https://registry.hub.docker.com/v2/library/nginx/tags/list" | jq .tags[] | grep "alpine"
        ```
        This command would list tags for the official NGINX image and filter for those containing "alpine".

3.  **Authenticate to the Docker Registry:**
    *   If the image is in a private repository, you must be logged in. Use `docker login`.
    *   For Docker Hub:
        ```bash
        docker login
        # You will be prompted for your username and password.
        ```
    *   For other private registries (e.g., `my-private-registry.com`):
        ```bash
        docker login my-private-registry.com
        # You will be prompted for your username and password.
        ```
    *   Cloud registries have specific login methods (see "Environment-Specific Notes").

4.  **Specify the Correct Registry (if not Docker Hub):**
    *   Always prefix the image name with the full registry URL if it's not Docker Hub.
    *   **Incorrect:** `docker pull my-app:latest` (attempts to pull `my-app:latest` from Docker Hub)
    *   **Correct:** `docker pull my-private-registry.com/my-team/my-app:latest`

5.  **Consult Image Provider Documentation/Support:**
    *   If you're pulling a third-party image and have verified all the above, there might be specific instructions or prerequisites for that image. Sometimes an image is only available for certain architectures, or it might be behind an access restriction.

## Code Examples

Here are some concise, copy-paste ready examples illustrating common scenarios and fixes.

**Scenario 1: Incorrect Tag Specified**

```bash
# This command will likely fail with "manifest unknown" if '22.04.5' is not an existing tag
docker pull ubuntu:22.04.5
```

```bash
# Corrected command after checking available tags (e.g., on Docker Hub)
docker pull ubuntu:22.04
```

**Scenario 2: Pulling from a Private Registry Without Login**

```bash
# This command will fail if you are not logged in to my-private-registry.com
docker pull my-private-registry.com/my-org/my-app:v1.0
```

```bash
# Step 1: Login to the private registry
docker login my-private-registry.com
# Enter username: myuser
# Enter password:
# Login Succeeded

# Step 2: Now, pull the image
docker pull my-private-registry.com/my-org/my-app:v1.0
```

**Scenario 3: Omitting the Registry Name for a Non-Docker Hub Image**

```bash
# This assumes 'my-image:latest' exists on Docker Hub, which it likely doesn't
docker pull my-image:latest
```

```bash
# Corrected command, specifying the full registry path
docker pull gcr.io/my-gcp-project/my-image:latest
```

## Environment-Specific Notes

The nuances of handling image pulls can vary slightly depending on your environment.

*   **Cloud Registries (AWS ECR, GCP GCR, Azure ACR):**
    *   **Authentication:** These registries typically require specific CLI tools or IAM/RBAC configurations for login. For AWS ECR, for instance, you'd use:
        ```bash
        aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
        ```
        (Replace `us-east-1` with your region and `123456789012` with your AWS account ID). Similar commands exist for Azure and GCP.
    *   **Permissions:** Beyond being logged in, the identity performing the pull (your user, an IAM role, a service account) must have the necessary permissions to access the specific repository. For ECR, this includes actions like `ecr:BatchCheckLayerAvailability`, `ecr:GetDownloadUrlForLayer`, and `ecr:GetAuthorizationToken`. I've seen situations where the login was successful, but the *pull* failed because the associated role lacked permissions to the specific repository.
    *   **Image Path:** Cloud registry image paths are verbose. Always ensure you're using the full path including the region, account ID (for AWS), or project ID (for GCP/Azure). Example: `123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo/my-image:my-tag`.

*   **Local Development:**
    *   Most local development uses Docker Hub. The primary causes here are almost always typos in the image name or tag, or trying to pull a private image without logging in.
    *   If you're running a local Docker registry (e.g., for testing), ensure it's up, running, and accessible on the correct port, and that you're using the correct `localhost:port/image:tag` path.

*   **CI/CD Pipelines:**
    *   This is a common place for `manifest unknown` errors. Issues often stem from:
        *   **Stale Credentials:** The service account or pipeline runner's credentials for the Docker registry might have expired or been revoked.
        *   **Incorrect Image References:** Environment variables or parameters passed to the `docker pull` command within the pipeline might be incorrect or resolve to a non-existent tag. I've frequently encountered cases where a build tag didn't match the pushed tag.
        *   **Permissions:** Similar to cloud registries, the CI/CD agent or service principal needs explicit permissions to pull from the target repository.
    *   Always verify the logs of your CI/CD pipeline for the exact `docker pull` command being executed and any preceding authentication steps.

## Frequently Asked Questions

**Q: Is "manifest unknown" a network error?**
**A:** Generally, no. This error indicates that Docker successfully connected to the registry, but the requested image and tag combination was not found. If it were a pure network error, you'd typically see messages like "connection refused," "dial tcp: lookup registry.example.com," or "i/o timeout."

**Q: Why does `docker images` not show my image, even after a successful build?**
**A:** The `docker images` command lists images *locally* stored on your machine. When you run `docker pull`, you're attempting to retrieve an image from a *remote* Docker registry. If you've just built an image and haven't tagged it or pushed it to a remote registry, `docker pull` won't find it in a remote location because it only exists locally.

**Q: Can proxy settings cause this error?**
**A:** Indirectly. If your proxy settings are misconfigured to the point that Docker cannot reach the registry *at all*, you would typically see a connection-related error. However, if a proxy is configured but is somehow corrupting the HTTP requests or responses for manifest retrieval, it *could* theoretically lead to a "manifest unknown" error, although this is far less common than simple typos or authentication issues.

**Q: How do I find all available tags for an image in a registry?**
**A:** The most straightforward way is to use the web interface of the Docker registry (e.g., Docker Hub, AWS ECR console). For Docker Hub, you can navigate to the image page, and it will list all available tags. Programmatically, it depends on the registry's API; for public Docker Hub images, a `curl` command to `https://registry.hub.docker.com/v2/library/<image_name>/tags/list` can list tags.

## Related Errors