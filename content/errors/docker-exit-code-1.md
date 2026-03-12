# Docker container exited with code 1
> Encountering "Docker container exited with code 1" means your container's main process terminated with a non-zero exit status, indicating an error; this guide explains how to diagnose and fix it.

## What This Error Means

When a Docker container exits with code 1, it signifies that the primary process running inside the container terminated unsuccessfully. In the Unix/Linux world, an exit code of `0` generally indicates success, while any non-zero value, particularly `1`, signals that something went wrong. This isn't an error *from* Docker itself, but rather an error *reported by* the application or script that Docker was asked to run. Docker simply observes the exit status of the `CMD` or `ENTRYPOINT` process it's managing and propagates that status.

Think of it as your application explicitly saying, "I tried to do something, but I failed." Docker's role here is primarily as an observer and executor. It launches your container, runs your specified command, and if that command exits with a non-zero status, Docker reports it to you. This generic nature means `exit code 1` can mask a vast array of underlying problems, from application-level bugs to configuration mistakes.

## Why It Happens

The root cause of an `exit code 1` is always tied to the main process within your container failing to complete its intended execution gracefully. This could be during startup, mid-operation, or even during shutdown if a critical finalization step fails. Docker's job is to keep the container running as long as its `ENTRYPOINT` or `CMD` process is active. When that process terminates, Docker stops the container. If it terminates with a non-zero code, Docker relays that code.

In my experience, this usually boils down to the application itself encountering a critical error it couldn't recover from, leading it to shut down. It's rarely an issue with Docker failing to *launch* the container, as those usually manifest as different error messages (e.g., image not found, permission denied for Docker daemon operations). If you see `exit code 1`, it means your application *started* within the container environment, but then failed internally.

## Common Causes

Diagnosing `exit code 1` often feels like detective work. Here are the most common culprits I've encountered:

*   **Application-Level Errors:** This is the most frequent cause.
    *   **Uncaught Exceptions:** A bug in your code, such as a `NullPointerException` in Java, an `IndexError` in Python, or an unhandled promise rejection in Node.js, can cause the application to crash and exit.
    *   **Runtime Errors:** Errors during application startup, like failure to connect to a required database, misconfigured environment variables, or missing configuration files.
    *   **Syntax Errors:** While often caught earlier, sometimes runtime compilation or script interpretation can hit a syntax error that leads to an immediate exit.
*   **Missing Dependencies or Files:**
    *   **Library Not Found:** Your application might require a specific shared library (`.so`, `.dll`) that isn't present in the container image.
    *   **Missing Packages:** A crucial package (e.g., `git`, `curl`, `jq`) that your `ENTRYPOINT` script or application relies on might be missing from the base image or wasn't installed during the `Dockerfile` build.
    *   **Missing Application Files:** `COPY` commands in your `Dockerfile` might have failed, or you forgot to copy essential application code into the image.
*   **Incorrect Configuration:**
    *   **Environment Variables:** Critical environment variables (e.g., database connection strings, API keys) might be missing or incorrectly set, causing the application to fail at startup.
    *   **Volume Mounts:** If your application expects a file or directory at a certain path via a volume mount, and that mount isn't correctly configured or the source doesn't exist, it can cause startup failure.
    *   **Network Configuration:** While less direct, an application failing to bind to a port or connect to an external service might trigger an exit.
*   **Permissions Issues:**
    *   The application tries to write to a directory where it doesn't have permissions (e.g., writing logs to `/var/log` as a non-root user without proper setup).
    *   The application tries to execute a script or binary that doesn't have executable permissions.
*   **Incorrect `ENTRYPOINT`/`CMD`:**
    *   The command specified in your `Dockerfile` (`ENTRYPOINT` or `CMD`) might be incorrect, misspelled, or point to a non-existent executable. Docker will attempt to run it, fail, and the shell might return `exit code 127` (command not found) or `1` if it's a script that errors out early.
    *   Sometimes, people omit `exec` in shell-form `ENTRYPOINT` or `CMD`, causing the shell to become PID 1 and gracefully handle signals, but if the child process exits with error, the shell then exits with that error.
*   **Resource Exhaustion:**
    *   **Out of Memory (OOM):** The application consumes too much memory, and the operating system's OOM killer terminates it. This often results in `exit code 137` (128 + signal 9 for SIGKILL), but can sometimes manifest as `1` if the application catches the signal and exits cleanly, or if the OOM happens *before* a signal handler.
    *   **CPU Limits:** If the application requires more CPU than allocated and gets stuck in a loop, it might fail.

