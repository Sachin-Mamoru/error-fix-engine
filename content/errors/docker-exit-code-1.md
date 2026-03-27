# Docker container exited with code 1
> Encountering "Docker container exited with code 1" means your container's main process terminated with a generic error; this guide explains how to diagnose and fix it.

## What This Error Means
When a Docker container exits with code 1, it's a clear signal that the primary process running inside the container terminated abnormally. It's crucial to understand that `exit code 1` is a generic status code, typically indicating a non-specific error or an unhandled exception within the application itself, rather than a problem with Docker as a platform. Docker simply reports that the process it was managing exited with this code. This means the issue isn't usually with Docker failing to start or run the container, but rather with what the container was *trying* to do. The application or script configured as the container's `CMD` or `ENTRYPOINT` simply failed and returned a non-zero exit status, conventionally signifying an error.

## Why It Happens
The `exit code 1` occurs because the main process running inside your container stops unexpectedly and returns a non-zero exit status. Unlike `exit code 0`, which indicates a clean shutdown, `1` signals a problem. From Docker's perspective, its job is done: it launched the process, and the process exited. Docker doesn't inherently know *why* the application failed; it just reports the outcome.

In my experience, this usually points to an issue with the application's environment, its configuration, or the application code itself. It could be anything from a missing file to a critical bug that causes the process to crash. Docker simply orchestrates the environment; the application running within that environment dictates its own success or failure.

## Common Causes
Pinpointing the exact reason for an `exit code 1` can feel like searching for a needle in a haystack because of its generic nature. However, certain common scenarios frequently lead to this error:

1.  **Missing Dependencies or Files:** The application inside the container might be looking for a file, library, or configuration that isn't present in the image or hasn't been mounted via a volume. This is a very frequent cause, especially if the `Dockerfile`'s `COPY` commands are incorrect or if external configuration isn't provided.
2.  **Incorrect `CMD` or `ENTRYPOINT`:** The command or script specified to run when the container starts might be syntactically incorrect, trying to execute a non-existent binary, or passing the wrong arguments to the application. I've seen this in production when a script path was subtly wrong.
3.  **Application Bugs or Unhandled Exceptions:** If the application code itself has a bug that leads to a crash, or an unhandled exception occurs during startup or early execution, the process will terminate with a non-zero exit code.
4.  **Environment Variable Issues:** The application might rely on specific environment variables that are either missing, misspelled, or set to incorrect values. This is common when migrating an application from one environment to another.
5.  **Permission Problems:** The user inside the container might not have the necessary permissions to read/write files, access specific directories, or execute binaries. This is particularly relevant when working with mounted volumes.
6.  **Resource Constraints (Less Common for Code 1, but possible):** While `exit code 137` typically indicates an Out-Of-Memory (OOM) kill, severe resource starvation (like disk full leading to a write failure) can sometimes manifest as an application-level `exit code 1` if the application isn't designed to handle such conditions gracefully.
7.  **Port Conflicts or Network Issues:** If the application tries to bind to a port that's already in use *within the container's network namespace* (unlikely for `exit 1` but possible if the app exits upon failure to bind), or if it immediately needs to connect to an external service that's unavailable, it might crash.
8.  **Configuration Errors:** Malformed configuration files (e.g., YAML, JSON, INI) that the application attempts to parse at startup can cause immediate termination.

## Step-by-Step Fix
Debugging `exit code 1` requires a systematic approach. Don't jump to conclusions; let the data guide you.

1.  **Check Container Logs First (Always!):**
    This is the most critical step. The container's logs are usually the treasure trove of information that explains why the process exited. Docker captures `stdout` and `stderr` streams, and most applications print their errors there.
    ```bash
    docker logs <container_id_or_name>
    ```
    Look for error messages, stack traces, warnings, or any output that suggests what went wrong immediately before the container stopped. If the logs are empty or unhelpful, the application might be crashing too quickly or not logging to `stdout`/`stderr`.

