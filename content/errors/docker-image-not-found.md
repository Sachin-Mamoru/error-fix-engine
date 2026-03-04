# Docker pull – image not found (manifest unknown)
> Encountering "Docker pull – image not found (manifest unknown)" means the specified Docker image or tag does not exist in the registry; this guide explains how to fix it.

## What This Error Means

When you execute a `docker pull` command and receive an error message like `Error response from daemon: manifest unknown: manifest unknown`, it signifies that the Docker daemon could not locate the requested image manifest on the remote registry. In simpler terms, Docker tried to find the metadata for the specific image name and tag you provided, but it wasn't there.

This error is distinct from network connectivity issues or authentication failures. While those can prevent Docker from *reaching* the registry, `manifest unknown` specifically indicates that the registry was reachable, but it couldn't find the requested resource (the image's manifest, which describes its layers and architecture) within its catalog. It's akin to asking for a specific book by title and edition number at a library, and the librarian confirming the library is open, but that particular book simply isn't on any shelf, or was never cataloged under that exact identifier.

## Why It Happens

This error primarily arises when the Docker client's request for an image doesn't match an existing entry in the target Docker registry. The "manifest unknown" part points directly to the image's metadata not being found. It's a clear signal that the name, the tag, or the entire path to the image is incorrect or no longer valid.

I've seen this happen across various environments, from local development machines to production CI/CD pipelines. It's a common stumbling block, often caused by simple oversight, but sometimes indicating a deeper issue with image management or registry configuration.

## Common Causes

In my experience, the `manifest unknown` error usually boils down to one of these common scenarios:

1.  **Typo in Image Name or Repository:** This is by far the most frequent cause. A small misspelling in the image name (e.g., `ubntu` instead of `ubuntu`), or an incorrect repository name (e.g., `myrepo/nginx` instead of `myorganization/nginx`), will lead to Docker not finding the manifest.
2.  **Incorrect or Missing Tag:** Images are versioned using tags. If you request a tag that doesn't exist for a given image (e.g., `myimage:v2.1` when only `v2.0` and `v2.2` exist), or if the `latest` tag isn't what you expect or has been deleted, you'll get this error. Docker will default to `latest` if no tag is specified, which can sometimes lead to unexpected results if `latest` isn't maintained.
3.  **Private Registry or Repository, No Authentication:** You might be trying to pull an image from a private registry (like Docker Hub private repositories, AWS ECR, Google Container Registry, Azure Container Registry, or a self-hosted Artifactory) without first logging in. Docker cannot see the manifest of a private image without proper authentication, resulting in the `manifest unknown` error.
4.  **Wrong Registry Specified:** By default, `docker pull` attempts to retrieve images from Docker Hub. If your image resides in a different registry (e.g., `gcr.io/my-project/my-image` or `myregistry.com/my-image`), you *must* prefix the image name with the full registry URL. Forgetting this prefix means Docker searches Docker Hub, where the image won't be found.
5.  **Image or Tag Deleted/Renamed:** The image or the specific tag you're looking for might have been removed or renamed in the registry. This can happen during cleanup, maintenance, or as part of a deprecation strategy. If it's gone, Docker can't find its manifest.
6.  **Network or DNS Issues (Less Common for *this* specific error):** While less common for a `manifest unknown` error (which implies reaching the registry but not finding the *resource*), fundamental network connectivity problems or DNS resolution issues preventing your Docker client from even *contacting* the registry could indirectly lead to this if the registry itself returns a malformed or empty response that Docker interprets as a missing manifest. More often, you'd see a connection timeout or refusal.

Understanding these common causes is the first step towards a quick resolution.

## Step-by-Step Fix

Here’s a methodical approach to troubleshoot and fix the `Docker pull – image not found (manifest unknown)` error. Work through these steps sequentially until your issue is resolved.

