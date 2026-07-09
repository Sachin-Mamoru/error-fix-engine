# Git error: Permission denied (publickey)
> Encountering 'Permission denied (publickey)' means your Git client can't authenticate with the remote server using an SSH key; this guide explains how to fix it.

## What This Error Means

When you attempt to interact with a remote Git repository (e.g., `git push`, `git pull`, `git clone`) and receive `Permission denied (publickey)`, it indicates that your local Git client failed to authenticate with the remote Git server using an SSH key. SSH (Secure Shell) relies on a pair of cryptographic keys – a private key kept on your local machine and a corresponding public key registered with the remote server – to establish a secure, authenticated connection without requiring a password each time. This error explicitly states that the server couldn't verify your identity based on the public key it expected to receive.

## Why It Happens

This error fundamentally means the SSH handshake process failed because the server could not find a matching public key for the private key presented by your client, or the private key itself was not accessible or correctly configured. The server is saying, "I don't recognize you, or I can't prove who you are with the information you're providing." It's a security mechanism preventing unauthorized access to your repositories. From my experience, it's one of the most common setup hurdles for new developers and even seasoned engineers setting up a new machine or environment.

## Common Causes

Several scenarios can lead to the `Permission denied (publickey)` error:

1.  **Missing SSH Key Pair:** You haven't generated an SSH key pair (`id_rsa`/`id_rsa.pub` or similar) on your local machine.
2.  **Public Key Not Registered:** Your SSH public key (`id_rsa.pub`) has not been added to your user account on the remote Git hosting service (e.g., GitHub, GitLab, Bitbucket).
3.  **Private Key Not Loaded in `ssh-agent`:** Even if you have a key, your `ssh-agent` (a background program that holds your private keys) isn't running or hasn't loaded your private key, especially if it's passphrase-protected.
4.  **Incorrect File Permissions:** The permissions on your `~/.ssh` directory or the private key file itself are too liberal, which SSH considers a security risk and will refuse to use the key.
5.  **Wrong Private Key Being Used:** If you have multiple SSH keys, Git (or rather, SSH) might be trying to use a different private key than the one whose public counterpart is registered on the remote server. This often happens when `~/.ssh/config` is misconfigured or absent.
6.  **Incorrect Git Remote URL:** Your Git remote URL might be using HTTPS instead of SSH, or it might be pointing to a different server/user where your key isn't registered. While not a direct SSH key issue, it can manifest similarly if SSH is then attempted.
7.  **Key Expired or Revoked:** Less common, but sometimes keys can be configured to expire or might have been manually revoked by a repository administrator.
8.  **SSH Agent Forwarding Issues:** In environments like remote servers or Docker, if you're trying to use a local key, agent forwarding might not be correctly set up.

## Step-by-Step Fix

Let's walk through a systematic approach to diagnose and resolve this issue. I've found this sequence reliable in debugging these kinds of problems.

### 1. Verify Your Git Remote URL

First, ensure your Git remote URL is configured to use SSH, not HTTPS.
```bash
git remote -v
```
You should see URLs starting with `git@` (e.g., `git@github.com:youruser/yourrepo.git`). If it's `https://github.com/...`, you might need to change it.

```bash
# To change an HTTPS URL to SSH
git remote set-url origin git@github.com:youruser/yourrepo.git
```

### 2. Check for Existing SSH Keys

Look in your `~/.ssh` directory for existing key pairs.
```bash
ls -al ~/.ssh
```
You're looking for files like `id_rsa`, `id_ed25519`, `id_dsa`, etc., and their corresponding `.pub` public key files. If you don't see any, you'll need to generate one (Step 3).

### 3. Generate a New SSH Key Pair (If Needed)

If you don't have an SSH key or want to create a new one, use `ssh-keygen`. It's generally recommended to use `ed25519` for modern systems.
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```
*   Press Enter to accept the default file path (`~/.ssh/id_ed25519`).
*   **Strongly recommend** setting a passphrase. It adds an extra layer of security. You'll enter it twice.

### 4. Ensure Correct File Permissions

SSH is very particular about key permissions for security reasons.
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519 # Or your private key file name
chmod 644 ~/.ssh/id_ed25519.pub # Or your public key file name
```
In my experience, incorrect permissions are a very common cause, especially when files are copied or restored.

### 5. Add Your Private Key to the `ssh-agent`

