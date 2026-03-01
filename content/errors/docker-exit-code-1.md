# Docker container exited with code 1
> Encountering "Docker container exited with code 1" means your container's main process terminated unexpectedly; this guide explains how to diagnose and fix it.

## What This Error Means

When a Docker container exits with code 1, it signifies a non-zero exit status from the container's main process. In the world of shell scripting and programming, a non-zero exit code typically indicates that something went wrong during execution. Unlike `exit code 0`, which denotes success, code 1 is a general catch-all for errors. It doesn't tell you *what* went wrong, only *that* it went wrong. This generic nature means the actual cause could be almost anything, from a misconfigured application to missing dependencies, or a syntax error in your startup script.

As a Principal Engineer, I've often found this error to be one of the most common and, at times, frustrating issues to debug, precisely because of its lack of specificity. It's a signal to dig deeper into the container's internal operations.

## Why It Happens

A Docker container's lifecycle is tied directly to its main process (the one executed by `CMD` or `ENTRYPOINT` in your Dockerfile). When this process starts, runs, and then finishes, the container stops. If the process exits successfully (with code 0), the container exits cleanly. If it exits with any other code, particularly code 1, it means the process encountered an unhandled error or an explicit instruction to terminate due due to a problem.

In my experience, this usually points to an issue within the application running inside the container, or with the environment the container provides. It's rarely a Docker daemon problem itself, but rather an issue with how your application interacts with the container runtime. Common culprits include application crashes, failed startup scripts, or resource exhaustion.

## Common Causes

Here are some of the most frequent reasons I've encountered for a Docker container exiting with code 1:

*   **Application Crash/Error:** The most straightforward cause. Your application code (Python, Node.js, Java, Go, etc.) has an unhandled exception or an error that causes it to terminate prematurely.
*   **Incorrect `ENTRYPOINT` or `CMD`:** The command specified to start the container's main process might be incorrect, misspelled, or trying to execute a script that doesn't exist.
*   **Missing Dependencies:** The application inside the container might be missing critical files, libraries, or environment variables it needs to start or run properly. For instance, a database connection string might be missing, or a required package wasn't installed during the image build.
*   **File Permissions Issues:** The user inside the container might not have the necessary permissions to read/write files or execute scripts required for the application to function.
*   **Resource Exhaustion:** While less common for code 1 (which often points to a logical error), memory limits or CPU exhaustion *can* lead to a process being killed and exiting with a non-zero code. This is more often associated with exit code 137 (killed by OOM killer) but can sometimes manifest as code 1 if the application has a specific handler for low-resource conditions.
*   **Configuration Errors:** Environment variables are not set correctly, configuration files are malformed, or required directories are not present.
*   **Port Conflicts:** While typically leading to a hung container or a different error, sometimes an application might crash trying to bind to a port that's already in use, leading to an exit.

I've personally debugged situations where a seemingly minor typo in an `ENTRYPOINT` script or a missing environment variable value from a `.env` file led directly to this error.

## Step-by-Step Fix

When I approach a container exhibiting `exit code 1`, I follow a systematic debugging process.

1.  **Inspect Container Logs First:**
    This is always my first step. The logs are the primary source of information about what happened inside the container.
    ```bash
    docker logs <container_id_or_name>
    ```
    If the container stopped recently, you can often find its name or ID using `docker ps -a`. Look for stack traces, error messages, or any output from your application indicating why it shut down. Pay close attention to the lines immediately preceding the container's exit.

2.  **Examine Container Status and Exit Code:**
    Confirm the container's last status and the precise exit code.
    ```bash
    docker ps -a
    docker inspect <container_id_or_name> --format='{{.State.ExitCode}}'
    ```
    While you know it's `1`, verifying it helps rule out other codes like `137` (OOM kill) or `127` (command not found), which have different root causes.

3.  **Validate `ENTRYPOINT` and `CMD`:**
    Check your Dockerfile or the `docker run` command for `ENTRYPOINT` and `CMD` instructions. Ensure the specified command exists and is executable within the container's context.
    A common issue is a script not having execute permissions. You can fix this in your Dockerfile:
    ```dockerfile
    COPY my-entrypoint.sh /usr/local/bin/
    RUN chmod +x /usr/local/bin/my-entrypoint.sh
    ENTRYPOINT ["/usr/local/bin/my-entrypoint.sh"]
    ```

4.  **Check File Paths and Permissions:**
    If your application interacts with files, volumes, or uses specific configuration files, verify their paths and permissions inside the container.
    *   Does the file exist at the expected path?
    *   Does the user running the application inside the container have read/write access?
    I often debug this by running an interactive shell in a new container based on the same image.

5.  **Review Environment Variables:**
    Missing or incorrect environment variables are a frequent cause. Use `docker inspect` to see the environment variables passed into the container:
    ```bash
    docker inspect <container_id_or_name> --format='{{json .Config.Env}}'
    ```
    Compare these with what your application expects.

6.  **Debug Interactively (Advanced):**
    If logs aren't sufficient, the most effective way to debug is to run an interactive shell inside your container *before* your application starts. This allows you to inspect the filesystem, run commands, and manually attempt to start your application.
    ```bash
    docker run -it --rm --entrypoint /bin/bash <image_name_or_id>
    ```
    Once inside, you can navigate directories, list files (`ls -la`), check environment variables (`env`), and try to run your application's `ENTRYPOINT`/`CMD` manually to see exactly where it fails. If your image doesn't have `bash`, try `sh`.