## Step-by-Step Fix

Here’s my go-to troubleshooting process when I hit an `exit code 1`:

1.  **Check Docker Container Logs Immediately:** This is your absolute first step. Docker logs are the primary source of information from inside the container. Look for stack traces, specific error messages, or warnings that occurred just before the container exited.

    ```bash
    docker logs <container_id_or_name>
    ```

    If the container exited very quickly, you might not see much. If you're using `docker-compose`, use `docker-compose logs <service_name>`.

2.  **Inspect the Container's Final State:** The `docker inspect` command can give you valuable metadata about how the container exited, including the exact exit code and any associated error messages Docker might have captured.

    ```bash
    docker inspect <container_id_or_name> | grep -E "ExitCode|Error"
    ```

    Pay close attention to `State.ExitCode` and `State.Error`.

3.  **Run the Container Interactively for Debugging:** The best way to diagnose issues is to step inside the container environment. Launch your image with an interactive shell and try to reproduce the problem or manually execute your `ENTRYPOINT`/`CMD`.

    ```bash
    docker run -it --rm <image_name> /bin/bash # or /bin/sh if bash isn't installed
    ```

    Once inside:
    *   Manually execute your container's `CMD` or `ENTRYPOINT` command. Watch for any errors.
    *   Check for missing files: `ls -la /app`, `cat /app/config.json`.
    *   Check environment variables: `env` or `printenv`.
    *   Verify dependencies: `which python`, `pip list`, `ldd /usr/local/bin/my_app`.
    *   Check permissions: `ls -la /data`. Try creating a file: `touch /data/test.txt`.

4.  **Review Your Dockerfile:** The `Dockerfile` is the blueprint for your image. Errors here can lead to missing files, incorrect permissions, or flawed `ENTRYPOINT`/`CMD` definitions.
    *   Ensure all `COPY` commands are moving the correct files.
    *   Check `RUN` commands for any failed package installations or script executions.
    *   Verify the `ENTRYPOINT` and `CMD` are exactly what you intend to run and that the specified paths are correct within the container.

5.  **Verify Configuration and Environment Variables:** If your application relies on external configuration, ensure it's correctly provided.
    *   Double-check `docker run -e` flags or environment sections in `docker-compose.yml`.
    *   Ensure any volume mounts (`-v`) are correctly mapping host paths to container paths, and that the files expected by your application exist on the host.

6.  **Test Resource Limits:** If you suspect memory issues, try running the container with increased memory limits using `-m` in `docker run` or the `mem_limit` option in `docker-compose.yml`. While OOM usually gives `exit code 137`, I've seen this manifest as `1` in some application frameworks.

    ```bash
    docker run -it --rm -m 2g <image_name> /bin/bash
    ```

7.  **Simplify and Isolate:** If you're still stuck, try to simplify your application or `Dockerfile`. Can you get a barebones version of your app to run? Can you run just `sleep 3600` in the image to confirm Docker can launch it? This helps isolate whether the problem is with Docker, the image, or your application code.

## Code Examples

Here are some common commands and scenarios you'll use:

**1. Checking logs of an exited container:**

```bash
# Assuming your container was named 'my-web-app' or has an ID like 'abcdef123456'
docker logs my-web-app
```

**2. Inspecting the container's exit details:**

```bash
docker inspect my-web-app | jq '.[].State | {Status, Running, Paused, Restarting, OOMKilled, Dead, Pid, ExitCode, Error, StartedAt, FinishedAt}'
```
*(Requires `jq` for pretty printing; remove `| jq ...` if not installed.)*

**3. Running an image interactively to debug:**

```bash
# Replace 'my-app-image:latest' with your image name
# Replace '/bin/bash' with '/bin/sh' if bash is not available in your image
docker run -it --rm my-app-image:latest /bin/bash
```

Inside the container:
```bash
# Try to run your app's main command
python /app/main.py
# Or check environment variables
env
# Or check file permissions
ls -la /app
```

**4. Example of a `Dockerfile` causing `exit code 1` (missing dependency):**

```dockerfile
# Dockerfile_broken
FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt .
COPY app.py .
# MISSING: RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```
`requirements.txt`:
```
requests
```
`app.py`:
```python
import requests
import os

print("Starting application...")
try:
    response = requests.get("https://www.example.com")
    print(f"Fetched example.com: {response.status_code}")
except Exception as e:
    print(f"Error fetching: {e}")
    # Application exits with code 1 due to missing 'requests' module
    exit(1)

print("Application finished successfully.")
```

