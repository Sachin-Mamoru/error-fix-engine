# Git error: Permission denied (publickey)
> Encountering 'Git error: Permission denied (publickey)' means your SSH key setup is incorrect; this guide explains how to fix it.

## What This Error Means

When you see the "Permission denied (publickey)" error during a Git operation (like `git clone`, `git pull`, or `git push`), it means your local machine is attempting to authenticate with a remote Git server (e.g., GitHub, GitLab, Bitbucket) using the SSH protocol, but the server is rejecting the connection. This isn't a problem with Git itself, but rather with how your SSH client is trying to prove its identity to the SSH server. The server expects to find a matching public key for a private key that your client presents, and that validation is failing. Essentially, the server doesn't recognize you or doesn't trust the key you're trying to use.

## Why It Happens

This error fundamentally happens because the secure handshake between your local machine's SSH client and the remote Git server's SSH daemon isn't completing successfully. SSH authentication relies on a key pair: a private key stored securely on your local machine and a corresponding public key registered with the remote service. When you initiate an SSH connection (which Git does under the hood for SSH URLs), your client tries to use one of its known private keys to sign a challenge from the server. The server then verifies this signature using the public key it has on file for your user. If the private key isn't available, isn't loaded, has incorrect permissions, or if the corresponding public key isn't on the server, the authentication fails, leading to the "Permission denied (publickey)" error.

## Common Causes

In my experience, this error almost always boils down to one of a few common issues:

1.  **Missing or Incorrect Private Key:** The SSH client can't find your private key in the default location (`~/.ssh/id_rsa`, `~/.ssh/id_ed25519`, etc.) or it's simply not present on your system.
2.  **Private Key Not Loaded into SSH Agent:** Even if the private key exists, the `ssh-agent` (a program that holds private keys in memory for SSH) might not have it loaded. This means it's not available for the SSH client to use.
3.  **Incorrect Key Permissions:** For security reasons, SSH keys must have very strict file permissions. If your private key file (e.g., `id_rsa`) or the `~/.ssh` directory is too permissive, the SSH client will refuse to use it.
4.  **Public Key Not Registered on Remote:** The corresponding public key is not uploaded to your user profile on the remote Git service (GitHub, GitLab, Bitbucket, etc.) or is associated with a different user account.
5.  **Using the Wrong SSH Key:** You might have multiple SSH keys, and the client is trying to use a key that isn't recognized by the specific remote repository or user account. This often happens when working with multiple organizations or personal/work accounts.
6.  **SSH Configuration Issues (`~/.ssh/config`):** Your SSH configuration file might be directing your SSH client to use the wrong key for a particular host, or it might have incorrect host entries.
7.  **Incorrect Remote URL:** You're trying to use an SSH remote URL (e.g., `git@github.com:user/repo.git`), but you've mistakenly configured Git to use an HTTPS URL (e.g., `https://github.com/user/repo.git`), or vice-versa, causing Git to try the wrong authentication method.
8.  **Server Fingerprint Change:** Less common but possible, the remote server's host key (fingerprint) might have changed, triggering a warning and preventing connection. This typically prompts a different error message but can indirectly block SSH.

## Step-by-Step Fix

Let's walk through the troubleshooting steps. I always follow this sequence when I hit this error, and it rarely fails to identify the root cause.

### Step 1: Verify SSH Agent Status and Loaded Keys

First, ensure your `ssh-agent` is running and has your keys loaded.

1.  **Check if `ssh-agent` is running:**
    ```bash
    eval "$(ssh-agent -s)"
    ```
    If it's not running, this command will start it and set the necessary environment variables. If it's already running, it might just output the agent PID.

2.  **List loaded keys:**
    ```bash
    ssh-add -l
    ```
    This command lists the fingerprints of all identities currently loaded into the `ssh-agent`. If you see "The agent has no identities," your key isn't loaded. If you see keys listed, ensure they are the correct ones for your Git host.

### Step 2: Add Your SSH Key to the Agent

If your key isn't loaded, add it.

1.  **Identify your private key file:** Common names are `id_rsa` or `id_ed25519` within your `~/.ssh` directory.
2.  **Add the key:**
    ```bash
    ssh-add ~/.ssh/id_rsa
    # Or for Ed25519 keys:
    # ssh-add ~/.ssh/id_ed25519
    ```
    If your key has a passphrase, you'll be prompted to enter it. If you get an error like "Could not open a connection to your authentication agent," repeat Step 1 to ensure the agent is running. If you see "No such file or directory," your private key might be in a different location or missing.

