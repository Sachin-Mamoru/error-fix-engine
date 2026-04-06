# Git error: Permission denied (publickey)
> Encountering Git error: Permission denied (publickey) means Git cannot authenticate your identity via SSH; this guide explains how to fix it.

## What This Error Means

When you see "Permission denied (publickey)" during a Git operation (like `git clone`, `git pull`, or `git push`), it signifies that the SSH authentication mechanism has failed. Git itself isn't the problem here; it's merely reporting an issue with the underlying secure shell (SSH) connection it's trying to establish with your remote Git repository host (e.g., GitHub, GitLab, Bitbucket).

In essence, your client machine tried to connect to the remote server using SSH, presenting an identity (an SSH key), but the server did not accept it. This usually means the server doesn't have a record of the public key corresponding to the private key your client tried to use, or the client failed to properly present the private key. It's a security gate saying, "I don't know you, or I can't verify your identity."

## Why It Happens

SSH uses a pair of cryptographic keys: a private key and a public key. You keep the private key secret on your local machine, and you upload the public key to services you want to access (like your Git host). When you initiate an SSH connection, your client uses your private key to prove its identity to the server. The server then checks if it has a matching public key and if the proof is valid. If this check fails at any stage, you get a "Permission denied (publickey)" error.

This robust authentication mechanism ensures that only authorized users with the correct key can access your repositories, preventing unauthorized access even if someone knows your username. The error simply tells us that this handshake process didn't complete successfully.

## Common Causes

In my experience, this error almost always boils down to one of a few common misconfigurations or omissions:

*   **Missing SSH Key Pair:** You haven't generated an SSH key pair on your local machine.
*   **Public Key Not Registered:** You've generated a key pair, but you haven't uploaded your public key to your Git hosting provider (GitHub, GitLab, Bitbucket, etc.). The server simply doesn't know your identity.
*   **SSH Key Not Added to the Agent:** Your private key exists, but your SSH agent (a background program that manages your SSH keys) isn't aware of it. Without the agent, your SSH client can't find and use the key.
*   **Incorrect Private Key Usage:**
    *   The SSH client is looking for a key at a default location (e.g., `~/.ssh/id_rsa` or `~/.ssh/id_ed25519`), but your private key is located elsewhere.
    *   You have multiple private keys, and the wrong one is being used or offered.
    *   The private key requires a passphrase, and the SSH agent either doesn't have it or isn't prompting for it correctly.
*   **Incorrect File Permissions:** SSH is very strict about key file permissions. If your private key file (`id_rsa` or `id_ed25519`) or the `~/.ssh` directory has permissions that are too broad (e.g., writable by others), SSH will refuse to use it for security reasons.
*   **Using HTTPS URL Instead of SSH:** Your Git remote URL might be configured to use HTTPS (e.g., `https://github.com/user/repo.git`) instead of SSH (e.g., `git@github.com:user/repo.git`). While you *can* authenticate with HTTPS using a personal access token, the "publickey" error specifically points to an SSH issue.
*   **SSH Configuration Issues (`~/.ssh/config`):** Sometimes, a custom SSH configuration file might direct traffic or keys incorrectly, especially when dealing with multiple accounts or custom hostnames.
*   **Corrupted Key Files:** Though rare, a key file might be corrupted, rendering it unusable.

## Step-by-Step Fix

Let's walk through the troubleshooting steps systematically. This approach has helped me resolve this error countless times, both on development machines and production servers.

### Step 1: Verify Your SSH Agent and Existing Keys

First, check if your SSH agent is running and which keys it currently manages.

1.  **Check if the SSH agent is running:**
    ```bash
    eval "$(ssh-agent -s)"
    ```
    If it's already running, it will output its PID. If not, it will start it. On some systems (especially macOS), the agent might start automatically.

2.  **List keys currently known by the agent:**
    ```bash
    ssh-add -l
    ```
    If you see `The agent has no identities.` or similar, no keys are loaded. If you see key fingerprints, your agent is active and has keys. Note the key paths to ensure they are the ones you intend to use.

### Step 2: Generate an SSH Key Pair (If Needed)

If you don't have an SSH key pair, or you're unsure, it's best to generate a new one. I prefer `ed25519` keys for their security and performance.

1.  **Generate a new key pair:**
    ```bash
    ssh-keygen -t ed25519 -C "your_email@example.com"
    ```
    *   You'll be prompted for a file to save the key. The default (`~/.ssh/id_ed25519`) is usually fine. Press Enter.
    *   You'll be asked for a passphrase. I highly recommend using one for security, especially for production environments. The SSH agent will manage it for you, so you won't type it repeatedly.