2.  **Inspect the Container's State:**
    After checking logs, inspect the container's metadata. This gives you details about the command that was executed, environment variables, mounted volumes, and the precise exit code.
    ```bash
    docker inspect <container_id_or_name>
    ```
    Pay close attention to the `"State"` object, specifically `"ExitCode"`, `"Error"`, and `"FinishedAt"`. Also, review `"Config.Cmd"`, `"Config.Entrypoint"`, `"Config.Env"`, and `"HostConfig.Binds"` to ensure what Docker *thought* it was running matches your expectations.

3.  **Run an Interactive Debug Shell:**
    If logs are sparse or the issue is hard to pin down, try to interact with the container's environment directly. Run a new container from the same image, but override its `ENTRYPOINT` or `CMD` to launch a shell (like `bash` or `sh`). This allows you to explore the filesystem, check permissions, and manually execute commands.
    ```bash
    docker run -it --entrypoint /bin/sh <image_name>
    ```
    Once inside the container shell, try:
    *   Navigating to the application's working directory (`cd /app`).
    *   Listing files (`ls -la`).
    *   Checking environment variables (`env`).
    *   Manually executing the application's `CMD` or `ENTRYPOINT` command to see its output directly.

4.  **Verify Your `Dockerfile` and Image Build:**
    Sometimes, the problem isn't at runtime but during the image build itself. Ensure that your `Dockerfile`:
    *   `COPY`s all necessary files.
    *   `RUN`s all required installation commands (e.g., `apt-get install`, `pip install`).
    *   Sets the correct `WORKDIR`.
    *   Defines a valid `CMD` or `ENTRYPOINT`.
    If you've recently changed your `Dockerfile`, try rebuilding the image and carefully reviewing the build logs for any warnings or errors.

5.  **Check Application Code and Configuration:**
    If the logs strongly suggest an application-level error (e.g., a specific line number in a stack trace), you'll need to dive into the application code. Debugging within the container (using `gdb`, `pdb`, `jdwp`, etc.) can be effective, or you might need to replicate the issue in your local development environment outside of Docker first. Ensure any configuration files are correctly formatted and accessible.

6.  **Review Resource Limits:**
    While `exit code 137` is the typical OOM indicator, it's worth a quick check. If your application is memory-hungry and close to the container's memory limit, it *could* sometimes lead to an application crash before the OOM killer steps in cleanly. Use `docker stats` for running containers, or `docker inspect` for `HostConfig.Memory` and `HostConfig.MemorySwap`.

7.  **Ensure Correct Environment Variables and Volume Mounts:**
    Double-check that all required environment variables are passed correctly, especially when using `docker run -e` or `docker-compose.yml` `environment` sections. Similarly, confirm that volumes are mounted to the correct paths inside the container and that the container has the necessary permissions to access them.

## Code Examples

**1. Checking Logs for a Container:**
This is your first line of defense.
```bash
docker logs my_app_container
```
Example output (hypothetical Python app error):
```
Traceback (most recent call last):
  File "/app/main.py", line 5, in <module>
    raise ValueError("Failed to load critical configuration")
ValueError: Failed to load critical configuration
```
This clearly indicates an application-level `ValueError`.

**2. Inspecting Container Details:**
Useful for confirming `CMD`, `ENTRYPOINT`, and `ExitCode`.
```bash
docker inspect my_app_container --format "{{json .State.ExitCode}}"
docker inspect my_app_container --format "{{json .Config.Cmd}}"
docker inspect my_app_container --format "{{json .Config.Entrypoint}}"
docker inspect my_app_container --format "{{json .Config.Env}}"
```
Example output for exit code:
```json
1
```
Example for `CMD`:
```json
[
    "python",
    "main.py"
]
```

**3. Running an Interactive Debug Shell:**
To explore the environment inside the container.
```bash
docker run -it --rm --name debug_shell my_image_name /bin/bash
```
Inside the container:
```bash
# Check current directory
pwd
# List files to see if expected files are present
ls -la
# Try running the application command manually
python main.py
# If that works, exit and rethink. If it fails, you'll see the error directly.
exit
```

