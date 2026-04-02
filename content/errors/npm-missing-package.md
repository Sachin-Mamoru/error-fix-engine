# npm ERR! 404 Not Found – package not found in registry
> Encountering "npm ERR! 404 Not Found – package not found in registry" means npm couldn't locate the specified package in its configured registry; this guide explains how to fix it.

## What This Error Means

The `npm ERR! 404 Not Found – package not found in registry` error is a clear indication that the Node Package Manager (npm) client successfully connected to its configured registry (typically `https://registry.npmjs.org/`), but the specific package it attempted to fetch could not be located. The "404 Not Found" is an HTTP status code, signifying that the requested resource – in this case, a particular npm package – does not exist at the URL where the client tried to retrieve it from the server.

This error is distinct from network connectivity issues (e.g., `ETIMEDOUT` or `ECONNREFUSED`), which would indicate a failure to reach the registry server at all. Instead, a 404 error confirms that the npm registry server received the request but reported that the package itself, or the specific version requested, is unavailable. It’s a common hurdle, and in my experience, it's often simpler to fix than it initially appears.

## Why It Happens

At its core, this error occurs because the npm client is trying to download a package that, for one reason or another, isn't present in the location it's looking. This can range from a simple typo in the package name to more complex issues involving private registries, network configurations, or package deprecation. The npm client's request to the registry is like asking a librarian for a book by its exact title and author; if the book isn't on the shelves under that specific query, the librarian (the registry) will report it as not found.

## Common Causes

Based on my troubleshooting experience, the `npm ERR! 404 Not Found` error can stem from several common scenarios:

1.  **Typographical Errors:** This is by far the most frequent culprit. A simple misspelling in the package name within your `package.json` file or directly in the `npm install` command can lead to npm searching for a non-existent package. For example, `npm install react-router-dom` versus `npm install react-routerdom`.
2.  **Package Name Change or Deprecation:** Over time, package maintainers might rename their packages, split them into multiple packages, or even unpublish them entirely. If your project tries to depend on a package name that no longer exists or has been deprecated, you'll encounter a 404.
3.  **Incorrect Scoped Package Name:** Scoped packages begin with an `@` symbol (e.g., `@angular/core`, `@my-org/my-private-lib`). If the scope name is incorrect or misspelled, or if the package name within the scope is wrong, the registry won't find it.
4.  **Private Package Not Accessible:** If you're trying to install a package hosted on a private npm registry (e.g., Azure Artifacts, JFrog Artifactory, GitHub Packages) but your npm client is configured to use the public `npmjs.org` registry, or if you lack proper authentication to your private registry, you'll receive a 404. The public registry doesn't know about your private packages.
5.  **Wrong Registry Configuration:** Your `npm` client might be configured to use an incorrect or outdated registry URL. This often happens after working with private registries and forgetting to switch back, or if your `.npmrc` file is misconfigured.
6.  **Non-existent Package Version:** You might be requesting a specific version of a package that does not exist in the registry, even if other versions of the package do. For example, `npm install some-package@1.0.999` where `1.0.999` was never published.
7.  **Local npm Cache Corruption:** Although less common for a fresh 404, a corrupted or stale npm cache could theoretically lead to issues where npm tries to retrieve an outdated or incorrect package reference that no longer exists.
8.  **Proxy or VPN Interference:** In corporate environments, proxies or VPNs can sometimes intercept and misroute npm requests. While this more often leads to network-related errors, a misconfigured proxy might return a 404 if it fails to correctly forward the request to the actual registry.

## Step-by-Step Fix

Addressing the `npm ERR! 404 Not Found` error usually involves systematically checking the most common causes. Follow these steps:

1.  **Verify Package Name and Version:**
    *   **Check `package.json`:** Carefully inspect your `dependencies` and `devDependencies` for any misspellings.
    *   **Check your `npm install` command:** If you're running a direct install, double-check the command.
    *   **Search on `npmjs.com`:** Go to `https://www.npmjs.com/` and search for the package name exactly as it appears in your error or `package.json`. If it doesn't appear, or appears with a different spelling, you've found your issue.
    *   **Check available versions:** If you're requesting a specific version (e.g., `package@1.2.3`), use `npm view <package-name> versions` to see all published versions and ensure your requested version exists.

    ```bash
    # Example: Searching for a potentially misspelled package
    npm search my-pacakge # (should be 'my-package')

    # Example: Checking available versions for a package
    npm view react versions
    ```