### Step 3: Check Key Permissions

Incorrect permissions are a frequent culprit.

1.  **Check permissions for your `~/.ssh` directory:**
    ```bash
    chmod 700 ~/.ssh
    ```
2.  **Check permissions for your private key file:**
    ```bash
    chmod 600 ~/.ssh/id_rsa
    # Or for Ed25519 keys:
    # chmod 600 ~/.ssh/id_ed25519
    ```
    The private key file should only be readable by you, and the `~/.ssh` directory should only be accessible by you. SSH is very strict about this for security reasons.

### Step 4: Verify Public Key on Remote Git Host

Ensure the public key corresponding to your private key is correctly registered on GitHub, GitLab, Bitbucket, or your self-hosted Git server.

1.  **Locate your public key:** This is usually the private key file name with a `.pub` extension (e.g., `~/.ssh/id_rsa.pub`).
2.  **Copy the public key content:**
    ```bash
    cat ~/.ssh/id_rsa.pub
    # Or for Ed25519 keys:
    # cat ~/.ssh/id_ed25519.pub
    ```
    Copy the *entire* output, starting with `ssh-rsa` or `ssh-ed25519` and ending with your email/comment.
3.  **Go to your Git host's settings:**
    *   **GitHub:** Settings -> SSH and GPG keys -> New SSH key.
    *   **GitLab:** User Settings -> SSH Keys -> Add an SSH key.
    *   **Bitbucket:** Personal settings -> SSH keys -> Add key.
4.  **Paste the public key:** Ensure there are no extra spaces or line breaks.
5.  **Verify it's for the correct user account.** I've seen this when users have multiple accounts and upload the key to the wrong one.

### Step 5: Test SSH Connection to the Git Host

This step verifies that SSH itself can connect, independently of Git.

```bash
ssh -T git@github.com
# For GitLab: ssh -T git@gitlab.com
# For Bitbucket: ssh -T git@bitbucket.org
```
*   If successful, you'll typically see a message like "Hi [username]! You've successfully authenticated..." or similar. This means your SSH setup is likely correct, and the issue might be with your Git remote URL.
*   If it still fails with "Permission denied (publickey)," then the problem is still with your SSH key setup on your local machine or with the public key on the remote. Re-check steps 1-4 carefully.

### Step 6: Review SSH Configuration (`~/.ssh/config`)

If you have specific SSH configurations, they might be interfering.

1.  **Open or create `~/.ssh/config`:**
    ```bash
    nano ~/.ssh/config
    # Or use your preferred text editor
    ```
2.  **Ensure correct `IdentityFile` entries:** If you have multiple keys or custom key names, your config file should specify which key to use for which host.
    ```
    Host github.com
      Hostname github.com
      User git
      IdentityFile ~/.ssh/id_rsa_myproject
      # Or for the default key:
      # IdentityFile ~/.ssh/id_rsa
      # Or an Ed25519 key:
      # IdentityFile ~/.ssh/id_ed25519
    ```
    The `User git` line is important as Git SSH operations typically use the 'git' user on the remote.
3.  **Remove any conflicting entries** or ensure the correct `IdentityFile` points to the key you want to use.

### Step 7: Check Git Remote URL

Even if SSH is working, Git needs to be told to use SSH.

1.  **Check your current remote URL:**
    ```bash
    git remote -v
    ```
    Look for an entry like `origin git@github.com:user/repo.git (fetch)`. If it's `https://github.com/user/repo.git`, then Git is trying to use HTTPS authentication, not SSH.

2.  **Change to SSH URL if necessary:**
    ```bash
    git remote set-url origin git@github.com:user/repo.git
    ```
    Replace `user/repo.git` with the correct path to your repository. After this, try your Git command again.

## Code Examples

Here are some of the most critical commands, ready for copy-paste:

*   **Start SSH agent and add default private key (with passphrase prompt):**
    ```bash
    eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_rsa
    ```

*   **List keys currently loaded in SSH agent:**
    ```bash
    ssh-add -l
    ```

*   **Set correct permissions for the SSH directory and private key:**
    ```bash
    chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_rsa
    ```

*   **Test SSH connection to GitHub (replace host as needed):**
    ```bash
    ssh -T git@github.com
    ```

*   **View current Git remote URLs:**
    ```bash
    git remote -v
    ```

