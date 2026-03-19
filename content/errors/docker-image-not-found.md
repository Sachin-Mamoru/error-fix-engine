# Docker pull – image not found (manifest unknown)
> Encountering "image not found (manifest unknown)" means Docker cannot locate the specified image or tag in the registry; this guide explains how to fix it.

## What This Error Means

When you see the "image not found (manifest unknown)" error during a `docker pull` operation, it indicates that the Docker daemon, after contacting the specified registry, could not find the image manifest list or manifest for the image name and tag you provided. In simpler terms, Docker checked the registry, but it couldn't find the "blueprint" or "table of contents" for the specific image you asked for.

This isn't just a generic "file not found" message; it's specific to the registry's cataloging system. The registry either doesn't have any record of that image name or, more commonly, it has the image name but not the exact tag you requested.

## Why It Happens

This error primarily occurs because Docker cannot resolve the image identifier you've given it to an actual, existing image manifest within the target registry. The reasons can range from simple typographical errors to complex authentication or network issues, or even that the image truly doesn't exist where Docker is looking.

In my experience, it almost always boils down to one of two things: either the image name or tag is incorrect, or Docker doesn't have the necessary permissions to access a private registry where the image resides. Less frequently, but still worth considering, are network problems preventing Docker from reaching the registry at all.

## Common Causes

Understanding the common culprits can significantly speed up your troubleshooting process. Here are the scenarios I frequently encounter:

*   **Typographical Error in Image Name or Tag:** This is by far the most common cause. A simple misspelling in the image name (e.g., `ubntu` instead of `ubuntu`) or an incorrect tag (e.g., `v2.1` instead of `2.1.0`) will lead to this error. Docker image names are case-sensitive, especially repository paths.
*   **Incorrect Image Tag:** You might be requesting a tag that doesn't exist for the given image. For instance, if an image only has `latest` and `1.0.0` tags, requesting `2.0.0` will fail. The `latest` tag is also often misleading; it's simply a tag, not necessarily the most recent build, and it might not even exist for some repositories.
*   **Private Registry Authentication Failure:** If you're pulling from a private registry (like Docker Hub private repositories, Amazon ECR, Google Container Registry, Azure Container Registry, or a self-hosted one), and you're not logged in, or your credentials have expired, Docker won't be authorized to view or pull the image manifest. The registry will then respond as if the image doesn't exist to prevent unauthorized enumeration.
*   **Image or Tag Does Not Exist (Deleted/Never Pushed):** The image or the specific tag you're trying to pull might have been deleted from the registry or was never successfully pushed there in the first place. This can happen during cleanup operations or if a CI/CD pipeline failed to push.
*   **Incorrect Registry Domain:** You might be trying to pull from `myregistry.com/myimage` when the correct registry is `anotherregistry.com/myimage`. Or, you might be omitting the registry domain entirely for a non-Docker Hub image (e.g., pulling `myimage` expecting it from a custom registry without specifying `mycustom.registry/myimage`).
*   **Network Connectivity Issues:** Your Docker host might not be able to reach the registry due to firewall rules, proxy issues, DNS resolution failures, or general network outages. The `manifest unknown` error can sometimes mask a deeper network problem, as the initial connection might succeed, but the subsequent lookup fails.
*   **Proxy Configuration Problems:** If your environment requires a proxy to access external resources, Docker might not be correctly configured to use it, preventing it from reaching the registry.

## Step-by-Step Fix

Here's a systematic approach to resolve the "image not found (manifest unknown)" error. Work through these steps methodically.

1.  **Verify Image Name and Tag:**
    *   **Double-check spelling:** A simple typo is the most frequent culprit. Look for case sensitivity issues as well.
    *   **Confirm tag existence:** Visit the registry's website (e.g., Docker Hub, your private registry UI) and search for the image. Confirm that the exact tag you're trying to pull actually exists. If `latest` is failing, try a specific version tag.
    *   **Example:** If you're pulling `myuser/myimage:v1.0.0`, ensure both `myuser/myimage` and `v1.0.0` are correct.