2.  **Set correct permissions for the private key:**
    SSH is very particular about permissions.
    ```bash
    chmod 600 ~/.ssh/id_ed25519
    ```
    This makes the private key readable only by the owner. The public key (`.pub` file) can have more permissive settings (e.g., 644) as it's meant to be shared.

### Step 3: Add Your Private Key to the SSH Agent

Even if you generated a key, the agent might not automatically load it.

1.  **Add your private key to the SSH agent:**
    ```bash
    ssh-add ~/.ssh/id_ed25519
    ```
    If you used a passphrase, you'll be prompted to enter it. Once added, `ssh-add -l` should show your key.

### Step 4: Copy Your Public Key

You need to provide your public key to your Git hosting service.

1.  **Display your public key:**
    ```bash
    cat ~/.ssh/id_ed25519.pub
    ```
    Copy the entire output to your clipboard. It will look something like `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC5... your_email@example.com`.

### Step 5: Add Your Public Key to Your Git Host

This is a critical step. Log in to your Git hosting platform (GitHub, GitLab, Bitbucket) and add your copied public key.

*   **GitHub:** Settings -> SSH and GPG keys -> New SSH key.
*   **GitLab:** User Settings -> SSH Keys -> Add an SSH key.
*   **Bitbucket:** Personal settings -> SSH keys -> Add key.

Paste the public key you copied in Step 4 into the designated field. Give it a descriptive title (e.g., "My Work Laptop" or "Dev Server Key").

### Step 6: Verify SSH Connection to Your Git Host

After adding the key, test the connection without performing any Git operations.

1.  **Test connection:**
    *   **GitHub:**
        ```bash
        ssh -T git@github.com
        ```
    *   **GitLab:**
        ```bash
        ssh -T git@gitlab.com
        ```
    *   **Bitbucket:**
        ```bash
        ssh -T git@bitbucket.org
        ```
    You should see a message like "Hi *username*! You've successfully authenticated, but GitHub does not provide shell access." or similar. If you get "Permission denied," re-check all previous steps, especially Step 3 and 5.

### Step 7: Ensure Your Git Remote URL Uses SSH

Your Git repository needs to be configured to use the SSH protocol, not HTTPS.

1.  **Check your current remote URL:**
    Navigate to your local repository and run:
    ```bash
    git remote -v
    ```
    Look for URLs starting with `https://` (e.g., `https://github.com/user/repo.git`). If you see one, you need to change it.

2.  **Change the remote URL to SSH:**
    Find the correct SSH URL on your Git host's repository page (it typically starts with `git@`). It will look something like `git@github.com:user/repo.git`. Then update your remote:
    ```bash
    git remote set-url origin git@github.com:user/repo.git
    ```
    Replace `origin` with your remote name if it's different.

### Step 8: Retry Your Git Operation

Now, try your original Git command (e.g., `git pull`, `git push`, `git clone`). It should now work without the "Permission denied" error.

## Code Examples

Here are some concise, copy-paste-ready commands for the most common scenarios.

**1. Generate a new Ed25519 SSH key (recommended):**
```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519
```
*Note: The `-f` flag specifies the file path directly, avoiding the prompt.*

**2. Ensure SSH agent is running and add a key:**
```bash
eval "$(ssh-agent -s)" # Start agent if not running
ssh-add ~/.ssh/id_ed25519 # Add your private key
```

**3. Display your public key for copying:**
```bash
cat ~/.ssh/id_ed25519.pub
```

**4. Check your Git remote URL and change it to SSH:**
```bash
# Check current remotes
git remote -v

# Change the 'origin' remote to an SSH URL (replace with your actual URL)
git remote set-url origin git@github.com:your_username/your_repository.git
```

**5. Verify SSH connection to your Git host:**
```bash
# For GitHub
ssh -T git@github.com

# For GitLab
ssh -T git@gitlab.com

# For Bitbucket
ssh -T git@bitbucket.org
```

**6. Set strict permissions for your private key:**
```bash
chmod 600 ~/.ssh/id_ed25519
```

## Environment-Specific Notes

The "Permission denied (publickey)" error can manifest differently or require slightly altered approaches depending on your environment.

### Cloud Virtual Machines (AWS EC2, GCP Compute Engine, Azure VMs)

