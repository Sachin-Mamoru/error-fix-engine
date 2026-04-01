# npm ERR! EACCES permission denied
> Encountering npm ERR! EACCES permission denied means npm lacks write access to critical directories; this guide explains how to fix it.

## What This Error Means

When you see `npm ERR! EACCES permission denied`, it's a clear signal from your operating system that the `npm` process is trying to write a file or create a directory in a location where it doesn't have the necessary permissions. The `EACCES` part is a standard Unix error code for "Permission denied". In the context of `npm`, this error almost exclusively occurs when you're attempting to install a global package (using the `-g` flag) or when `npm` is trying to manage its internal caches or global `node_modules` directory.

Specifically, `npm` is attempting to modify files within a directory that is typically owned by the `root` user or another system account, rather than your current user. This prevents `npm` from installing, updating, or deleting packages globally, as it cannot write to its designated global installation path, which by default often resides in system-wide locations like `/usr/local/lib/node_modules` or `/usr/lib/node_modules`.

## Why It Happens

This error fundamentally stems from a mismatch between the user executing `npm` and the owner of the `npm` global installation directories. When `npm` needs to install a package globally, it places that package and its executables into specific system-wide locations. If these locations are not owned by your current user, or if your user does not have write permissions to them, the `EACCES` error is triggered.

In my experience, the core reason this happens is usually due to one of two scenarios:
1.  **Incorrect initial setup:** Node.js and `npm` were installed using `sudo` or as the `root` user, making the global directories (`node_modules`, `bin`, `share`) owned by `root`. Subsequent `npm` commands executed as a non-root user will then fail.
2.  **Environment changes:** Switching between Node.js versions, using a different user account, or even system updates can sometimes mess with the permissions, leaving the global `npm` directories in a state where your current user no longer has write access.

The standard `npm` installation process expects that the user will have full read/write access to its global installation prefix. When this expectation is violated, the `EACCES` error is the inevitable result.

## Common Causes

Let's break down the most common scenarios I've encountered that lead to this permission nightmare:

*   **Installing Node.js via `sudo` or as `root`:** This is the most prevalent cause. If you've ever run `sudo apt-get install nodejs` or `sudo brew install node`, the global `npm` directories were likely created and owned by `root`. When you later try to `npm install -g <package>` as your regular user, `npm` tries to write to these root-owned directories and gets denied. I've seen this in production when developers set up new CI/CD runners and use `sudo` for convenience.
*   **Mixing package managers:** Installing Node.js via `apt`, `brew`, `nvm`, or directly from the official installer can lead to different installation paths and ownerships. If you switch between these methods without cleaning up or reconfiguring `npm`, you might end up with conflicting permissions. For instance, installing via `brew` might put things in `/usr/local/` while a system package might use `/usr/`.
*   **Corrupt permissions:** Less common, but sometimes file system permissions can become corrupted or altered by other system processes, leaving `npm`'s directories inaccessible even if they were initially set up correctly. This can happen after system restores or certain security hardening actions.
*   **Using `sudo npm install -g` as a workaround:** While it *seems* to work by forcing the command to run as `root`, this is a temporary fix that exacerbates the problem. It writes more files as `root`, ensuring that any future `npm` commands run by your regular user will continue to hit `EACCES`. It creates a cycle of needing `sudo` for global installs, which is exactly what we want to avoid. This is a common trap, especially for junior engineers trying to get something working quickly.

## Step-by-Step Fix

There are a few ways to tackle `npm ERR! EACCES`. I'll outline the most common and robust solutions.

First, identify your global `npm` installation prefix:
```bash
npm config get prefix
```
This command will output the directory where `npm` expects to install global packages. Common outputs are `/usr/local` or `/usr`. Keep this in mind as you proceed.

### Option 1: Fix Permissions (Recommended for existing installations)

This is the most straightforward and generally recommended solution if you want to keep your Node.js installation in its current location. It involves changing the ownership of `npm`'s global directories to your user.

1.  **Get your username:**
    ```bash
    whoami
    ```
    This command will print your current username. For example, `omarfarooq`.