**4. Example `Dockerfile` with a potential `CMD` issue:**
If `app.py` expects arguments, but none are provided, or `python3` isn't installed.
```dockerfile
# Dockerfile
FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
# This CMD might be missing arguments that app.py expects, or app.py itself has an error
CMD ["python", "app.py"]
```

**5. Example `docker-compose.yml` with missing environment variable:**
If `my_service` expects `API_KEY` but it's not set.
```yaml
# docker-compose.yml
version: '3.8'
services:
  my_service:
    image: my_app_image
    environment:
      # API_KEY: "your_secret_key" # Missing this line, if app.py expects it
      DATABASE_URL: "postgresql://user:password@db:5432/mydb"
    ports:
      - "8000:8000"
```

## Environment-Specific Notes

*   **Cloud Deployments (Kubernetes, AWS ECS, Azure Container Apps):**
    In orchestrated environments, debugging `exit code 1` follows similar principles but with added layers.
    *   **Kubernetes:** Use `kubectl logs <pod-name> -c <container-name>` to retrieve logs. `kubectl describe pod <pod-name>` provides extensive details, including events, container restart counts, environment variables, and mounted volumes. If `kubectl logs` is empty, check `kubectl describe` for `CrashLoopBackOff` events. You can also `kubectl exec -it <pod-name> -- /bin/bash` to get a shell inside a *running* container (if it manages to stay up).
    *   **AWS ECS:** Logs are typically sent to CloudWatch Logs. Check the task's logs in the CloudWatch console. Use `aws ecs describe-tasks` for detailed information on task status, exit codes, and container definitions. Ensure your Task Definition's `command` and `entryPoint` are correct.
    *   **Resource Limits:** Cloud platforms often enforce strict resource limits. While `exit code 137` is for OOM, inadequate CPU or I/O resources can sometimes starve an application, leading to internal errors that result in `exit code 1`. Always review resource requests and limits in your deployment manifests (e.g., Kubernetes `resources` section).

*   **Local Development:**
    Local debugging is often the easiest due to direct access to code and Docker. You can easily modify `Dockerfile`s, rebuild images, and re-run containers quickly. Using `docker run -it --entrypoint /bin/sh` is particularly effective here. You also have the advantage of running the application directly on your host machine to confirm if the issue is Docker-related or purely application-logic related. I find it beneficial to ensure the application works natively before attempting containerization, if possible.

*   **CI/CD Pipelines:**
    If `exit code 1` occurs during a CI/CD pipeline (e.g., in a build or test stage), the logs from your CI/CD platform are paramount. These logs often contain the `docker build` or `docker run` commands and their outputs, which can reveal issues related to dependency installation, test failures, or environment setup specific to the pipeline's execution agent. Make sure the environment variables and secrets are correctly passed to the pipeline.

## Frequently Asked Questions

**Q: Is `exit code 1` always a Docker problem?**
**A:** No, almost never. `Exit code 1` signifies an error within the application or script running inside the container, not with the Docker daemon or runtime itself. Docker is merely reporting the exit status of the process it launched.

**Q: How do I distinguish `exit code 1` from `exit code 137`?**
**A:** `Exit code 1` is a generic application-level error. `Exit code 137` specifically indicates that the container was killed by an external signal, most commonly due to an Out-Of-Memory (OOM) event. If you see `137`, your container likely ran out of allocated memory.

**Q: My container logs are empty, but I still get `exit code 1`. What now?**
**A:** If logs are empty, the application might be crashing too quickly for output to be captured, or it might not be configured to log to `stdout`/`stderr`. Your best bet is to use `docker run -it --entrypoint /bin/sh <image_name>` to get an interactive shell inside the container. Then, manually execute the container's `CMD` or `ENTRYPOINT` command to observe its behavior and any error output directly.

**Q: Can local antivirus software or firewalls cause a container to exit with code 1?**
**A:** While less common for a generic `exit code 1` (more common for network connectivity issues or failed starts), certain overly aggressive antivirus or firewall settings *could* potentially interfere with container processes, file access, or network calls, leading to an application crash. It's worth testing with them temporarily disabled if all other debugging steps fail on a local machine.

## Related Errors
*(none)*