The `ssh-agent` manages your private keys and handles passphrases, so you don't have to enter them repeatedly.

*   **Start the `ssh-agent` (if not running):**
    ```bash
    eval "$(ssh-agent -s)"
    ```
    You should see output like `Agent pid 1234`.

*   **Add your private key to the agent:**
    ```bash
    ssh-add ~/.ssh/id_ed25519 # Or your private key file name
    ```
    If your key has a passphrase, you'll be prompted to enter it now. This only needs to be done once per session or until the agent is killed. To persist this across reboots, you might need to add `eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519` to your shell's startup file (e.g., `~/.bashrc`, `~/.zshrc`).

### 6. Add Your Public Key to the Remote Git Service

This is critical. The remote server needs to know your public key to authenticate you.

1.  **Copy your public key:**
    ```bash
    cat ~/.ssh/id_ed25519.pub
    ```
    Copy the entire output, starting with `ssh-ed25519` and ending with `your_email@example.com`.

2.  **Go to your Git hosting service settings:**
    *   **GitHub:** Settings -> SSH and GPG keys -> New SSH key.
    *   **GitLab:** User Settings -> SSH Keys.
    *   **Bitbucket:** Personal settings -> SSH keys.

3.  Paste your public key into the designated field and give it a descriptive title.

### 7. Test the SSH Connection

You can test if your SSH setup is working correctly without cloning a repository.
```bash
ssh -T git@github.com # Replace github.com with your Git server if different
```
*   **First connection:** You might be asked to confirm the authenticity of the host. Type `yes` and press Enter. This adds the host's fingerprint to `~/.ssh/known_hosts`.
*   **Success:** You should see a message confirming successful authentication (e.g., "Hi yourusername! You've successfully authenticated...").
*   **Failure:** If it still fails with `Permission denied (publickey)`, proceed to the next step.

### 8. Inspect `~/.ssh/config`

If you have multiple keys or encounter issues with specific hosts, your `~/.ssh/config` file might be involved.
```bash
cat ~/.ssh/config
```
Look for `Host` entries that might specify a particular `IdentityFile`. For example:
```
Host github.com
  Hostname github.com
  User git
  IdentityFile ~/.ssh/my_github_key
  IdentitiesOnly yes # This forces SSH to only use the specified IdentityFile
```
If you find such an entry, ensure the `IdentityFile` points to the *correct* private key file whose public counterpart is registered on GitHub.

### 9. Use Verbose SSH for Diagnosis

When all else fails, run SSH in verbose mode to get detailed debugging output.
```bash
ssh -vvv git@github.com
```
Look for lines indicating which private keys SSH is trying, where it's looking, and why it's failing. This output often pinpoints the exact problem (e.g., "no mutual signature algorithm", "authentications that can continue: publickey", "Trying private key: /path/to/key").

## Code Examples

Here are the key commands you'll likely use, ready to copy-paste.

```bash
# 1. Generate an SSH key pair (replace email with yours)
ssh-keygen -t ed25519 -C "carmen.ortega@example.com"

# 2. Check and set correct permissions for SSH directory and private key
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519 # Use your private key filename

# 3. Start the ssh-agent (if not running)
eval "$(ssh-agent -s)"

# 4. Add your private key to the ssh-agent
ssh-add ~/.ssh/id_ed25519 # Use your private key filename

# 5. Copy your public key to clipboard (macOS example, adjust for Linux/Windows)
# macOS:
pbcopy < ~/.ssh/id_ed25519.pub
# Linux (requires xclip):
xclip -sel clip < ~/.ssh/id_ed25519.pub

# 6. Test your SSH connection (replace github.com if needed)
ssh -T git@github.com

# 7. Example .ssh/config entry for specific key
# Create/edit ~/.ssh/config and add:
# Host specific-github.com
#   Hostname github.com
#   User git
#   IdentityFile ~/.ssh/id_ed25519_special
#   IdentitiesOnly yes
# Then use: git clone specific-github.com:youruser/yourrepo.git

# 8. Get verbose SSH output for debugging
ssh -vvv git@github.com
```

## Environment-Specific Notes

The `Permission denied (publickey)` error can manifest differently or require specific considerations based on your environment.

### Cloud Virtual Machines (AWS EC2, GCP, Azure VMs)