2.  **Change ownership of the `npm` global directories:**
    Replace `<your-username>` with the output from `whoami` and `<npm-prefix>` with the output from `npm config get prefix`.

    ```bash
    sudo chown -R $(whoami) $(npm config get prefix)/{lib/node_modules,bin,share}
    ```
    Let's break down this command:
    *   `sudo`: Executes the command with superuser privileges, as we're modifying system-owned directories.
    *   `chown`: Changes the owner of files and directories.
    *   `-R`: Recursive. This is critical as it applies the ownership change to all files and subdirectories within the specified paths.
    *   `$(whoami)`: A command substitution that inserts your current username.
    *   `$(npm config get prefix)`: Another command substitution that gets `npm`'s global prefix.
    *   `/{lib/node_modules,bin,share}`: This is a bash brace expansion that expands to `.../lib/node_modules`, `.../bin`, and `.../share`. These are the primary directories where global `npm` packages, executables, and documentation are stored. We need to ensure your user owns all of them.

    After running this command, try your `npm install -g` command again. It should now work without permission errors.

### Option 2: Reconfigure `npm` to use a different directory (Alternative)

If you're uncomfortable with `sudo` or if fixing permissions proves too complex (e.g., in a highly restricted environment), you can tell `npm` to use a different directory for global packages – one located within your user's home directory. This is often my preferred method for new setups, as it completely sidesteps the `sudo` issue.

1.  **Create a new directory for global packages:**
    ```bash
    mkdir ~/.npm-global
    ```
    This creates a new directory named `.npm-global` in your home directory, which you definitely own.

2.  **Configure `npm` to use this new directory:**
    ```bash
    npm config set prefix '~/.npm-global'
    ```
    This tells `npm` to install all future global packages into `~/.npm-global` instead of the system-wide default.

3.  **Add this directory to your system's PATH:**
    For the global executables (like `nodemon`, `create-react-app`, etc.) to be accessible from your terminal, you need to add the `bin` subdirectory of your new `npm` prefix to your shell's `PATH` environment variable.

    Open your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`, or `~/.profile`) with a text editor and add the following line:
    ```bash
    export PATH=~/.npm-global/bin:$PATH
    ```
    Save the file and then apply the changes by running:
    ```bash
    source ~/.bashrc  # Or ~/.zshrc, ~/.profile, etc.
    ```
    Now, when you install a global package, `npm` will place it in `~/.npm-global/bin`, and your shell will find it.

### Option 3: Use a Node Version Manager (Long-term Solution)

For the most robust and hassle-free experience, especially if you work with multiple Node.js versions, I strongly recommend using a Node Version Manager like NVM (Node Version Manager), `n`, or Volta. These tools manage Node.js and `npm` installations in your user's home directory, inherently avoiding `EACCES` issues.

*   **NVM (Node Version Manager):** My personal go-to. It allows you to install and switch between multiple Node.js versions effortlessly. Each Node.js installation (and its accompanying `npm`) is installed in `~/.nvm`, which is user-owned.
    ```bash
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    # After installation, restart your terminal or source your profile
    nvm install node # Installs the latest LTS version of Node.js and npm
    nvm use node     # Uses the installed version
    ```
    With NVM, you rarely, if ever, encounter `EACCES` for global `npm` installs.

## Code Examples

Here are the key commands used in the fixes, ready for copy-pasting.

**1. Getting `npm`'s global prefix:**
```bash
npm config get prefix
```

**2. Fixing permissions on default global `npm` directories (replace `myuser` with your actual username):**
```bash
# Example: If npm config get prefix returns /usr/local
sudo chown -R myuser /usr/local/{lib/node_modules,bin,share}

# General command using substitution
sudo chown -R $(whoami) $(npm config get prefix)/{lib/node_modules,bin,share}
```

**3. Configuring `npm` to use a user-owned directory:**
```bash
# Create the new directory
mkdir ~/.npm-global

# Set npm's prefix to this new directory
npm config set prefix '~/.npm-global'

# Add to your PATH (e.g., in ~/.bashrc or ~/.zshrc)
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

## Environment-Specific Notes

The `EACCES` error manifests differently, or requires different considerations, depending on your environment.

### Cloud (CI/CD Pipelines)

In CI/CD environments (e.g., GitLab CI, GitHub Actions, Jenkins), this error usually indicates that the build agent is trying to install global packages using a user that doesn't have write access to the Node.js installation directory.
*   **Solution:** Never use `sudo npm install -g` in CI/CD. Instead, use a Node Version Manager (like NVM for shell-based runners), or configure `npm` to use a local prefix within the build workspace that the CI user owns. Most CI platforms provide tools or pre-built images with Node/npm installed correctly, or they recommend using NVM. I've often seen teams try to install global tools like `firebase-tools` or `serverless` and hit this. Always ensure the `npm` user has control over the install path.

