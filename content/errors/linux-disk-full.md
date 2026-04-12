# Linux No space left on device (ENOSPC)
> Encountering the "No space left on device" error means your disk partition has run out of free space or inodes; this guide explains how to diagnose and resolve it.

## What This Error Means
The "No space left on device" error, indicated by the `ENOSPC` error code, is a critical system message in Linux that signals a storage-related problem. At its core, it means your operating system, or an application attempting to write data, has run out of available capacity on a particular filesystem. This isn't just about megabytes or gigabytes; it can mean one of two things: either there are no free data blocks left (the traditional understanding of "disk full"), or, less commonly but often more puzzlingly, there are no free *inodes* left. Inodes are data structures that store metadata about files and directories (permissions, ownership, timestamps, location of data blocks), and each file or directory requires one. When you hit `ENOSPC`, any operation that attempts to write new data or create new files will fail, often leading to application crashes, system instability, or even preventing crucial logs from being written.

## Why It Happens
This error typically occurs because a filesystem has reached its maximum capacity. When an application tries to create a new file, write to an existing file, or even just create a temporary file, the operating system checks if there's enough space. If there isn't, the write operation fails with `ENOSPC`.

The "why" can often be traced back to either an overwhelming amount of data being written, or a lack of proper cleanup. For instance, log files might grow unchecked, temporary directories might accumulate junk, or a build process might create thousands of small intermediate files. In my experience, the less intuitive cause — inode exhaustion — often catches developers off guard. You might see `df -h` report plenty of free space, but `df -i` tells a different story: all inodes are used up. This happens when there are a huge number of very small files, each consuming an inode, even if they collectively don't use much block space.

## Common Causes
In my career, I've seen `ENOSPC` crop up in various scenarios, and pinpointing the exact cause requires systematic investigation. Here are the most common culprits:

*   **Excessive Log Files:** Uncontrolled logging is a frequent cause, especially in production environments. Application logs, web server access logs (Nginx, Apache), and system logs (`/var/log`) can grow rapidly if not properly rotated and compressed. I've seen a single misconfigured application fill an entire root partition with gigabytes of verbose logs.
*   **Accumulated Temporary Files:** Many applications create temporary files for various operations. If these applications crash, are terminated improperly, or simply don't have robust cleanup routines, `/tmp`, `/var/tmp`, and user-specific temporary directories (e.g., `~/.cache`, `~/.npm`) can become bloated.
*   **Application-Specific Data Overload:** Databases with large datasets, caches that aren't pruned, or file upload directories that are never cleaned can consume vast amounts of space. For example, a development server might accumulate many old Docker images or Maven/Gradle caches.
*   **Failed Backups or Snapshots:** Sometimes, backup processes fail midway, leaving partial backups that take up space. Or, older backups might not be automatically purged, leading to an accumulation of large archives.
*   **Package Manager Caches:** Tools like `apt`, `yum`, or `dnf` keep downloaded package files in caches (`/var/cache/apt/archives`, `/var/cache/yum`) to speed up future installations. While useful, these can grow quite large over time.
*   **Inode Exhaustion:** This is trickier. It happens when you have millions of very small files. Common examples include mail queues, web server session files, build artifacts (e.g., `node_modules` with deep dependency trees, Java `.class` files), or file systems used for temporary storage by applications that generate many tiny files. `git` repositories with lots of small files, or even `~/.config` directories for some applications, can contribute.

## Step-by-Step Fix
Addressing `ENOSPC` requires a systematic approach to identify and clear space. Always proceed with caution, especially when deleting files in production environments.

1.  **Identify the Full Partition:**
    Start by determining which filesystem is full. The `df -h` command will show disk usage in a human-readable format. Look for partitions with 100% (or close to 100%) usage.

    ```bash
    df -h
    ```

    You might see something like:
    ```
    Filesystem      Size  Used Avail Use% Mounted on
    /dev/vda1        20G   20G     0 100% /
    tmpfs           3.9G     0  3.9G   0% /dev/shm
    ```
    Here, `/dev/vda1` mounted at `/` (the root filesystem) is full.