1.  **Verify the Image Name and Tag for Typos:**
    *   **Action:** Carefully re-read the `docker pull` command you are using. Check for any misspellings in the image name (e.g., `nginx` vs. `ngnix`) or the tag (e.g., `1.21.4-alpine` vs. `1.21.4-alpne`).
    *   **Tip:** Copy-pasting the image name and tag directly from the source (documentation, CI/CD script, another working machine) is often the safest bet.
    *   **Example:** If you intended `docker pull ubuntu:22.04` but typed `docker pull ubunto:22.04`, the latter will fail.

2.  **Confirm the Image Tag Exists:**
    *   **Action:** If you're pulling a specific tag, verify that this tag actually exists for the image.
        *   For Docker Hub, visit `hub.docker.com/r/<username>/<imagename>/tags` in your browser.
        *   For other registries (ECR, GCR, etc.), use their respective UIs or CLI tools to list available tags.
    *   **Tip:** Avoid relying solely on `latest`. While convenient, the `latest` tag can be updated frequently, or sometimes isn't even present. Explicitly specifying a versioned tag (e.g., `node:16-alpine`) is generally better practice.
    *   **Shell Example:** For publicly available images, you can sometimes use `docker search` to get a general idea, but for tags, direct registry access is better.
        ```bash
        # This shows general images, not specific tags
        docker search ubuntu
        ```

3.  **Ensure Correct Registry Prefix and Authentication:**
    *   **Action A (Registry Prefix):** If the image is not on Docker Hub, you *must* prefix the image name with the full registry URL.
        *   **Example for Google Container Registry (GCR):** `gcr.io/my-project/my-app:1.0`
        *   **Example for AWS Elastic Container Registry (ECR):** `123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo/my-app:1.0`
        *   **Example for a private self-hosted registry:** `myregistry.com:5000/my-app:1.0`
    *   **Action B (Authentication):** If the image is private (even on Docker Hub), you need to log in first.
        ```bash
        docker login <registry-url>
        # e.g., docker login registry.gitlab.com
        # e.g., docker login
        ```
        You will be prompted for your username and password. For cloud registries like ECR, GCR, ACR, the login process is often specific and involves generating a temporary password or using a cloud-provider specific CLI helper.
        ```bash
        # Example for AWS ECR (requires AWS CLI installed and configured)
        aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
        ```
        After successful login, retry your `docker pull` command.

4.  **Check for Image Deletion or Renaming:**
    *   **Action:** If you're certain the image name, tag, and registry are correct, it's possible the image or specific tag has been removed or renamed in the registry.
    *   **Tip:** Consult with the image maintainer, your team's DevOps engineers, or the documentation for the service providing the image to confirm its current status and correct path.