When working with cloud VMs, SSH keys are fundamental.
*   **Initial Access:** You usually provision a key pair (or use an existing one) when launching an instance. This is the key used to `ssh` *into* the VM from your local machine.
*   **Git Operations from VM:** If you're trying to perform Git operations *from* the VM to a remote Git service (e.g., cloning a private repository from GitHub inside an EC2 instance), you need to set up SSH keys *on the VM itself* just as you would on your local machine. This means generating a new key pair on the VM, adding its public key to your Git service account, and ensuring the `ssh-agent` is running and loaded on the VM.
*   **SSH Agent Forwarding:** A more advanced technique is `ssh-agent` forwarding. This allows your local `ssh-agent` (and thus your local private keys) to be used on the remote VM. This means you don't have to copy your private key to the VM, improving security. You enable it with the `-A` flag when SSHing into the VM: `ssh -A user@your-vm-ip`. Then, Git operations inside the VM will use your local agent. I've seen this used effectively in production CI/CD environments where secrets need to be tightly controlled.

### Docker Containers

Docker containers are ephemeral and isolated, which introduces specific challenges for SSH keys.
*   **During Build (Dockerfile):** If your `Dockerfile` needs to clone private repositories, you cannot rely on an `ssh-agent`. You typically copy the private key into the container *during the build process* (which is generally discouraged due to security risks, as the key might end up in intermediate layers), or use multi-stage builds to only include necessary artifacts. A safer approach for private repos during builds is often to use deploy tokens or `git config --global url."https://oauth2:TOKEN@github.com".insteadOf "git@github.com"`.
*   **During Runtime:** For containers running Git operations, you can:
    *   **Mount the `~/.ssh` directory:** `docker run -v ~/.ssh:/root/.ssh ...`. This makes your local keys available inside the container. Be cautious with permissions.
    *   **SSH Agent Forwarding:** If you're running a Docker container from an SSH session that has agent forwarding enabled, you can sometimes forward the agent into the container. This is complex and often requires `socat` or similar tools.
    *   **Dedicated Keys:** Generate a specific key for the container, add its public key to your Git service, and mount only that key into the container.

### Local Development Environment

This is the primary scenario covered in the "Step-by-Step Fix" section. The key considerations are:
*   Ensuring your `~/.ssh` directory exists and has correct permissions.
*   Having an `id_rsa` or `id_ed25519` key pair.
*   Making sure the `ssh-agent` is running and your key is added, especially if it has a passphrase.
*   Verifying your public key is registered with the remote Git service.
*   Managing multiple keys with `~/.ssh/config` if you have different identities for different services or accounts.

## Frequently Asked Questions

**Q: Can I use an SSH key with a passphrase?**
A: Yes, and it's highly recommended for security. When you add a passphrase-protected key to the `ssh-agent` using `ssh-add`, you'll be prompted for the passphrase once. The `ssh-agent` then holds the decrypted key in memory, so you won't need to re-enter the passphrase for subsequent operations in that session.

**Q: I have multiple SSH keys (e.g., one for work, one for personal projects). How do I manage them?**
A: Use the `~/.ssh/config` file. You can define specific keys for different hosts. For instance:
```
Host github.com-personal
  Hostname github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_personal
  IdentitiesOnly yes

Host github.com-work
  Hostname github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_work
  IdentitiesOnly yes
```
Then, when cloning or interacting with repositories, you use the alias in the URL: `git clone github.com-personal:youruser/personal-repo.git`.

**Q: Why does it work on my old machine but not on my new one?**
A: This usually means your new machine is missing one or more of the crucial components: your private key, the `ssh-agent` setup, or the public key registered on the remote service. Go through the "Step-by-Step Fix" section on your new machine; specifically, ensure the private key is copied over (and has correct permissions), the `ssh-agent` is running, and the key is added to it.

**Q: Is it safe to store my SSH private key without a passphrase?**
A: While convenient, storing a private key without a passphrase is a significant security risk. If someone gains access to your machine, they gain immediate access to any system authenticated with that key. A passphrase provides an extra layer of protection, requiring an attacker to know both the key and the passphrase.

**Q: How do I remove an SSH key from the `ssh-agent`?**
A: To remove a specific key: `ssh-add -d ~/.ssh/id_ed25519`. To remove all keys: `ssh-add -D`. This is useful if you've added a temporary key or need to switch identities.

## Related Errors