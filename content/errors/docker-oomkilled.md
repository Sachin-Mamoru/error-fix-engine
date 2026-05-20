# Docker OOMKilled – container killed due to out of memory
> Encountering Docker OOMKilled means your container ran out of memory and was terminated; this guide explains how to diagnose and resolve it efficiently.

## What This Error Means

The "Docker OOMKilled" error indicates that your container was terminated by the Linux Out-Of-Memory (OOM) Killer. This happens when a process or group of processes within the container attempts to allocate more memory than is available or permitted to the container. The kernel, in an effort to prevent the entire host system from crashing due to memory exhaustion, selectively kills processes to free up resources. When a Docker container's processes are targeted by the OOM Killer, the container itself stops running, marked with an `OOMKilled` status. In my experience, this is often a critical signal that your application's resource demands are not being met by its allocated environment.

## Why It Happens

At its core, Docker OOMKilled occurs because the memory usage inside a container exceeded its assigned memory limit. Docker containers, by default, share the host's kernel and resources but can be constrained using control groups (cgroups). When you run a Docker container, you can specify a memory limit (`-m` or `--memory`). If this limit is hit, or if the Docker host itself runs critically low on memory, the OOM Killer steps in. It's a protection mechanism. Without it, a runaway process in one container could potentially starve the entire host machine, including other critical services, leading to system instability or a full crash. I've seen this in production when a seemingly minor code change introduced a memory leak, leading to cascading OOMKills across multiple services.

## Common Causes

Identifying the root cause of OOMKilled events can sometimes be a bit of a detective job. Here are the most common culprits I've encountered:

1.  **Application Memory Leaks:** This is perhaps the most insidious cause. Your application might be continuously allocating memory without properly releasing it, leading to a gradual increase in memory footprint until it hits the limit. This could be due to unclosed file handles, unreferenced objects, or growing data structures.
2.  **Insufficient Memory Limits:** The most straightforward cause. The memory allocated to the container (via Docker or orchestrator settings) is simply too low for the application's normal operation, especially under peak load. Default limits are often generous but not always adequate for specific workloads.
3.  **High Traffic/Load Spikes:** An increase in user requests or data processing can significantly boost an application's memory usage. If your memory limits are set based on average load, a sudden spike can push it over the edge.
4.  **Inefficient Code/Algorithm:** Sometimes the application itself is just very memory-hungry due to inefficient data structures, algorithms, or libraries it uses. For example, processing large datasets entirely in memory when a streaming approach would be more suitable.
5.  **Runtime Overhead:** Interpreted languages like Python or Java have their own runtime environments (JVM, Python interpreter) that consume memory in addition to your application code. Garbage collection in Java, for instance, can temporarily increase memory usage. Misconfigured JVM settings can exacerbate this.
6.  **Dependency Bloat:** External libraries or frameworks can introduce significant memory overhead that wasn't accounted for when estimating resource needs.
7.  **Misconfigured Docker Host:** Less common, but if the Docker daemon itself or other processes on the host consume excessive memory, it can indirectly lead to OOMKilled events for containers, even if they aren't explicitly hitting their own limits.

## Step-by-Step Fix

Addressing an OOMKilled error requires a systematic approach.

1.  ### Identify the OOMKilled Event
    First, confirm that the container was indeed OOMKilled.
    ```bash
    docker ps -a
    ```
    Look for containers with `Exited (137)` or `Exited (137) OOMKilled` status. An `Exit Code 137` specifically means the process received a `SIGKILL` signal, which is what the OOM killer sends.
    To get more details, inspect the container:
    ```bash
    docker inspect <container_id_or_name> | grep OOMKilled
    ```
    This will show `OOMKilled: true` if it was.

2.  ### Review Container Logs
    Check the application logs for any clues leading up to the OOM event.
    ```bash
    docker logs <container_id_or_name>
    ```
    Sometimes applications log memory warnings or errors just before termination.

