# Docker container exited with code 1
> Encountering "Docker container exited with code 1" means the main process inside your container failed to complete successfully; this guide explains how to fix it.

## What This Error Means

When a Docker container exits with code 1, it indicates that the primary process running inside the container terminated with a general error. In the Unix operating system, an exit code of `0` traditionally signifies success, while any non-zero exit code denotes some form of failure. Exit code `1` is the most generic failure code.

Unlike specific exit codes like `137` (out of memory) or `126` (command invoked cannot execute), `1` is ambiguous. It simply tells you, "Something went wrong." Docker itself isn't failing here; it's faithfully reporting the exit status of the application or script you tried to run within its isolated environment. Effectively, your container launched, ran its `ENTRYPOINT` or `CMD`, and that process then signaled that it encountered an error before shutting down.

## Why It Happens

The core reason this error appears is that the command or application designated as the container's primary process did not complete its intended execution successfully. This isn't usually a Docker engine problem, but rather a problem with what you're trying to run inside the container.

In my experience, this often points to issues with the application's startup, its configuration, or its environment. The container might have attempted to execute a script that failed due to a syntax error, a program that crashed immediately on launch, or a service that couldn't initialize because of missing dependencies or incorrect parameters. The "why" is almost always found within the container's runtime environment, not in Docker's ability to run it.

## Common Causes

Identifying the root cause of an `exit code 1` requires a systematic approach. Here are the most frequent culprits I've encountered:

