# npm ERR! 404 Not Found – package not found in registry
> Encountering npm ERR! 404 means the package wasn't found in the registry; this guide explains how to fix it.

When you're working with `npm`, the Node Package Manager, and encounter the `npm ERR! 404 Not Found – package not found in registry` error, it signifies a straightforward yet often frustrating issue: the package `npm` is trying to fetch simply isn't available at the location it's looking. This is one of the most common errors I've seen developers face, and in my experience, it almost always boils down to a few key root causes.

## What This Error Means

At its core, `npm ERR! 404 Not Found` is an HTTP 404 status code coming from the package registry (usually `registry.npmjs.org` or a private alternative). It means the server received your request for a specific package but could not find the resource (the package) you were asking for. It's not an issue with your local `npm` client itself, but rather a communication problem with the remote repository. Your `npm` client is functional, but the package you or your project expects it to find isn't there, or can't be accessed.

## Why It Happens

This error typically indicates that `npm` failed to locate a package (or a specific version of a package) in the configured npm registry. The reasons can range from simple typos to complex network or authentication issues. It's a clear signal that the package path `npm` is following doesn't lead to a valid package resource on the server. Unlike a `500 Internal Server Error`, a `404` tells you the server is working fine, it just doesn't have what you're asking for at that specific URL.

## Common Causes

Here’s a breakdown of the most common scenarios that lead to `npm ERR! 404 Not Found`:

1.  **Typographical Errors in Package Name:** This is, by far, the most frequent culprit. A simple misspelling in your `package.json` file, during an `npm install <package-name>` command, or even within a dependency of a dependency, can lead to `npm` searching for a non-existent package. For example, `react-router-domm` instead of `react-router-dom`.
2.  **Case-Sensitivity Issues:** While `npm` itself is generally case-insensitive for package names, the registry or specific operating systems might have subtle differences. Always double-check the exact casing of the package name.
3.  **Package Has Been Unpublished or Removed:** Developers occasionally unpublish packages from the registry. If a package your project depends on is no longer available, `npm` will naturally return a 404. I've encountered this in legacy projects where a less popular dependency was removed.
4.  **Non-existent Package Version:** You might be requesting a version of a package that never existed, was unpublished, or hasn't been released yet. This often happens if `package.json` specifies a very specific version (e.g., `1.2.3`) that isn't available, or if a range (`^1.0.0`) cannot resolve to a valid existing version.
5.  **Private or Scoped Package Issues:**
    *   **Incorrect Registry:** If you're trying to install a private package (e.g., `@my-org/my-private-package`) or a scoped public package (e.g., `@angular/core`), `npm` might not be configured to look in the correct registry. Private packages are often hosted on internal registries (like Artifactory, Nexus, Verdaccio).
    *   **Authentication Failure:** Even if the registry URL is correct, if you lack the necessary authentication (e.g., an `npm` token or `npm login` session) to access a private package, the registry might effectively return a 404, denying access to a package it *does* host.
