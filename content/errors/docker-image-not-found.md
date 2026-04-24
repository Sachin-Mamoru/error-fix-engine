# Docker pull – image not found (manifest unknown)
> Encountering Docker pull – image not found (manifest unknown) means the requested image or tag couldn't be located in the specified registry; this guide explains how to fix it by verifying image names, tags, and registry access.

## What This Error Means

When you execute a `docker pull` command and encounter the error `Error response from daemon: manifest unknown: manifest unknown`, it signifies that Docker was unable to locate the image manifest for the specified image name and tag in the target registry. The "manifest" is essentially a JSON document that describes the image, including its layers, architecture compatibility, and other metadata. If Docker can't find this manifest, it means the image as you've requested it either does not exist at all, or it doesn't exist under that specific tag or in that particular registry.

In my experience, this error is a definitive "resource not found" message, not typically a transient network issue. Docker successfully connected to the registry, but the registry itself reported that it doesn't have a record of the image manifest for the combination you provided.

## Why It Happens

This error primarily occurs because Docker cannot match your request to an existing image manifest within the specified registry. While seemingly complex, the underlying reasons are usually straightforward. It boils down to a mismatch between what you're asking for and what the registry actually hosts.

Common scenarios I've encountered that lead to this include:

1.  **Typographical Errors:** The most frequent culprit. A slight misspelling in the image name or tag.
2.  **Incorrect Image Tag:** You're requesting a tag that doesn't exist (e.g., `myapp:v2.0` when only `v1.0` is present, or using `latest` when a specific version is required).
3.  **Private Registry Access Issues:** You're trying to pull from a private registry without being properly authenticated, or your authentication has expired.
4.  **Image or Tag Deletion:** The image or specific tag you're looking for has been intentionally (or accidentally) removed from the registry.
5.  **Incorrect Registry Specification:** Docker defaults to Docker Hub (`docker.io`). If your image is on a different registry (e.g., a private company registry, AWS ECR, GCP GCR, Azure ACR), you must specify the full registry URL.
6.  **Architecture Mismatch (Less Common for this specific error):** While Docker usually handles architecture negotiation, sometimes an explicitly requested tag might only exist for a different architecture, leading to a "manifest unknown" if no compatible manifest is found.

## Common Causes

Let's break down the frequent causes into more actionable points:

*   **Typo in Image Name:** A classic. You might type `my-app` instead of `my_app`, or `ubuntu-server` instead of `ubuntu/server`. Double-check every character.
*   **Incorrect Image Tag:** Many images use specific version tags (e.g., `nginx:1.21.6`). If you try `nginx:stable` or `nginx:latest` and those tags aren't maintained or refer to a different version than you expect, you'll get this error. Some repositories might not even use `latest`.
*   **Missing or Expired Private Registry Authentication:** If the image resides in a private repository (like a company's artifact registry or a cloud provider's container registry), you must authenticate using `docker login` before you can pull. An expired session will also trigger this.
*   **Image Was Deleted or Never Pushed:** It's possible the image you're trying to pull was never successfully pushed to the registry in the first place, or it was pushed but later deleted. This happens, especially with development or test images.
*   **Wrong Registry URL:** Docker Hub is the default. If your image is on `myregistry.com/myuser/myimage:tag`, you *must* include `myregistry.com` in your pull command. Forgetting this means Docker searches Docker Hub, where it won't find your image.
*   **Network/Proxy Configuration Issues:** While less directly tied to "manifest unknown" (which implies the registry was reached), sometimes deeply embedded network issues or misconfigured proxies can prevent *any* communication with the registry, leading to this error if the initial registry lookup fails in a way that maps to "not found." However, you'd typically see a different network-related error in such cases.

## Step-by-Step Fix

Here's a systematic approach to troubleshoot and resolve the `manifest unknown` error.

### Step 1: Verify Image Name and Tag

This is the most crucial step. Re-examine the `docker pull` command you used.
*   **Check for typos:** Is the image name spelled exactly as it appears in the registry? Are there hyphens, underscores, or specific casing requirements?
*   **Confirm the tag:** Does the tag `v1.0`, `latest`, `dev`, etc., actually exist for that image? Many images specify exact version numbers.

**Action:** Go to the registry's UI (e.g., Docker Hub, AWS ECR console) and visually confirm the exact image name and the tag you intend to use.

```bash
# Example of what to check:
# If you ran: docker pull myorg/mywebapp:v1.0.0
# Is it actually 'myorg/my-webapp:1.0.0' or 'myorg/mywebapp:latest'?
```

### Step 2: Specify the Full Registry Path

If the image is not on Docker Hub, you *must* include the full registry domain.

**Action:** Add the registry URL to your command.

```bash
# For a public image on Docker Hub (often implicit, but good to be explicit for clarity):
docker pull docker.io/library/ubuntu:latest

# For a private registry:
docker pull myregistry.com/myorg/myimage:tag
```

### Step 3: Authenticate to Private Registries

If you're pulling from a private registry (like your company's own registry, or a cloud provider's ECR/GCR/ACR), you need to be logged in.

**Action:** Use `docker login` to authenticate.

```bash
# For Docker Hub or a generic private registry:
docker login myregistry.com
# You'll be prompted for Username and Password.

# For cloud registries, authentication often involves a specific CLI command
# to get temporary credentials, then piping them to docker login.
# Example for AWS ECR (replace <REGION> and <AWS_ACCOUNT_ID>):
# aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
```

After successful login, try the `docker pull` command again.

### Step 4: Confirm Image Existence in the Registry

Sometimes, an image or tag genuinely doesn't exist anymore.

**Action:**
*   Check the registry's web interface or CLI tools to list available images and tags.
*   For Docker Hub, you can use `docker search <image-name>` for public images, but direct browser search is often more reliable for tags.
*   For private registries, consult your organization's documentation or the registry's GUI.