*   **Change Git remote URL from HTTPS to SSH:**
    ```bash
    git remote set-url origin git@github.com:your_username/your_repository.git
    ```

## Environment-Specific Notes

The "Permission denied (publickey)" error can manifest differently or require slightly different approaches depending on your environment.

*   **Cloud Virtual Machines (AWS EC2, GCP Compute Engine, Azure VMs):**
    *   **Key Management:** For initial access, cloud providers often provide or require you to specify an SSH key pair during instance creation. Ensure you're using the *correct* private key associated with the EC2 instance or VM when connecting to it. If you're using a jump host or bastion, your key needs to be on the jump host or forwarded.
    *   **SSH Agent Forwarding:** When connecting from a local machine *through* a cloud VM to another Git host (e.g., from an EC2 instance to GitHub), you'll often need to use SSH agent forwarding. This allows your local `ssh-agent` to provide keys to remote connections without copying private keys to the VM. Add `-A` to your `ssh` command: `ssh -A user@your-vm-ip`.
    *   **Permissions:** Just like on a local machine, file permissions on cloud VMs are critical. The `~/.ssh` directory and key files must have correct permissions.

*   **Docker Containers:**
    *   **No Persistent Agent:** Docker containers are ephemeral. If you start an `ssh-agent` inside a container and add keys, they will be lost when the container stops.
    *   **Mounting Keys:** For development containers, you can mount your local `~/.ssh` directory as a volume into the container: `-v ~/.ssh:/root/.ssh`. However, be cautious with this as it can expose your keys if the container is compromised.
    *   **SSH Agent Forwarding:** The most secure way to use your local SSH keys inside a running Docker container is SSH agent forwarding. This involves mounting the `ssh-agent` socket into the container.
        ```bash
        docker run -it \
          -v "$SSH_AUTH_SOCK:/ssh-auth.sock" \
          -e SSH_AUTH_SOCK="/ssh-auth.sock" \
          your_image_name bash
        ```
        This allows Git operations within the container to use the keys managed by your host's `ssh-agent`.

*   **Local Development Machines (macOS, Linux, Windows WSL/Git Bash):**
    *   **Standard Practices:** The steps outlined above (checking `ssh-agent`, permissions, `~/.ssh/config`) are most relevant here.
    *   **Multiple Users/Keys:** If you manage multiple Git accounts (personal, work) on the same machine, ensure your `~/.ssh/config` file explicitly defines `IdentityFile` for different `Host` entries to avoid conflicts and ensure the correct key is used.
    *   **Windows:** Git Bash for Windows usually works similar to Linux. For native Windows SSH clients, key paths and permissions might differ slightly, but the `ssh-agent` concept remains. Tools like Pageant (part of PuTTY) can act as an `ssh-agent`.

## Frequently Asked Questions

**Q: What if `ssh-add` says "Could not open a connection to your authentication agent"?**
A: This means your `ssh-agent` is not running or its environment variables aren't correctly set. Run `eval "$(ssh-agent -s)"` to start it and configure your shell, then try `ssh-add` again.

**Q: Why do I have multiple SSH keys? How do I choose which one?**
A: You might have multiple keys for different purposes (e.g., personal GitHub, work GitLab, specific projects requiring unique keys). You can manage which key is used by creating or editing your `~/.ssh/config` file. Use `Host` entries combined with `IdentityFile` to specify which private key to use for a particular remote hostname.

**Q: Is it safe to use SSH keys without a passphrase?**
A: While convenient, using keys without a passphrase is less secure. If someone gains access to your private key file, they can impersonate you without any further authentication. I strongly recommend using passphrases and relying on `ssh-agent` to manage them so you only enter it once per session.

**Q: My key is loaded, permissions are correct, and the public key is on the remote, but it still fails. What else?**
A: Double-check the Git remote URL (`git remote -v`). Ensure it's using the SSH protocol (`git@github.com:...`) and not HTTPS. Also, try connecting verbosely using `ssh -vvv git@github.com` (replace `github.com` with your host) to get detailed debug output, which can sometimes reveal specific SSH client/server handshake issues.

**Q: How do I generate a new SSH key pair?**
A: You can generate a new SSH key pair using `ssh-keygen`.
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# For RSA keys (less recommended now):
# ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```
Follow the prompts, remembering to set a strong passphrase. This will typically create `id_ed25519` and `id_ed25519.pub` (or `id_rsa` and `id_rsa.pub`) in your `~/.ssh` directory.

## Related Errors