**5. Corrected `Dockerfile`:**

```dockerfile
# Dockerfile_fixed
FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt .
COPY app.py .
# FIXED: Install dependencies
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

## Environment-Specific Notes

The general troubleshooting steps apply across environments, but certain aspects differ:

*   **Local Development (Docker Desktop, native Docker CLI):**
    *   **Pros:** Direct access to `docker logs`, `docker exec`, and `docker inspect`. You control the host machine, making volume mounts and network configurations relatively straightforward. Quick iteration times.
    *   **Cons:** Your local environment might not perfectly mirror production (e.g., different host OS, different network setup), leading to "works on my machine" syndrome. Resource limits are often less constrained locally, masking OOM issues.

*   **Cloud Environments (Kubernetes, AWS ECS, Azure Container Instances, Google Cloud Run):**
    *   **Pros:** Centralized logging solutions (CloudWatch, Stackdriver, Azure Monitor Logs) provide a more robust way to gather logs from potentially many containers. Integrated health checks and restart policies.
    *   **Cons:** Direct `docker exec` access might be limited or require specific permissions. You'll often interact with the orchestrator's CLI (e.g., `kubectl logs`, `aws ecs execute-command`) rather than raw `docker` commands. Debugging can be trickier as you might not have full control over the host node or the ability to run arbitrary debug containers in production clusters. I've seen this in production when a service starts up fine locally but fails in Kubernetes due to a missing ConfigMap or Secret that wasn't properly mounted.

*   **Docker Compose:**
    *   **Pros:** Excellent for multi-service local development. Configuration is declarative in `docker-compose.yml`. `docker-compose logs` provides aggregated output, and `docker-compose exec` allows shell access.
    *   **Cons:** Can sometimes hide nuanced Docker daemon issues behind the Compose abstraction.

Regardless of environment, the principle remains: get to the logs, understand the process's final state, and try to replicate the failure in an isolated, interactive environment.

## Frequently Asked Questions

**Q: What's the difference between `exit code 1` and `exit code 137`?**
**A:** `exit code 1` is a generic error reported by the application itself, indicating it terminated unsuccessfully. `exit code 137` (`128 + 9`) specifically means the container process was terminated by an external SIGKILL signal. This often points to the container running out of memory and being terminated by the host's OOM (Out Of Memory) killer.

**Q: My container works locally but fails in CI/CD with `code 1`. Why?**
**A:** This is a common scenario. Likely causes include:
    1.  **Environmental Differences:** Missing environment variables, different file paths, or network access issues in the CI/CD environment.
    2.  **Resource Constraints:** CI/CD runners might have stricter CPU/memory limits than your local machine, leading to OOM or timeout issues.
    3.  **Dependency Discrepancies:** The base image or installed packages might differ slightly, or a `pip install` or `npm install` command might fail silently in CI/CD build stages.
    4.  **Secrets/Configuration:** Secrets injection mechanisms (e.g., Kubernetes Secrets, AWS Secrets Manager) might not be correctly configured in CI/CD, leading to missing credentials.

**Q: How can I prevent this error in the future?**
**A:**
    1.  **Robust Logging:** Implement comprehensive logging in your application to capture errors and important startup information.
    2.  **Health Checks:** Use Docker's `HEALTHCHECK` instruction or orchestrator-specific health probes (Kubernetes `livenessProbe`, `readinessProbe`) to proactively monitor application status.
    3.  **Defensive Coding:** Implement proper error handling and graceful shutdown procedures in your application code.
    4.  **Reproducible Builds:** Ensure your `Dockerfile` is deterministic and that all dependencies are explicitly managed and versioned.
    5.  **Automated Testing:** Integrate unit, integration, and end-to-end tests into your CI/CD pipeline to catch issues early.

**Q: Can Docker itself cause an `exit code 1`?**
**A:** Rarely directly. If Docker fails to *start* the `ENTRYPOINT` or `CMD` process (e.g., the specified executable doesn't exist), it might report a different error (e.g., `exit code 127` for "command not found" from the shell wrapping your CMD) or fail to create the container entirely. An `exit code 1` almost exclusively originates from the application process *after* Docker has successfully launched it.

## Related Errors
*(None at this time.)*