*   **Key Pairs vs. SSH Agent:** Cloud VMs often rely on instance-specific key pairs assigned at launch. When you `ssh` into the VM, you specify the private key using `-i /path/to/key.pem`.
*   **Git Operations *from* the VM:** If you're doing Git operations *from* the VM (e.g., `git clone` a private repo), you'll need to generate a new SSH key pair *on the VM itself* and add the public key to your Git provider account, just like on a local machine.
*   **IAM Roles/Service Accounts:** For automated Git operations (e.g., by a CI/CD pipeline running on the VM), consider using Git provider features like deploy keys or leveraging cloud provider service accounts/IAM roles with OIDC for Git authentication if supported, rather than directly managing user SSH keys. I've seen this in production when deploying from EC2 instances to private repos.
*   **`~/.ssh/config`:** If you have multiple users or projects on a single VM, using `~/.ssh/config` can help manage which private key to use for specific Git hosts (e.g., `Host github.com-myuser`).

### Docker Containers

*   **SSH Agent Forwarding (Recommended):** The most secure way to perform Git operations from *inside* a Docker container against private repos is to use SSH agent forwarding. This allows the container to use the SSH keys from your host machine's agent without copying them into the container.
    ```bash
    # Run container with agent forwarding
    docker run -it -e SSH_AUTH_SOCK=$SSH_AUTH_SOCK -v $SSH_AUTH_SOCK:$SSH_AUTH_SOCK my_image /bin/bash
    ```
    Inside the container, `ssh-add -l` should show your host's keys.
*   **Copying Keys (Use with Caution):** Avoid baking private SSH keys directly into Docker images. If you absolutely must, copy them at runtime (e.g., using a multi-stage build or `docker cp`) and ensure they are immediately deleted or tightly permissioned. This is generally not recommended for security reasons.
*   **Build-time Cloning:** For cloning public repositories during image build, you don't need SSH keys. For private repositories, if you *must* clone at build time, consider using an HTTPS token for temporary access rather than SSH keys.

### Local Development Environments

*   **Standard Setup:** The steps outlined in "Step-by-Step Fix" are primarily designed for local development machines (Linux, macOS, Windows with WSL/Git Bash).
*   **Multiple Accounts:** If you work with multiple Git accounts (e.g., a personal GitHub and a work GitHub), you'll likely have multiple key pairs. Use `~/.ssh/config` to tell SSH which key to use for which host:
    ```
    # ~/.ssh/config
    Host github.com-personal
        HostName github.com
        User git
        IdentityFile ~/.ssh/id_ed25519_personal

    Host github.com-work
        HostName github.com
        User git
        IdentityFile ~/.ssh/id_ed25519_work
    ```
    Then, your remote URLs would be `git@github.com-personal:myuser/repo.git`.

### CI/CD Pipelines (Jenkins, GitLab CI, GitHub Actions, CircleCI, etc.)

*   **Deploy Keys:** For read-only access to a single repository by a build server, a "deploy key" is an excellent solution. You generate a key pair, add the public key as a deploy key to the specific repo, and store the private key as a secret in your CI/CD environment variables.
*   **Access Tokens/OIDC:** Many CI/CD platforms now integrate with Git providers using OAuth or OpenID Connect (OIDC) to issue temporary, scoped tokens, which is often more secure and flexible than managing SSH keys. This is my preferred method where available.
*   **Secrets Management:** Never hardcode private keys in your pipeline scripts. Always use your CI/CD platform's secret management features to store and inject private keys as environment variables during pipeline execution.

## Frequently Asked Questions

**Q: Should I use a passphrase when generating my SSH key?**
**A:** Yes, absolutely. A passphrase adds an extra layer of security. If your private key is ever compromised, the passphrase protects it. When using an SSH agent, you typically only enter the passphrase once per session, making it convenient.

**Q: Can I have multiple SSH keys?**
**A:** Yes. You can generate multiple key pairs (e.g., one for work, one for personal projects). You'll manage them using the `ssh-add` command and often by configuring your `~/.ssh/config` file to specify which key to use for different hosts or users.

**Q: What if `ssh-add` gives "Could not open a connection to your authentication agent."?**
**A:** This means your SSH agent isn't running. You need to start it first, usually with `eval "$(ssh-agent -s)"`. Then you can add your keys.

**Q: My key is listed by `ssh-add -l`, and it's on my Git host. Why am I still getting "Permission denied"?**
**A:** Double-check the permissions on your private key file (`chmod 600 ~/.ssh/id_ed25519`). Also, ensure your Git remote URL is configured to use SSH (`git@github.com:user/repo.git`) and not HTTPS. Finally, verify that the public key you uploaded to the Git host truly matches the private key you're trying to use.

**Q: What's the difference between `id_rsa` and `id_ed25519`?**
**A:** These are different types of cryptographic algorithms used for generating keys. `id_rsa` uses the RSA algorithm, while `id_ed25519` uses the Ed25519 algorithm. Ed25519 is generally considered more secure, faster, and produces shorter keys. For new keys, `ed25519` is the recommended choice.

## Related Errors

*   [linux-permission-denied](/errors/linux-permission-denied.html)