```bash
# Example for searching public images on Docker Hub:
docker search nginx
```

If the image or tag is truly missing, you'll need to find an alternative or investigate why it was removed.

### Step 5: Check Network and Proxy Configuration (Less Common)

While "manifest unknown" typically isn't a direct network error, an inability to reach *any* registry could sometimes lead to this.

**Action:**
*   **Verify internet connectivity:** Can you reach other websites or `ping google.com`?
*   **Check Docker daemon proxy settings:** If you're behind a corporate proxy, ensure Docker is configured to use it. This often involves editing `/etc/docker/daemon.json` (on Linux) or adjusting Docker Desktop settings.
    ```json
    {
      "proxies": {
        "http-proxy": "http://proxy.example.com:3128",
        "https-proxy": "https://proxy.example.com:3129",
        "no-proxy": "*.test.com,127.0.0.0/8"
      }
    }
    ```
    Remember to restart the Docker daemon after making changes.
*   **Check environment variables:** Ensure `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` are correctly set if Docker relies on them in your environment.

### Step 6: Review Docker Client Configuration

In rare cases, a misconfigured Docker client or credential helper could interfere.

**Action:**
*   Ensure your `~/.docker/config.json` isn't corrupt or pointing to incorrect credential helpers.
*   Try restarting your Docker daemon or Docker Desktop.

## Code Examples

Here are common `docker pull` scenarios and how to correctly execute them.

```bash
# Pulling a public image from Docker Hub with a specific tag
# (docker.io is the default registry, 'library/' is for official images)
docker pull docker.io/library/ubuntu:22.04

# Pulling a public image from Docker Hub using a shorter name (implicit docker.io/library/)
docker pull nginx:1.23.4-alpine

# Logging into a private registry
docker login myregistry.com
# Enter username and password when prompted.

# Pulling an image from a private registry after authentication
docker pull myregistry.com/myorg/my-app:development

# Example for logging into AWS ECR (replace <REGION> and <AWS_ACCOUNT_ID>)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Listing local images to verify if it was already pulled (or if a similar one exists)
docker images
```

## Environment-Specific Notes

The "manifest unknown" error can present slightly differently or require specific considerations depending on your environment.

*   **Cloud Container Registries (AWS ECR, GCP GCR, Azure ACR):**
    *   **Authentication:** This is often the biggest hurdle. These registries require specific authentication flows, usually involving their respective cloud CLIs (`aws ecr`, `gcloud auth`, `az acr login`) to obtain temporary credentials or configure Docker's credential helper. Simply running `docker login` with a username/password usually won't work out-of-the-box. I've seen this in production many times where a CI/CD pipeline fails because the IAM role's permissions or token expired.
    *   **Permissions:** Beyond authentication, the IAM user or role performing the pull needs the correct permissions to access the registry and the specific repository. For ECR, this includes actions like `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`, `ecr:BatchCheckLayerAvailability`.
    *   **Region:** Ensure the registry URL explicitly includes the correct region (e.g., `123456789012.dkr.ecr.us-west-2.amazonaws.com`). Pulling from `us-east-1` when the image is in `us-west-2` will result in "manifest unknown."

*   **Docker Desktop (Local Development):**
    *   **Credential Helper:** Docker Desktop typically manages credentials for Docker Hub smoothly. For other private registries, ensure the credential helper (if configured) is working correctly.
    *   **VPN/Proxy:** If you're using a corporate VPN or local proxy, ensure Docker Desktop's network settings are configured to respect them. Sometimes, local DNS issues can also contribute.

*   **Local Development with `docker-compose`:**
    *   **`image` field:** The `image` field in your `docker-compose.yml` file is prone to the same typos or incorrect tag issues as direct `docker pull` commands. Double-check its value.
    *   **Build vs. Pull:** Ensure you intend to *pull* the image and haven't accidentally configured `docker-compose` to *build* it locally from a non-existent `build` context, or vice-versa.

## Frequently Asked Questions

**Q: Is `manifest unknown` always a network error?**
A: No, in my experience, it's very rarely a direct network connectivity error in the sense of "cannot reach host." It almost universally means Docker *could* communicate with the registry, but the registry reported that the requested image name and tag combination simply does not exist. If there were a connectivity issue, you'd typically see a different error like "connection refused" or "timeout."

**Q: Can a deleted image cause this error?**
A: Absolutely. If an image, or a specific tag of an image, has been removed from the registry (either intentionally or accidentally), any subsequent `docker pull` attempts for that image and tag will result in the `manifest unknown` error.

**Q: I'm using a cloud registry (e.g., ECR). How do I ensure I'm pulling from the correct region?**
A: The region is a critical part of the registry URL for cloud providers. For ECR, for example, it's `[AWS_ACCOUNT_ID].dkr.ecr.[REGION].amazonaws.com`. You must ensure your `docker login` command and subsequent `docker pull` command both specify the correct, full regional URL where your image is hosted.

**Q: What if I'm behind a corporate proxy?**
A: You need to configure the Docker daemon to use your proxy. This is typically done by editing the `daemon.json` file (e.g., `/etc/docker/daemon.json` on Linux) and adding proxy settings for `http-proxy`, `https-proxy`, and `no-proxy`. After modifying, you must restart the Docker daemon. Docker Desktop has proxy settings within its GUI.

**Q: My image was working yesterday, but today I get `manifest unknown`. What happened?**
A: This scenario strongly suggests that the image or the specific tag you were using has been deleted, renamed, or modified in the registry since your last successful pull. This often happens in development environments where images are frequently cleaned up or overwritten. Check the registry's audit logs or consult with the team responsible for managing that registry.

## Related Errors