1.  **Application Crash/Logic Error:** This is perhaps the most common reason. Your application (e.g., Python script, Node.js app, Java JAR) might have an unhandled exception, a segmentation fault, or a critical logic error that causes it to terminate prematurely.
2.  **Incorrect `ENTRYPOINT` or `CMD`:** The command specified in your `Dockerfile` (or overridden with `docker run`) might be incorrect. This could be a typo, an attempt to run a non-existent executable, or passing invalid arguments to your application.
3.  **Missing Dependencies or Files:** The application within the container might be trying to access files, libraries, or modules that were not included in the Docker image during the build process. This often manifests as "file not found" or "module not found" errors.
4.  **Environment Variable Issues:** Critical environment variables required by your application might be missing, misspelled, or have incorrect values, leading the application to fail during initialization.
5.  **Permissions Problems:** The user inside the container might lack the necessary permissions to read certain files, write to directories, or execute specific commands, especially if you're running as a non-root user.
6.  **Port Conflicts/Binding Issues:** While less common for a generic `exit code 1` (often leading to a more specific error or the application simply failing to start cleanly), if an application tries to bind to a port that's already in use *within the container's network namespace* or experiences other network-related failures during startup, it might exit with code 1.
7.  **Configuration Errors:** Your application might be attempting to load a configuration file that is malformed, missing, or points to non-existent resources (e.g., a database connection string that's invalid).
8.  **Resource Limits (Indirectly):** While an explicit OOM error usually leads to `exit code 137`, an application that fails gracefully (or not so gracefully) when it runs out of CPU or memory *before* the kernel intervenes might exit with code 1.

## Step-by-Step Fix

Troubleshooting `Docker container exited with code 1` follows a methodical path. This is how I approach it every time:

1.  **Check Container Logs First and Foremost:**
    The absolute first step is to check the container's standard output (`stdout`) and standard error (`stderr`). This is where your application usually logs its problems.
    ```bash
    docker logs <container_id_or_name>
    ```
    *   **Action:** Look for stack traces, error messages (e.g., "File not found," "Segmentation fault," "Unhandled exception," "Connection refused"), or any output that indicates why your application stopped. Often, the answer is right there.
    *   **If logs are empty or unhelpful:** This can mean the application crashed so quickly it couldn't log, or it's logging to a file inside the container that isn't streamed to `stdout`/`stderr`. Proceed to the next step.

2.  **Inspect the Container for Exit Details:**
    While `docker logs` gives you application output, `docker inspect` provides detailed runtime information, including the `ExitCode` and any `Error` Docker itself might have captured.
    ```bash
    docker inspect <container_id_or_name> | grep -i 'state\|exitcode\|error'
    ```
    *   **Action:** This confirms the exit code and might reveal a Docker-level error message if the container failed to even start its entrypoint correctly.

3.  **Run the Image Interactively and Test:**
    If logs are unhelpful, the next best thing is to get *inside* the container's environment and try to debug manually.
    ```bash
    # Run a shell inside the container image
    docker run -it --entrypoint /bin/bash <image_name>
    # Or for Alpine/BusyBox
    # docker run -it --entrypoint /bin/sh <image_name>
    ```
    *   **Action:** Once inside the interactive shell, try to manually run the `ENTRYPOINT` or `CMD` command that your `Dockerfile` specifies.
        *   Does the main application command exist? (`ls -l /path/to/your/app`)
        *   Are its dependencies met? (`python myapp.py` or `java -jar myapp.jar`)
        *   Are expected environment variables present? (`echo $MY_VAR`)
        *   Are file permissions correct? (`ls -lR /app/`)
    *   This allows you to reproduce the error in a controlled environment and get immediate feedback.

4.  **Review Your `Dockerfile` and `docker run` Command:**
    Go back to the source.
    *   **`ENTRYPOINT` and `CMD`:** Are they correct? Are you passing the right arguments? I've seen countless typos here.
    *   **`COPY` and `ADD` instructions:** Are all necessary files (application code, config files, scripts) being copied into the image correctly and to the right locations?
    *   **`RUN` instructions:** Did any build-time `RUN` commands (like `pip install -r requirements.txt`) fail during the image build process without you noticing? Check your CI/CD logs if applicable.
    *   **Base Image:** Is the base image appropriate for your application? Does it have the necessary libraries pre-installed?

5.  **Check Environment Variables and Volumes:**
    *   **Environment Variables:** Ensure all expected environment variables are being passed correctly using `-e KEY=VALUE` in `docker run` or defined in your `Dockerfile`. A common mistake is assuming an env var is set when it isn't.
    *   **Volumes:** If you're mounting volumes (`-v /host/path:/container/path`), ensure the content in the host path is what the container expects and that permissions allow the container to read/write as needed.

6.  **Simplify and Isolate:**
    If all else fails, try to reduce your application or `Dockerfile` to its simplest form.
    *   Can you run a basic "Hello World" in the same base image?
    *   Can you comment out parts of your application code until it runs successfully, then reintroduce complexity piece by piece?
    *   This strategy helps isolate if the issue is with your Docker setup or deep within your application's code.

## Code Examples

Here are some concise, copy-paste ready examples for common troubleshooting steps.

**1. Checking Logs of a Stopped Container:**
Assume your container's name is `my-failing-app`.
```bash
docker logs my-failing-app
```
If you only have the ID:
```bash
docker ps -a  # Find the container ID
docker logs <container_id_from_above>
```

**2. Inspecting Container Exit State:**
```bash
docker inspect my-failing-app | grep -E "State|ExitCode|Error"
```
Example Output:
```
        "State": {
            "Status": "exited",
            "Running": false,
            "Paused": false,
            "Restarting": false,
            "OOMKilled": false,
            "Dead": false,
            "Pid": 0,
            "ExitCode": 1,
            "Error": "",
            "StartedAt": "2023-10-27T10:00:00.123456789Z",
            "FinishedAt": "2023-10-27T10:00:00.987654321Z"
        },
```

**3. Running an Interactive Shell in the Container Image:**
This lets you explore the environment and manually run commands. Replace `your-image-name:tag` with your actual image.
```bash
docker run -it --rm --entrypoint /bin/bash your-image-name:tag
```
Once inside, you can:
```bash
ls -l /app
cat /app/config.json
python my_script.py # Try to run your application directly
```

**4. Example of a `Dockerfile` that might cause `exit code 1`:**
Consider this `Dockerfile`:
```dockerfile
# Dockerfile
FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
# CMD tries to run a script that doesn't exist or is misspelled
CMD ["python", "app_main.py"] 
```
If `app.py` is copied, but `CMD` specifies `app_main.py`, the container will exit with code 1 because `python` cannot find `app_main.py`.

## Environment-Specific Notes

The troubleshooting principles remain consistent, but the tools and access methods change across different environments.

*   **Local Development:** This is the easiest environment to debug. You have direct `docker logs`, `docker inspect`, and `docker run -it` access. Iteration is fast. You can also easily modify your `Dockerfile` and rebuild your image. Using `docker-compose` makes managing multiple services and their logs simpler.

*   **Cloud Deployments (e.g., AWS ECS, Kubernetes, Azure Container Instances):**
    *   **Logs are paramount:** You won't have direct `docker run -it` access to a failing production container. Logs are pushed to centralized services (e.g., AWS CloudWatch, Azure Monitor, Kubernetes `kubectl logs`). Ensuring your application logs verbosely to `stdout`/`stderr` is critical.
    *   **Debugging:** For Kubernetes, `kubectl logs <pod-name> -c <container-name>` is your first port of call. For more advanced debugging, `kubectl exec -it <pod-name> -- /bin/bash` can get you an interactive shell *if the container is still running or has not been evicted*. If it's constantly crashing and restarting, you might need to change the pod definition to keep it running for debugging, or deploy a temporary debug container.
    *   **Resource Management:** In these environments, resource limits (CPU, memory) are common. While `exit code 1` is usually application-driven, `OOMKilled` (exit code `137`) can sometimes be preceded by an application exiting with `1` if it detects resource exhaustion before the OOM killer steps in.

*   **CI/CD Pipelines:**
    *   When an `exit code 1` occurs in a CI/CD pipeline, it usually means your image built successfully but failed during the `docker run` or test phase.
    *   **Focus on pipeline logs:** Review the entire build and deploy logs from your CI/CD system (e.g., GitLab CI, Jenkins, GitHub Actions). The verbose output during the `docker run` step will often contain the `docker logs` output, or at least point to where the failure occurred.
    *   **Replicate Locally:** The best strategy is to take the exact image that failed in CI/CD, pull it locally, and try to run it with the same `docker run` command and environment variables as the pipeline used. This often quickly reveals the discrepancy.

## Frequently Asked Questions

**Q: Is `exit code 1` always a critical error?**
**A:** Yes, in the context of Unix-like systems and Docker, any non-zero exit code signifies that the process terminated with an error. While the severity of the underlying issue might vary, the container's designated task did not complete successfully.

**Q: How is `exit code 1` different from `exit code 137`?**
**A:** `Exit code 1` is a generic error code generated by the application itself, indicating a problem within its logic or environment. `Exit code 137` is much more specific: it means the container was forcefully terminated by the operating system, typically because it ran out of memory (OOMKilled). The `137` comes from `128 + SIGKILL`, where `SIGKILL` is signal 9.

**Q: My container logs are completely empty, but it still exits with code 1. What now?**
**A:** If logs are empty, it often means the process crashed extremely early, before it could even initialize its logging system, or it's logging to a file inside the container that isn't streamed to `stdout`/`stderr`. Your next step should be to run the image interactively using `docker run -it --entrypoint /bin/bash <image_name>` and try to manually execute the `ENTRYPOINT`/`CMD` command to see the error output directly in your terminal.

**Q: Can `docker stop` cause a container to exit with code 1?**
**A:** No, `docker stop` sends a `SIGTERM` signal (graceful shutdown) and, after a timeout, a `SIGKILL` (forceful shutdown, resulting in `exit code 137` if not `0`). If your application receives `SIGTERM` and then *explicitly* exits with `1` as part of its shutdown logic, that would be an application-specific behavior, not a direct result of `docker stop` causing a generic failure. Normally, an application should exit with `0` on graceful shutdown.

**Q: What if the problem is specific to the `root` user vs. a non-`root` user?**
**A:** Permissions are a common cause of `exit code 1`. If your `Dockerfile` uses `USER nonrootuser`, ensure that this user has read/write/execute permissions for all necessary files and directories. Try running the container as `root` (by removing or commenting out the `USER` instruction, or using `--user root` with `docker run`) as a diagnostic step. If it works as `root`, you have a permissions issue.

## Related Errors
*(none)*