### Docker

This is a common headache in Dockerfiles if not handled carefully.
*   **During Build (Dockerfile `RUN` instructions):** If you install Node.js as `root` (which is typical in many base images or `apt-get` commands), and then run `npm install -g` as `root` in a `RUN` command, it works. However, if a later `RUN` command or a subsequent `USER` directive switches to a non-root user, and that user tries to *update* or *install* another global package, they'll hit `EACCES`.
    *   **Best Practice:** When installing global packages in a Dockerfile, explicitly set the `npm config prefix` to a user-owned directory *before* installing, or create and `chown` the default prefix to the non-root user you plan to use.
    ```dockerfile
    # Example using a non-root user 'node' (often default in official node images)
    FROM node:lts-slim

    # Set npm to use a user-owned directory for global packages
    RUN npm config set prefix /home/node/.npm-global && \
        # Ensure the directory exists and is owned by the 'node' user
        mkdir -p /home/node/.npm-global && \
        chown -R node:node /home/node/.npm-global

    # Add npm's bin directory to PATH for the 'node' user
    ENV PATH="/home/node/.npm-global/bin:$PATH"

    # Switch to the non-root user
    USER node

    # Now, global installs by 'npm' will go into a user-owned directory
    RUN npm install -g pm2
    ```
*   **During Runtime:** If your `Dockerfile` installs global packages as `root`, but your `docker run` command or container entrypoint executes `npm` commands as a non-root user, you'll see `EACCES`. Ensure consistency in user context throughout your Docker build and runtime.

### Local Development

This is where you'll most frequently encounter and fix `EACCES`. The solutions provided in the "Step-by-Step Fix" section (fixing permissions with `chown` or reconfiguring `npm`'s prefix) are specifically tailored for local development environments on macOS, Linux, and WSL. Using a Node Version Manager like NVM is, in my professional opinion, the most robust way to manage Node.js versions and avoid these permission issues locally.

## Frequently Asked Questions

**Q: Why is `sudo npm install -g` considered bad practice?**
**A:** Using `sudo npm install -g` forces `npm` to run as the `root` user, which then creates files and directories owned by `root`. This means your regular user will not have write permissions to these global `npm` directories, leading to `EACCES` errors for any subsequent `npm` commands run without `sudo`. It's a cyclical problem that makes your environment brittle and insecure.

**Q: Will fixing permissions break anything else on my system?**
**A:** No, fixing the ownership of the `npm` global directories to your user is a standard and safe practice. It ensures that `npm` can manage its packages correctly without requiring elevated privileges. It only affects the `npm` installation, not other system components.

**Q: What if I don't have `sudo` access on my machine?**
**A:** If you cannot use `sudo` (e.g., on a shared server or restricted environment), your best option is **Option 2: Reconfigure `npm` to use a different directory** within your home directory (`~/.npm-global`). This approach entirely bypasses the need for root permissions, as you own your home directory. Alternatively, use a Node Version Manager like NVM, which also installs Node/npm within your home directory.

**Q: Does this `EACCES` error also apply to local `node_modules` within my project?**
**A:** Generally, no. This specific `EACCES` error (the global `npm ERR! EACCES`) almost exclusively refers to permission issues with `npm`'s global installation directories (`-g`). If you get permission errors within a project's `node_modules` directory, it's usually due to:
1.  The project directory itself being owned by another user.
2.  Running `npm install` in a directory that has been previously modified by `sudo` (e.g., `sudo npm install` was run in the project directory once).
3.  File system corruption.
For local `node_modules`, you'd typically run `sudo chown -R $(whoami) .` within the project directory to fix ownership.

**Q: Should I just uninstall and reinstall Node.js to fix this?**
**A:** While uninstalling and reinstalling Node.js *might* reset permissions if done correctly (e.g., using a version manager from the start), it's often overkill and doesn't directly address the root cause of existing permission issues. The `chown` command (Option 1) or reconfiguring the `npm` prefix (Option 2) are more targeted and efficient solutions. If you do decide to reinstall, consider using NVM to prevent future `EACCES` problems.

## Related Errors
- [linux-permission-denied](/errors/linux-permission-denied.html)
- [docker-permission-denied](/errors/docker-permission-denied.html)