2.  **Check for Inode Exhaustion:**
    If `df -h` shows plenty of free space but you're still getting `ENOSPC`, your problem is likely inode exhaustion. Use `df -i` to check inode usage.

    ```bash
    df -i
    ```

    If `IUse%` is near 100% for the problematic partition, then you have too many small files.

3.  **Find Large Files and Directories (for block space issues):**
    Navigate to the mount point of the full partition (e.g., `/` or `/var`). Use `du -sh *` to find the largest directories. Recursively drill down until you find the culprits. Remember to include hidden directories (`.[!.]*`).

    ```bash
    # Start at the root (or problematic mount point)
    sudo du -sh /*
    sudo du -sh /.[!.]* # Check hidden directories at root, e.g., /.snapshot

    # Example: if /var is large, check within /var
    sudo du -sh /var/*

    # Example: if /var/log is large, check within /var/log
    sudo du -sh /var/log/*
    ```
    Once you've identified large files or directories, you can make informed decisions about deletion. For instance, I've often found massive `docker` directories or uncleaned database backups.

4.  **Analyze Inode Usage (for inode issues):**
    If `df -i` indicated inode exhaustion, you need to find where all the small files are. This command can help pinpoint directories containing a high number of files:

    ```bash
    sudo find /path/to/full/partition -xdev -printf '%h\n' | sort | uniq -c | sort -rh | head -n 20
    ```
    Replace `/path/to/full/partition` with the actual mount point (e.g., `/`). This command finds the 20 directories with the most files.