7.  **Rebuild the Image:**
    Sometimes, the issue stems from a cached layer or an unexpected change during the image build process. A clean rebuild can resolve this, especially if you suspect build-time dependencies or instructions are failing.
    ```bash
    docker build --no-cache -t my-image:latest .
    ```

## Code Examples

Here are some concise, copy-paste ready examples to illustrate common problems and fixes.

**1. Debugging a failed `ENTRYPOINT`:**

Suppose your Dockerfile has an `ENTRYPOINT` script:
```dockerfile
# Dockerfile
FROM alpine:latest
COPY my-script.sh /app/my-script.sh
RUN chmod +x /app/my-script.sh
ENTRYPOINT ["/app/my-script.sh"]
```
And `my-script.sh` looks like this initially (with a typo):
```bash
#!/bin/sh
echo "Starting my application..."
exec non_existent_command # This will fail
```
Running `docker build . -t myapp` and `docker run myapp` will result in `exit code 1`.

To debug:
```bash
# Get container logs
docker logs <container_id>
# Expected output: "/app/my-script.sh: non_existent_command: not found"

# Run interactively to inspect
docker run -it --rm --entrypoint /bin/sh myapp
# Once inside, you can check:
# ls -l /app/my-script.sh
# cat /app/my-script.sh
# Then try to run the problematic part:
# non_existent_command
```
You'd then correct `my-script.sh` to execute the actual application, e.g.:
```bash
#!/bin/sh
echo "Starting my application..."
exec python myapp.py # Assuming a Python app
```

**2. Missing Environment Variable:**

Consider a Python Flask application that requires a `DB_HOST` environment variable:
```python
# app.py
import os
db_host = os.getenv("DB_HOST")
if not db_host:
    print("Error: DB_HOST environment variable not set.")
    exit(1) # Explicitly exit with code 1
print(f"Connecting to database at {db_host}...")
# ... rest of your application
```
If you run this container without setting `DB_HOST`:
```bash
# Running without DB_HOST
docker run my-flask-app
```
It will exit with code 1.

To fix:
```bash
# Running with DB_HOST set
docker run -e DB_HOST=mydb.example.com my-flask-app
```

## Environment-Specific Notes

The `exit code 1` can behave differently or have different debugging implications depending on your environment.

*   **Local Development:** On your local machine, you have full control and can easily run `docker logs` and interactive shells (`docker run -it`). Resource limits are often generous, so resource exhaustion is less likely unless explicitly configured. Debugging is generally the most straightforward here.

*   **CI/CD Pipelines:** In a CI/CD environment (e.g., Jenkins, GitLab CI, GitHub Actions), container exits can halt pipelines. The challenge here is less direct access. You'll rely heavily on pipeline logs which capture `stdout` and `stderr` from your Docker commands. Ensure your CI scripts capture `docker logs` for any failing containers before cleanup. I've seen this in production when a new code change introduces a dependency not installed in the Docker image, leading to a build failure and subsequent container `exit 1` in CI tests.

*   **Production Deployments (Orchestrators like Kubernetes):** In production, `exit code 1` is particularly critical as it means your service is failing. Kubernetes, for instance, will detect the container failure and try to restart it (based on `restartPolicy`). Persistent `exit code 1` will lead to a `CrashLoopBackOff` state. Here, you'll need to check the pod logs (`kubectl logs <pod_name>`), describe the pod (`kubectl describe pod <pod_name>`) for events, and potentially exec into a running pod (if it manages to start even briefly) or deploy a debug-specific pod to diagnose. Cloud-specific logging solutions (CloudWatch, Stackdriver, etc.) become crucial. Resource limits are strictly enforced in production, making memory/CPU issues more plausible, though usually with different exit codes.

## Frequently Asked Questions

**Q: What if `docker logs` are empty or don't show any useful error?**
**A:** This can happen if your application crashes before it can emit any output, or if its output is redirected elsewhere. In this case, your best bet is to use the interactive debugging approach (`docker run -it --rm --entrypoint /bin/bash <image>`) to step through the startup process manually. Also, check if your application explicitly redirects `stderr` or `stdout` to files, which you'd then need to inspect from within the container.

**Q: Is `exit code 1` always a problem with my application code?**
**A:** Not always. While often application-related, `exit code 1` can also be due to environment issues (missing configuration, incorrect file permissions, invalid command in `ENTRYPOINT`/`CMD`) or even an issue with the underlying base image if critical system utilities are missing or broken. However, it *does* originate from the container's main process, not the Docker daemon itself.

**Q: How can I prevent `exit code 1` issues in my CI/CD pipeline?**
**A:** Implement robust health checks (e.g., `HEALTHCHECK` in Dockerfile), comprehensive unit and integration tests that run within containers, and ensure your CI environment accurately mirrors production configurations as much as possible. Capture and analyze `docker logs` in your pipeline outputs for early detection.

**Q: Can Docker's `HEALTHCHECK` instruction help with `exit code 1`?**
**A:** Yes, `HEALTHCHECK` can help diagnose *why* an application might be failing, even if it doesn't directly prevent `exit code 1`. A `HEALTHCHECK` command runs periodically *inside* the container and can report `healthy` or `unhealthy`. If your container starts but immediately becomes `unhealthy`, it gives you an early warning and a specific command to debug, often before the main process might crash with an `exit code 1`.

## Related Errors

*   [docker-permission-denied](/errors/docker-permission-denied.html)