2.  **Check Registry Authentication:**
    *   If the image is in a private repository, you *must* be logged in.
    *   Run `docker login <registry-domain>` (e.g., `docker login` for Docker Hub, `docker login my-ecr-repo.amazonaws.com` for ECR).
    *   Enter your username and password/token when prompted.
    *   If you recently changed your password or token, you might need to `docker logout` first and then `docker login` again to refresh credentials.

    ```bash
    # For Docker Hub:
    docker login

    # For a specific private registry (e.g., Amazon ECR):
    # Ensure you have AWS CLI configured and your ECR registry URL
    # Example using AWS ECR helper (requires aws-cli installed and configured)
    # $(aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com)
    # A more general example:
    docker login my-private-registry.com
    ```

3.  **Confirm Image Existence on Registry:**
    *   Manually search for the image on the registry website (e.g., `hub.docker.com` for public images, or your private registry's UI).
    *   Confirm the exact repository path and available tags. Sometimes an image might exist under a different namespace or repository name than you expected. I've seen this happen when teams refactor their image naming conventions.

4.  **Verify Full Registry Path (if not Docker Hub):**
    *   For images not on Docker Hub, you must specify the full registry domain.
    *   **Incorrect:** `docker pull myorg/myimage:mytag` (if `myorg` is not on Docker Hub).
    *   **Correct:** `docker pull myregistry.com/myorg/myimage:mytag`

5.  **Check Network Connectivity and DNS Resolution:**
    *   **Ping the registry:** Try `ping <registry-domain>` (e.g., `ping registry-1.docker.io` or `ping my-private-registry.com`). If it fails, you have a network issue.
    *   **Check DNS:** Use `nslookup <registry-domain>` or `dig <registry-domain>` to ensure your system can resolve the registry's IP address.
    *   **Firewall/Proxy:** Ensure no local or corporate firewalls are blocking outgoing connections to the registry's domain and ports (typically 443 for HTTPS). If you are behind a corporate proxy, ensure Docker's proxy settings are correctly configured (often in `/etc/docker/daemon.json` or Docker Desktop settings).

6.  **Review Docker Daemon Configuration (Proxies, Insecure Registries):**
    *   If you're using an internal or self-signed certificate registry, you might need to configure Docker as an "insecure-registry" in `/etc/docker/daemon.json` (for Linux) or Docker Desktop settings. This should be done with caution and only for trusted internal registries.
    *   For proxy settings, ensure `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` environment variables are set correctly for the Docker daemon, or configured via `daemon.json`.

7.  **Clear Docker Cache (less common but can help):**
    *   While less likely for `pull` operations (which primarily involve fetching new data), sometimes local metadata can become stale.
    *   `docker system prune` can clean up stopped containers, unused networks, dangling images, and build cache. Use with caution as it removes resources.

## Code Examples

Here are some concise, copy-paste ready examples for common scenarios.

**1. Basic `docker pull` command:**

```bash
# Pull an official image from Docker Hub with a specific tag
docker pull ubuntu:22.04

# Pull an image from Docker Hub with the 'latest' tag (often default if no tag specified)
docker pull nginx:latest

# Pull a public image from a custom registry (e.g., Google Container Registry)
docker pull gcr.io/google-samples/hello-app:1.0
```

**2. Logging into a Docker Registry:**

```bash
# Log into Docker Hub (default)
docker login

# Log into a specific private registry
docker login my-private-registry.com
```

**3. Searching for an image (on Docker Hub):**

```bash
# Search for images containing 'nginx' on Docker Hub
docker search nginx
```

**4. Logging out of a Docker Registry:**

```bash
# Log out of Docker Hub (default)
docker logout

# Log out of a specific private registry
docker logout my-private-registry.com
```

## Environment-Specific Notes

The "image not found (manifest unknown)" error can manifest differently or require specific considerations based on your environment.

*   **Cloud Environments (Kubernetes, AWS ECS, Azure AKS, GCP GKE):**
    *   **IAM Roles/Service Accounts:** When running containers in cloud orchestration platforms, container runtimes (like `kubelet` or `containerd` in Kubernetes, or ECS agent) don't typically use `docker login`. Instead, they rely on IAM roles or service accounts attached to the worker nodes or tasks. Ensure these roles have explicit permissions to pull images from the relevant container registry (e.g., `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`, `ecr:BatchCheckLayerAvailability` for AWS ECR).
    *   **ImagePullSecrets (Kubernetes):** For private registries outside of the cloud provider's native one (e.g., pulling from Docker Hub private repos into EKS), you'll need to configure `imagePullSecrets` in your Kubernetes deployments.
    *   **VPC Endpoints/Private Link:** If your worker nodes are in a private subnet and need to pull from a public registry, ensure proper NAT Gateway or VPC Endpoint configurations are in place to allow egress traffic. For AWS ECR, using VPC Endpoints for ECR services is a best practice.
    *   **Cross-Account Access:** I've encountered this when trying to pull images from an ECR repository in a different AWS account. Ensure the ECR repository policy explicitly grants pull permissions to the IAM role of the consumer account.

*   **Docker Desktop (macOS/Windows):**
    *   **Proxy Settings:** Docker Desktop has its own network settings. If you're behind a corporate proxy, ensure you configure the HTTP/HTTPS proxy settings directly within Docker Desktop's preferences.
    *   **DNS Settings:** Similar to proxy settings, you might need to configure custom DNS servers within Docker Desktop if your local network's DNS resolver is struggling to find registry domains.
    *   **VPN Interference:** A common issue I've seen is VPNs interfering with Docker Desktop's network. Try temporarily disabling your VPN to see if it resolves the issue.

*   **Local Development Machines (Linux, macOS CLI):**
    *   **Local DNS/`resolv.conf`:** Verify your system's DNS configuration (`/etc/resolv.conf` on Linux) is correct and points to valid DNS servers.
    *   **Firewall Rules:** Your local firewall (e.g., `ufw` on Linux, macOS firewall) might be blocking outgoing connections to the Docker registry.
    *   **Corporate Network/VPN:** Corporate networks often have strict firewalls, proxy servers, and sometimes even SSL inspection that can interfere with `docker pull` operations. Ensure your Docker client is configured to respect these. Using a VPN can sometimes route traffic through a different path that bypasses necessary proxy configurations, leading to issues.

## Frequently Asked Questions

**Q: Can "image not found (manifest unknown)" mean I don't have permissions to pull?**
**A:** Yes, absolutely. For private repositories, if you are not properly authenticated or authorized, the registry will often respond with this error rather than explicitly stating "permission denied." This is a security measure to prevent information leakage about existing images.

**Q: Does the `latest` tag always refer to the most recent version of an image?**
**A:** Not necessarily. `latest` is just a tag, like any other (`v1.0`, `stable`, `dev`). It's up to the image publisher to decide which version `latest` points to. It *usually* points to the most recent stable build, but it can be out of date or even absent for some images. Always prefer specific version tags in production.

**Q: How do I pull an image from a custom private registry that isn't Docker Hub?**
**A:** First, you need to log into that specific registry using `docker login <registry-url>`. Then, when you pull the image, you must prefix the image name with the full registry URL, like `docker pull <registry-url>/<username>/<image-name>:<tag>`.

**Q: What if the image was just pushed to the registry, and I'm still getting this error?**
**A:** It's possible there's a slight delay in replication across the registry's internal systems, especially in geographically distributed registries. Give it a few moments and try again. More likely, though, is a typo in the image name or tag during the push operation, or a permission issue preventing you from seeing the newly pushed image.

**Q: I'm behind a corporate proxy. How do I configure Docker to work with it?**
**A:** For Docker CLI, you can set `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` environment variables for your Docker client and daemon. For Docker Desktop, there are specific proxy settings within its preferences pane. The Docker daemon itself might need configuration in `/etc/docker/daemon.json` for persistent proxy settings.

## Related Errors