5.  **Verify Network Connectivity (Less Common for "manifest unknown", but worth a quick check):**
    *   **Action:** Ensure your machine has network access to the Docker registry.
    *   **Shell Example:** Ping the registry URL or try to access it via `curl` (though `curl` won't show the image content directly without authentication, it can confirm network path).
        ```bash
        ping hub.docker.com
        curl -I https://hub.docker.com/v2/ # Check for HTTP response
        ```
    *   **Troubleshooting:** If these fail, investigate your local network, firewall rules, or DNS configuration.

## Code Examples

These examples demonstrate correct syntax and common commands used when troubleshooting `manifest unknown` errors.

**1. Basic `docker pull` with a specific tag (public image):**
```bash
docker pull ubuntu:22.04
```

**2. Pulling from a custom registry (e.g., Google Container Registry):**
```bash
docker pull gcr.io/my-project-id/my-application:v1.2.3
```

**3. Logging into Docker Hub (for private repositories):**
```bash
docker login
# You will be prompted for Username and Password
```

**4. Logging into a specific private registry (e.g., GitLab Container Registry):**
```bash
docker login registry.gitlab.com
# Enter your GitLab username and Personal Access Token (PAT)
```

**5. Logging into AWS ECR using `aws cli` for credentials:**
```bash
# Replace 123456789012 with your AWS account ID
# Replace us-east-1 with your ECR region
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

**6. Searching for an image on Docker Hub (general search, not tag-specific):**
```bash
docker search nginx
```

## Environment-Specific Notes

The troubleshooting steps remain largely the same, but the nuances of authentication and registry access can differ significantly across environments.

*   **Cloud Registries (AWS ECR, Google Container Registry, Azure Container Registry):**
    *   **Authentication:** This is often the biggest difference. You usually don't use a simple username/password you set. Instead, you'll rely on cloud-provider specific tools to generate temporary credentials or use IAM roles. For example, AWS ECR requires the AWS CLI to generate a password, and GCR/ACR integrate with their respective cloud authentication mechanisms. Ensure your local machine or CI/CD runner has the correct IAM permissions to *read* from the registry. I've seen this in production when an old IAM role's permissions weren't updated after a migration, leading to `manifest unknown`.
    *   **Repository Naming:** Cloud registries often enforce specific naming conventions and path structures, including project IDs or account IDs as part of the full image path. Double-check these.
    *   **Region:** Ensure you are targeting the correct region for your cloud registry. Forgetting `us-east-1` or `eu-west-2` in your ECR path is a common mistake.

*   **Local Development:**
    *   **Focus on Typos & Tags:** When working locally, the most common culprits are simple typos in the image name or an incorrect tag. You have direct control over your environment, so network issues are usually easier to diagnose than in a complex CI/CD setup.
    *   **`docker login`:** If you're pulling a private image, confirm you're logged into the correct registry. Your `~/.docker/config.json` file stores your login credentials.

*   **CI/CD Pipelines (Jenkins, GitLab CI, GitHub Actions, Azure DevOps):**
    *   **Automated Authentication:** This is where authentication gets critical. Your CI/CD runner needs a non-interactive way to log into the registry. This usually involves:
        *   **Environment Variables:** Passing registry username/password or access tokens as secure environment variables.
        *   **Service Principals/IAM Roles:** Assigning an IAM role (AWS), Service Principal (Azure), or Service Account (GCP) with appropriate read permissions to the CI/CD runner itself.
    *   **Credential Expiry:** In my experience, expired temporary credentials or tokens are a frequent cause of `manifest unknown` in CI/CD. Ensure your credential generation or refresh mechanism is robust.
    *   **Image Cache:** While less relevant for `manifest unknown`, CI/CD runners often have clean environments, meaning they don't have a local image cache that might mask issues. This means any pull command is a fresh attempt to reach the registry.

## Frequently Asked Questions

**Q: What's the difference between `manifest unknown` and `repository does not exist`?**
**A:** `repository does not exist` typically means Docker could not find the *repository itself* within the registry. This is often due to a major typo in the repository name or if it's a private repository you haven't authenticated to at all. `manifest unknown`, however, suggests that Docker found the repository, but couldn't find the *specific image tag's metadata* within that repository. It's a more granular error.

**Q: Why does `docker pull myimage:latest` sometimes fail with `manifest unknown`?**
**A:** Even if an image exists, the `latest` tag might not exist or might have been explicitly removed by the image maintainer. While `latest` is a common convention, it's just another tag. If `myimage` only has tags `v1.0` and `v2.0`, pulling `myimage:latest` will fail if no such `latest` tag was ever pushed or if it was deleted. Always verify available tags.

**Q: How can I find the correct image names and tags for public images?**
**A:** For public images, the best source is the official documentation for the software you're trying to use (e.g., Node.js Docker documentation, Nginx Docker documentation). For Docker Hub images, visit `hub.docker.com` and search for the image. The "Tags" tab will list all available tags.

**Q: I'm sure the image exists and I'm logged in, what else could it be?**
**A:** If you've exhausted all other options, consider these rare cases:
    1.  **Registry Glitch:** A temporary outage or misconfiguration on the registry side.
    2.  **Proxy Issues:** If you're behind a corporate proxy, it might be interfering with Docker's communication, though this usually manifests as connection errors rather than `manifest unknown`.
    3.  **Local Docker Daemon Issue:** Restarting your Docker daemon (`sudo systemctl restart docker` on Linux, or via Docker Desktop UI) can sometimes resolve transient issues.

## Related Errors