5.  **Clear Temporary Files:**
    *   **System-wide temporary files:** `sudo rm -rf /tmp/*` (use with extreme caution, only if you're sure no critical applications are actively using files in `/tmp`).
    *   **User-specific caches:** `rm -rf ~/.cache/*`, `~/.npm/_cacache`, `~/.gradle/caches`.
    *   **Package manager caches:**
        *   Debian/Ubuntu: `sudo apt clean`
        *   CentOS/RHEL: `sudo yum clean all` or `sudo dnf clean all`

6.  **Rotate and Compress Logs:**
    *   Manually delete old log files:
        ```bash
        # Example: Delete .log files older than 7 days in /var/log/my_app
        sudo find /var/log/my_app -name "*.log" -mtime +7 -delete
        ```
    *   Configure `logrotate` for critical applications. Most default installations handle system logs, but custom applications might need manual configuration.
    *   Consider compressing older logs rather than outright deleting them: `gzip old_log_file.log`.

7.  **Identify and Remove Old/Unused Files:**
    *   **Find large files:**
        ```bash
        sudo find / -xdev -type f -size +1G -print0 | xargs -0 du -h | sort -rh | head -n 10
        ```
        This lists the 10 largest files (over 1GB) on the root filesystem. Adjust `-size` and path as needed.
    *   **Docker cleanup:** `docker system prune -a` (removes all stopped containers, unused networks, dangling images, and build cache). This is often a massive space saver for Docker hosts.
    *   **Git repositories:** Large `.git` directories, especially from monorepos or heavily history-rewritten repos, can be cleaned with `git gc --prune=now`.

8.  **Extend the Filesystem (Last Resort):**
    If cleanup isn't sufficient, or if the system is genuinely undersized, you might need to extend the filesystem. This usually involves:
    *   Resizing the underlying logical volume (LVM) or cloud disk (e.g., AWS EBS, Azure Disks).
    *   Then, extending the filesystem itself (`resize2fs` for ext4, `xfs_growfs` for XFS). This typically requires root privileges and some downtime, or at least unmounting/remounting for some file systems.

## Code Examples

**Check Disk Space Usage (Human Readable):**
```bash
df -h
```

**Check Inode Usage:**
```bash
df -i
```

**Find Top 10 Largest Directories from Current Location:**
```bash
sudo du -sh * | sort -rh | head -n 10
```

**Find Top 10 Directories with the Most Files (Inode-heavy check, from root):**
```bash
sudo find / -xdev -printf '%h\n' | sort | uniq -c | sort -rh | head -n 10
```

**Delete Log Files Older Than 30 Days in a Specific Directory:**
```bash
sudo find /var/log/nginx -name "*.log" -mtime +30 -delete
```
*Note: Be very careful with `find ... -delete`.*

**Clean APT Package Cache (Debian/Ubuntu):**
```bash
sudo apt clean
```

**Clean YUM/DNF Package Cache (CentOS/RHEL):**
```bash
sudo yum clean all
# or
sudo dnf clean all
```

**Remove Old Docker Images, Containers, Volumes, and Networks:**
```bash
docker system prune -a
```

**Find Largest Files (over 500MB) on the Root Filesystem:**
```bash
sudo find / -xdev -type f -size +500M -print0 | xargs -0 du -h | sort -rh | head -n 10
```

## Environment-Specific Notes

*   **Cloud Environments (AWS EC2/EBS, Azure VMs/Disks, GCP Compute Engine/Persistent Disks):**
    Cloud providers make resizing volumes relatively straightforward. If you're consistently hitting `ENOSPC`, it's often simpler and safer to increase the disk size than to aggressively prune. You'll typically increase the volume size through your cloud console, then connect to the instance and use `resize2fs` or `xfs_growfs` to extend the filesystem to use the newly available space. Monitor disk usage with cloud-native tools (e.g., CloudWatch, Azure Monitor) to proactively prevent issues. I often set up alarms for `DiskUsage > 90%`.

*   **Docker / Containerized Applications:**
    The `ENOSPC` error can occur both *inside* a container and on the *host* filesystem where Docker stores its data.
    *   **Inside a container:** If an application inside a container is logging excessively or creating many temporary files, it can fill up the container's writable layer. This typically means you need to adjust log rotation within the container or remap `/var/log` to a dedicated host volume.
    *   **On the host:** Docker itself can consume a lot of disk space for images, containers, and volumes. The `docker system prune -a` command is invaluable here for clearing out unused resources. Also, remember that volumes mounted from the host will still occupy space on the host's filesystem, so you'll need to check the host's disk usage directly.

*   **Local Development Machines:**
    Local dev environments are notorious for `ENOSPC` due to massive `node_modules` directories, `target/` folders from Java/Rust builds, VM images, or multiple Git repositories with extensive histories.
    *   `npm cache clean --force` or `pnpm store prune` for Node.js.
    *   `cargo clean` for Rust projects.
    *   Deleting old VM images or snapshots.
    *   Manually review and delete large, no-longer-needed project directories.

## Frequently Asked Questions

**Q: `df -h` shows plenty of space, but I still get `ENOSPC`. What gives?**
A: This is almost certainly an inode exhaustion issue. While you have free *data blocks*, you've run out of available *inodes*, meaning no new files (even tiny ones) can be created. Use `df -i` to confirm inode usage.

**Q: Is it safe to delete files while the system is running?**
A: Be cautious. Deleting a file that is still open and being used by a running process will mark the file for deletion, but its disk space won't be freed until the process completely releases its file handle. You might need to restart the process or even the service to free up space immediately. Use `lsof | grep deleted` to find open, deleted files.

**Q: How can I prevent `ENOSPC` from happening again?**
A: Implement proactive monitoring (e.g., `df -h` in cron jobs, Prometheus/Grafana alerts), configure `logrotate` for all critical applications, set up automated cleanup scripts for temporary directories or old backups, and periodically review application configurations that might lead to excessive file creation.

**Q: My root partition is full, and I can't even install `du` or `find` to diagnose! What do I do?**
A: This is a tricky situation. You'll likely need to boot into a rescue mode or a live Linux distribution (e.g., a USB stick). From there, you can mount your problematic root partition, and then use the tools available on the rescue system to diagnose and clean up. Minimal commands like `rm` and `ls` might still work if you can get a shell.

## Related Errors