2.  **Clear npm Cache:** A stale cache can sometimes cause issues. Clearing it forces npm to re-fetch package metadata.

    ```bash
    npm cache clean --force
    ```

    After clearing, retry your `npm install` command.

3.  **Inspect npm Registry Configuration:**
    *   Determine which registry npm is currently using:
        ```bash
        npm config get registry
        ```
    *   For public packages, this should ideally be `https://registry.npmjs.org/`. If it's pointing to a private registry or a different URL, and you're trying to install a public package, you'll get a 404.
    *   To set it back to the default public registry:
        ```bash
        npm config set registry https://registry.npmjs.org/
        ```
    *   Check for `.npmrc` files in your project directory or user home (`~/.npmrc`), as these can override global npm configurations.

4.  **Verify Private Package Access and Configuration:**
    *   If the missing package is a private one, ensure your npm client is configured to authenticate with your private registry. This typically involves:
        *   Having the correct registry URL set for the scope: `npm config get @scope:registry`
        *   Being logged in: `npm whoami --registry https://your-private-registry.com`
        *   Ensuring an authentication token is present in your `.npmrc` file (either globally or in the project root). In my experience, forgetting to `npm login` or having an expired token is a common cause here.

    ```ini
    # Example .npmrc for a private registry
    @my-org:registry=https://my-private-registry.com/npm/
    //my-private-registry.com/npm/:_authToken=npm_YOUR_AUTH_TOKEN
    ```

5.  **Check for Proxy or VPN Settings:**
    *   If you're behind a corporate proxy or using a VPN, ensure npm is correctly configured to use it.
        ```bash
        npm config get proxy
        npm config get https-proxy
        ```
    *   If these are unset, and you require a proxy, configure them:
        ```bash
        npm config set proxy http://your.proxy.server:port
        npm config set https-proxy http://your.proxy.server:port
        npm config set registry http://registry.npmjs.org/ # Use http if your proxy struggles with https
        ```
        Remember to revert these if you move off the proxy network.

6.  **Try a Known-Good Version (if applicable):** If you suspect a version-specific issue, try installing an older, known-stable version of the package.

    ```bash
    npm install some-package@1.0.0
    ```

By systematically working through these steps, you should be able to identify and resolve the root cause of the `npm ERR! 404 Not Found` error.

## Code Examples

Here are some concise, copy-paste ready code examples to help troubleshoot:

```bash
# 1. Clear npm cache (always a good first step for many npm issues)
npm cache clean --force

# 2. Check your current npm registry
npm config get registry

# 3. Set registry to default public npm (if it's incorrect)
npm config set registry https://registry.npmjs.org/

# 4. Search for a package (to verify spelling and existence)
npm search webpack-cli # Use the correct spelling you expect

# 5. View all available versions of a package (e.g., to confirm a specific version exists)
npm view react versions

# 6. Install a specific version of a package (if you suspect a version issue)
npm install express@4.17.1

# 7. Check if you're logged into a private registry
npm whoami --registry https://my-private-registry.com/npm/

# 8. List all active npm configurations, useful for debugging
npm config list -l
```

## Environment-Specific Notes

The context in which you encounter this 404 error can influence the troubleshooting approach. I've seen this in production when environmental factors come into play.

### Local Development

On your local machine, the issue is typically one of the common causes: a typo, an outdated `package.json` reference, or a misconfigured local `.npmrc` file. Check your global npm configuration (`npm config list -l`) and any `.npmrc` file in your project root or user home directory (`~/.npmrc`). Proxy settings on your local machine, often found in environment variables or browser settings, can also interfere if npm isn't explicitly configured to use them.

### Docker Containers

When building or running applications in Docker containers, `npm ERR! 404` issues often relate to the build environment inside the container:

*   **`.npmrc` Files:** Ensure your `.npmrc` file, especially if it contains private registry configurations or authentication tokens, is correctly copied into the Docker image or mounted as a volume during the build process. A common mistake is not copying the `.npmrc` file early enough in the `Dockerfile` or inadvertently excluding it.
*   **Network Access:** The container's network configuration might differ from your host. Check if the container has outbound internet access to reach the npm registry, especially if it's behind a corporate proxy that requires specific `ENV` variables for network configuration (e.g., `HTTP_PROXY`, `HTTPS_PROXY`).
*   **Base Image:** Some base Docker images might come with pre-configured or restrictive npm settings that need to be overridden.