3.  ### Check Current Memory Limits
    Determine what memory limits were applied to the container.
    ```bash
    docker inspect <container_id_or_name> | grep Memory
    ```
    Look for `Memory` and `MemorySwap` under the `HostConfig` section. If no explicit limit was set, it might show `0`, meaning no limit was enforced by Docker, making the host's overall memory the effective limit.

4.  ### Monitor Memory Usage
    While the container is running (if it can start), monitor its memory consumption.
    ```bash
    docker stats <container_id_or_name>
    ```
    This command provides real-time statistics. Observe if memory usage steadily climbs towards the limit or if it spikes suddenly. If you can't run it long enough, consider running a new instance with increased limits temporarily to get a baseline. For more persistent monitoring, tools like `cAdvisor`, Prometheus with Node Exporter, or cloud-native monitoring solutions are invaluable.

5.  ### Profile Application Memory Usage
    This is often the most effective step for identifying memory leaks or inefficient code.
    *   **Python:** Use `memory_profiler`, `objgraph`, or `py-spy`.
    *   **Java:** Use `jstat -gc`, `jmap -heap`, VisualVM, or YourKit.
    *   **Node.js:** Use `heapdump`, `node-memwatch`, or Chrome DevTools for profiling.
    *   **Go:** Use `pprof`.
    Run these tools against your application locally or in a test environment to identify memory-hungry functions or data structures.

6.  ### Adjust Docker Memory Limits
    If monitoring suggests your application legitimately needs more memory than allocated, increase the limits.
    *   **For `docker run`:**
        ```bash
        docker run -m 512m -p 80:80 my-app:latest
        ```
        This sets a memory limit of 512 MB. Experiment with values like `256m`, `1g`, `2g`.
    *   **For `docker-compose`:** Modify your `docker-compose.yml` file.
        ```yaml
        version: '3.8'
        services:
          my-app:
            image: my-app:latest
            ports:
              - "80:80"
            deploy:
              resources:
                limits:
                  memory: 512M # Or 1G, 2G etc.
        ```
        Remember to rebuild and restart your services after changes: `docker-compose up --build -d`.

7.  ### Optimize Application Code
    This is the long-term solution. Based on your profiling results, refactor code to:
    *   Reduce in-memory data structures.
    *   Implement streaming for large data processing.
    *   Fix explicit memory leaks (e.g., closing resources, dereferencing objects).
    *   Tune garbage collection parameters for runtimes like JVM.

8.  ### Scale Host Resources
    If multiple containers on a single host are consistently running into OOM issues, even after increasing individual container limits, the underlying Docker host might simply be undersized. Consider upgrading the host's RAM or distributing your workload across more hosts.

## Code Examples

Here are common ways to set memory limits for Docker containers:

**1. Running a container with a specific memory limit (Docker CLI):**

This command starts a Nginx container with a memory limit of 256 megabytes.

```bash
docker run -d --name my-nginx -p 80:80 --memory="256m" nginx:latest
```

**2. Defining memory limits in `docker-compose.yml`:**

This `docker-compose.yml` snippet configures a service `web` to use a maximum of 1 gigabyte of memory.

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    image: my-backend-app:latest
    ports:
      - "8080:8080"
    environment:
      - JAVA_OPTS="-Xmx768m" # Example for Java apps, ensure this is less than Docker limit
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M # Optional: ensures at least 512MB is available
```

**3. Example Dockerfile for a Python application demonstrating potential memory usage:**

This example demonstrates a Python application that could consume a lot of memory if not handled carefully, potentially leading to OOMKilled.

```python
# app.py
def create_large_list(size):
    # This will consume 'size' * (size_of_int + overhead) bytes
    return list(range(size))

if __name__ == "__main__":
    print("Starting memory-intensive task...")
    # Attempt to create a list of 100 million integers
    # This might easily exceed typical container memory limits
    large_data = create_large_list(100_000_000)
    print(f"Created a list with {len(large_data)} elements.")
    # Simulate work
    import time
    time.sleep(3600) # Keep running to observe memory