6.  **Custom npm Registry Misconfiguration:** Your `npm` client might be configured to use a private or mirror registry (e.g., `npm config get registry`) that either doesn't host the package you need, or is itself misconfigured or offline.
7.  **Network or Proxy Issues:** While less common for a `404` (which implies the server was reached but the resource wasn't found), if a corporate firewall, VPN, or proxy is interfering with `npm`'s ability to even *reach* the registry, it could manifest strangely, though usually you'd see network errors first. Still, it's worth checking if you're behind a restrictive network.
8.  **Corrupted `package-lock.json` or `node_modules`:** In rare cases, a corrupted `package-lock.json` file might point to a non-existent package version or a malformed package name, causing `npm` to search for something that isn't there.

## Step-by-Step Fix

Here’s a practical, step-by-step guide to troubleshooting and resolving `npm ERR! 404 Not Found`:

1.  **Verify Package Name and Version:**
    *   **Check `package.json`:** Carefully inspect your `dependencies` and `devDependencies` sections in `package.json` for any misspellings.
    *   **Check `npm install` command:** If you're running `npm install <package-name>`, ensure the name is correct.
    *   **Search npm registry:** Use `npm search <potential-package-name>` to confirm the package name and check available versions.
        ```bash
        npm search react-router-dom # Correct
        npm search react-router-domm # Incorrect
        ```
    *   **Check existing versions:** Visit `npmjs.com/package/<package-name>` to see available versions. Ensure the version you're requesting (either explicitly or via a version range in `package.json`) actually exists.

2.  **Inspect Your npm Registry Configuration:**
    *   Determine which registry `npm` is currently using:
        ```bash
        npm config get registry
        ```
    *   By default, this should be `https://registry.npmjs.org/`. If it's a custom URL, ensure it's correct and accessible. If you're expecting to use a private registry, verify the URL.

3.  **Authentication for Private/Scoped Packages:**
    *   If you're dealing with a private package or a scoped public package from a custom registry, ensure you're authenticated.
    *   For `npmjs.org`, run `npm login`.
    *   For private registries, ensure your `.npmrc` file (in your project root or home directory) contains the necessary authentication token. For example:
        ```
        # .npmrc example for a private registry
        @my-scope:registry=https://my-private-registry.com/npm/
        //my-private-registry.com/npm/:_authToken=YOUR_AUTH_TOKEN
        ```
        Replace `YOUR_AUTH_TOKEN` with your actual token. I've often seen expired or revoked tokens cause this issue in CI/CD.

4.  **Clear the npm Cache:**
    *   Sometimes, a corrupted entry in the local `npm` cache can lead to issues. Clearing it can resolve unexpected behavior.
        ```bash
        npm cache clean --force
        ```
    *   After clearing, try `npm install` again.

5.  **Remove `node_modules` and `package-lock.json`:**
    *   To ensure a fresh install, delete your `node_modules` directory and `package-lock.json` (or `npm-shrinkwrap.json`) file, then try installing again. This ensures `npm` resolves dependencies from scratch.
        ```bash
        rm -rf node_modules package-lock.json
        npm install
        ```

6.  **Check Network Connectivity and Proxy Settings:**
    *   Verify you can reach the registry URL.
        ```bash
        curl -I https://registry.npmjs.org/
        ```
        You should see an HTTP 200 OK or 301/302 redirect. If it fails, you have a network issue.
    *   If you're behind a corporate proxy, configure `npm` to use it:
        ```bash
        npm config set proxy http://your-proxy-server:port
        npm config set https-proxy http://your-proxy-server:port
        npm config set strict-ssl false # Only if absolutely necessary and you understand the security implications
        ```

7.  **Try a Specific, Known-Good Version:**
    *   If the issue is with a version range (e.g., `^1.0.0`), try explicitly installing a known existing version.
        ```bash
        npm install <package-name>@<specific-version>
        ```
    *   If this works, it indicates the original version or range was problematic.

8.  **Consult npm Status Page:**
    *   On rare occasions, the `npmjs.org` registry itself might be experiencing an outage. Check the official npm status page (status.npmjs.org) to see if there are any ongoing incidents.

## Code Examples

Here are some concise, copy-paste ready examples for common fixes:

**1. Correcting Registry for a Single Install (e.g., for a private package):**
```bash
npm install @my-scope/my-private-package --registry=https://my-private-registry.com/npm/
```

**2. Setting Global Registry (for all future npm commands):**
```bash
npm config set registry https://my-private-registry.com/npm/
# To revert to default:
# npm config set registry https://registry.npmjs.org/
```

**3. Clearing npm Cache and Reinstalling:**
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**4. Searching for a Package:**
```bash
npm search express # Search for a public package
npm view @angular/core versions # See all available versions for a scoped package
```

**5. Example `.npmrc` for Private Registry Authentication:**
Create or edit `.npmrc` in your project root or home directory (`~/.npmrc`):
```
@my-org:registry=https://npm.pkg.github.com/
//npm.pkg.github.com/:_authToken=ghp_YOUR_GITHUB_TOKEN
```
*Note: Replace `YOUR_GITHUB_TOKEN` with a GitHub Personal Access Token that has `repo` and `read:packages` scopes.*

## Environment-Specific Notes

The context in which you encounter this error often influences the solution.

*   **Local Development:** This is where you'll most often find typos, or perhaps a simple `npm cache clean` will do the trick. Network issues are usually straightforward to diagnose. The key here is checking your `package.json` and local `npm config`.
*   **CI/CD Pipelines (e.g., Jenkins, GitLab CI, GitHub Actions):** In my experience, 404s in CI/CD are almost always related to either an expired authentication token, an incorrectly configured `.npmrc` file not being available in the build environment, or network egress rules blocking access to the registry. Always verify:
    *   Environment variables supplying tokens are correctly passed.
    *   The `.npmrc` is correctly placed and configured within the build agent's workspace.
    *   The CI runner has outbound network access to the npm registry.
*   **Docker Containers:** When building Docker images that involve `npm install`, ensure your `Dockerfile` correctly copies any necessary `.npmrc` files *before* the `npm install` step. Also, verify that the container itself has DNS resolution and network access to the registry. I've seen `npm install` commands failing inside Docker builds because an `.npmrc` with authentication was missing from the build context.
    ```dockerfile
    # Dockerfile example
    COPY package*.json ./
    # If using private packages, ensure .npmrc is copied before npm install
    # COPY .npmrc ./
    RUN npm ci --prefer-offline --no-audit
    ```
*   **Cloud Environments (e.g., AWS Lambda, Azure Functions):** When deploying serverless functions or similar cloud resources, the deployment package must contain all necessary configuration files, including `.npmrc` if private packages are used. Network security groups or VPC configurations might also inadvertently block outbound traffic to external npm registries.

## Frequently Asked Questions

*   **Q: My CI build is failing with `npm ERR! 404`, but it works locally. Why?**
    **A:** This is a very common scenario. It almost certainly points to differences in environment variables, authentication tokens, `.npmrc` configuration, or network access between your local machine and the CI/CD environment. Double-check that your CI pipeline has access to the correct registry URL and the necessary authentication credentials for any private or scoped packages.

*   **Q: Can I install a package from a different registry for just one command?**
    **A:** Yes, you can override the registry for a single `npm install` command using the `--registry` flag: `npm install my-package --registry=https://my-custom-registry.com/`.

*   **Q: What if the package truly doesn't exist anymore and I can't find an alternative?**
    **A:** If a package has been permanently unpublished and has no suitable alternatives, you'll need to refactor your project to remove the dependency. This might involve rewriting functionality or finding a different approach. Before resorting to this, always confirm it's truly gone by checking `npmjs.com` and GitHub for forks or alternatives.

*   **Q: Is `npm` registry down? How can I check?**
    **A:** Check the official npm status page at `status.npmjs.org`. If the registry is experiencing issues, waiting for a fix is the only solution.

*   **Q: What's the difference between `package-lock.json` and `node_modules` in this context?**
    **A:** `package-lock.json` records the exact versions and sources (including registry URLs) of every package installed. `node_modules` is where the actual package files reside. If `package-lock.json` points to a non-existent package or version, or `node_modules` is corrupted, a `404` can occur during `npm install` as `npm` tries to resolve these definitions. Removing both forces a fresh resolution and download.

## Related Errors
*(none)*