### CI/CD Pipelines (e.g., Jenkins, GitLab CI, GitHub Actions)

CI/CD environments are highly susceptible to registry-related issues:

*   **Environment Variables:** Authentication tokens for private registries are almost always passed as environment variables (`NPM_TOKEN`, `GH_TOKEN`) in CI/CD. Ensure these variables are correctly set, not expired, and accessible to the npm process.
*   **`.npmrc` Generation:** Often, `.npmrc` files for private registries are generated on-the-fly within the pipeline using secrets. Verify that this generation step is correct and the resulting `.npmrc` is placed in the expected location for `npm install` to find it.
*   **Caching:** CI pipelines often use caching mechanisms to speed up builds. A stale cache might incorrectly remember a non-existent package or an old registry configuration. Try disabling or invalidating the npm cache in your CI pipeline if you suspect this.
*   **Network Security:** The CI/CD runner's network might have strict firewall rules or egress filtering that prevent it from reaching certain npm registries or external package sources.

### Cloud Deployments (e.g., AWS Lambda, Heroku, Vercel)

Cloud platforms perform their own build processes. I've seen `404 Not Found` here when:

*   **Build Environment:** The build environment on cloud platforms might be different from your local setup. Ensure your `package.json` dependencies are valid and accessible from the cloud provider's build servers.
*   **Private Packages:** If your deployment relies on private packages, ensure your `.npmrc` file with authentication details is included in your deployment bundle or that the cloud provider's build service has the necessary credentials configured (e.g., through environment variables or specific build settings).
*   **Node.js Version:** An incompatible Node.js version might try to fetch an incorrect version of a package. Ensure your `engines.node` in `package.json` aligns with the platform's supported versions.

## Frequently Asked Questions

**Q: Why does `npm search` find the package, but `npm install` throws a 404?**
**A:** `npm search` often queries a different, potentially cached or less restrictive API endpoint of the npm registry. It might show packages that are deprecated, very old, or that exist but don't have the specific version you're requesting. `npm install`, on the other hand, tries to fetch a precise package/version combination. If that exact combination isn't found, you'll get the 404. Double-check the exact version you're trying to install against what's truly available using `npm view <package-name> versions`.

**Q: I've updated my `.npmrc` file, but the error persists. What's wrong?**
**A:** Ensure your `.npmrc` file is in the correct location. It can be in your project root, your user home directory (`~/.npmrc`), or globally configured. The hierarchy matters. Project-level `.npmrc` files override user-level ones, which override global configurations. After modifying `.npmrc`, it's also a good practice to run `npm cache clean --force` and then retry `npm install`. Use `npm config list` to see the effective configuration that npm is using.

**Q: Is this error typically caused by a network issue?**
**A:** No, not directly. A `404 Not Found` error means that the npm client successfully *reached* the registry server, but the server reported that the requested package resource could not be found. If there was a fundamental network issue (e.g., no internet connection, DNS resolution failure, firewall blocking access to the npm registry), you would typically see a different error, such as `ETIMEDOUT`, `ECONNREFUSED`, or `ENOTFOUND`.

**Q: Can a corporate proxy or VPN cause a 404 Not Found?**
**A:** While less common than direct network errors, a misconfigured proxy *can* sometimes lead to a 404. If the proxy incorrectly routes the request or if it fails to correctly forward specific package requests to the actual npm registry, it might return a 404 response itself instead of a network error. Ensure your `npm config` proxy settings are correct, and if possible, test without the proxy or VPN to rule it out.

**Q: What if the package was recently published or unpublished?**
**A:** When a package is very recently published, it might take a few moments for it to fully propagate across all npm registry mirrors, though this is rare for a 404. More likely, if a package was recently *unpublished* or *renamed*, then any attempt to install the old name will result in a 404. This is particularly true for private packages where access controls might have been recently changed.

## Related Errors

*   [npm-eresolve](/errors/npm-eresolve.html)
*   [docker-image-not-found](/errors/docker-image-not-found.html)