```
```dockerfile
# Dockerfile
FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]
```
To test this, build it (`docker build -t my-mem-app .`) and run it with a tight memory limit (`docker run -m 256m my-mem-app`). It will likely get OOMKilled quickly.

## Environment-Specific Notes

The context in which your containers run significantly impacts how you approach OOMKilled issues.

*   **Docker Desktop (Local Development):** On Docker Desktop (Mac, Windows), containers run inside a lightweight Linux VM. The memory available to this VM is configurable. If your containers are frequently OOMKilled locally, first check the Docker Desktop settings for the VM's allocated RAM. Increasing that often solves local development issues, but remember it doesn't fix inefficient application code. It just pushes the problem further down the line. Debugging locally is often easier due to direct access to tools.

*   **Cloud Orchestrators (Kubernetes, AWS ECS, Azure Container Instances):**
    *   **Kubernetes:** Here, `resources.limits.memory` defined in your pod specification is critical. If a container exceeds this limit, Kubernetes will terminate the pod with an OOMKilled event. The node itself also has memory, and if the sum of all pod memory requests/limits exceeds node capacity, scheduling issues or node-level OOM events can occur. For Java applications, it's vital to ensure JVM `Xmx` settings are slightly *less* than the container's memory limit, to account for native memory usage by the JVM.
    *   **AWS ECS/Fargate:** Memory limits are set at the task definition level. For Fargate, you choose a CPU/Memory combination, and the total memory is divided amongst containers in a task. Understanding how memory is shared or dedicated is crucial. I've often seen OOMs on Fargate where the application's runtime overhead was underestimated relative to the chosen task memory.
    Monitoring in these environments is typically done via cloud-native tools (e.g., CloudWatch for AWS, Stackdriver for GCP, Azure Monitor for Azure) integrated with your orchestrator.

*   **Bare Metal / VM Docker Host:** When running Docker directly on a Linux server, containers share the host kernel directly. Memory limits imposed by Docker (`-m`) are enforced by cgroups. If a container with no explicit memory limit consumes too much RAM, it can exhaust the host's memory, leading to the OOM Killer targeting *any* process, potentially even the Docker daemon itself or other crucial system services. This can be more disruptive than an OOM in an orchestrated environment.

## Frequently Asked Questions

**Q: What's the difference between `OOMKilled` and `Exit Code 137`?**
**A:** `OOMKilled` is a specific status reported by Docker, indicating that the container's main process was terminated by the Linux OOM killer. `Exit Code 137` is the generic Unix exit status for a process that was terminated by a `SIGKILL` signal (signal number 9). The OOM killer sends a `SIGKILL`, so an `OOMKilled` status will typically also show `Exit Code 137`.

**Q: How can I prevent OOMKilled errors in my CI/CD pipeline?**
**A:** Integrate memory profiling and load testing into your CI/CD. Run performance tests with realistic load profiles in environments that closely mimic production. Use tools like `docker stats` or cloud monitoring APIs to assert that memory usage stays within acceptable bounds for new builds. Automate this check to fail builds that exceed predefined memory thresholds.

**Q: My container is OOMKilled even when `docker stats` shows plenty of memory available. Why?**
**A:** This can be misleading. `docker stats` shows the current memory usage and limits. The OOMKilled event happens *at the moment* the limit is exceeded. It could be a sudden spike (e.g., during initialization or a specific task) that `docker stats` didn't catch, or `docker stats` might not reflect certain types of kernel-level memory allocations that count towards the limit. Also, ensure you're looking at the *container's* memory limit, not the host's available memory. In some cases, if `MemorySwap` is enabled and exhausted first, it can also lead to OOM.

**Q: Can I disable the OOM Killer for my Docker containers?**
**A:** While theoretically possible to tweak OOM killer scores for processes, it's generally a very bad idea for Docker containers. Disabling it would mean that an out-of-control container could consume all host memory, crashing the entire server and affecting all other services. The OOM Killer is a critical safety net. Instead of disabling it, focus on proper memory management and setting appropriate limits.

## Related Errors
No related errors were specified for this article.