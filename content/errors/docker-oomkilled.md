# Docker OOMKilled – container killed due to out of memory
> Encountering Docker OOMKilled means your container ran out of memory; this guide explains how to identify, prevent, and fix it.

## What This Error Means

The "Docker OOMKilled" error indicates that your container was terminated by the operating system's Out-Of-Memory (OOM) killer. This happens when a process or group of processes on the system, in this case, a Docker container, consumes more memory than it has been allocated or more than the system has available. The kernel, in an effort to maintain system stability and prevent a complete freeze, intervenes and selectively kills processes that are consuming excessive memory.

For a Docker container, this means it has exceeded its defined memory limit (if one was set) or it has exhausted the host machine's available memory. The container process receives a `SIGKILL` signal from the kernel, terminating it abruptly without a chance for graceful shutdown or cleanup. You'll typically see an `Exit Code 137` (which translates to 128 + 9, where 9 is the `SIGKILL` signal) when inspecting the container's status, or a specific `OOMKilled` status in `docker ps -a` output.

## Why It Happens

At its core, Docker OOMKilled occurs because a container attempts to use more memory than it's allowed or available. This can stem from several factors:

1.  **Insufficient Memory Limits:** The most straightforward reason. Docker allows you to set explicit memory limits for containers using the `--memory` flag (`-m`) in `docker run` or `memory` in `docker-compose.yaml`. If your application's actual memory usage exceeds this configured limit, the kernel will kill it.
2.  **Application Memory Leaks:** The application running inside the container might have a bug causing it to continuously allocate memory without releasing it. Over time, its memory footprint grows until it hits a limit. I've seen this in production when a seemingly small change to a data processing pipeline started holding onto references for too long.
3.  **Spikes in Memory Usage:** Even without a leak, an application might have peak memory demands that exceed its typical usage. This could be due to processing a large file, handling a sudden burst of requests, or running a complex query that loads a lot of data into memory.
4.  **Inefficient Memory Usage:** The application might not be written to be memory-efficient. This is common with certain programming languages or frameworks that have higher memory overheads, or when developers don't optimize data structures or algorithms for memory.
5.  **Host Memory Exhaustion:** If no specific memory limits are set for a container, it can consume as much memory as available on the Docker host. If multiple containers are running without limits, or if other processes on the host consume a lot of memory, the entire host can run out of memory, leading to the OOM killer terminating one or more containers (or even other host processes).
6.  **Swap Usage:** While Docker can utilize swap space, excessive swapping can degrade performance significantly. The OOM killer often targets processes even before swap is fully exhausted, especially if the `oom_score_adj` is high for a container process.

## Common Causes

Understanding the "why" helps, but the "what" often looks like one of these scenarios:

*   **Batch Processing:** A service designed to process data in batches might encounter an OOMKilled error when a particularly large batch arrives, exceeding the memory allocated for storing and manipulating that data.
*   **Image/Video Processing:** Applications handling large media files (e.g., resizing high-resolution images, transcoding video) can quickly consume vast amounts of memory if not optimized to process data in chunks or streams.
*   **Database Queries:** An application querying a database might attempt to load an entire result set into memory, especially if the query is not paginated or if the result set grows unexpectedly large. I've personally debugged issues where a simple `SELECT * FROM large_table` without limits caused a backend service to crash.
*   **Caching Layers:** While caches are designed for performance, an overly aggressive or poorly managed cache can grow unbounded, consuming all available memory.
*   **Unoptimized Language Runtimes:** Certain languages (e.g., Java with an unoptimized JVM heap, Node.js with large buffers) might require careful tuning of their runtime settings to fit within container memory limits.
*   **Development vs. Production Discrepancy:** An application running fine in a development environment with ample host memory might crash in a production environment with stricter container limits or more concurrent services.
*   **Third-party Libraries:** Sometimes, the memory bloat isn't from your code directly but from a third-party library that has unexpected memory requirements or leaks.

## Step-by-Step Fix

Fixing Docker OOMKilled requires a methodical approach, starting with identification and moving towards optimization.

### 1. Identify the OOMKilled Event

First, confirm that your container was indeed OOMKilled.

*   **Check container status:**
    ```bash
    docker ps -a
    ```
    Look for containers with `Exited (137)` or `Exited (139)` status and often an explicit `OOMKilled` message.
    ```
    CONTAINER ID   IMAGE          COMMAND       CREATED          STATUS                         PORTS     NAMES
    a1b2c3d4e5f6   my-app:latest  "python app.py"  2 minutes ago    Exited (137) 2 minutes ago OOMKilled  my-app-container
    ```

*   **Inspect container details:**
    ```bash
    docker inspect <container_id_or_name>
    ```
    Look for `"OOMKilled": true` within the `State` section.
    ```json
    [
        {
            "State": {
                "Status": "exited",
                "Running": false,
                "Paused": false,
                "Restarting": false,
                "OOMKilled": true,
                "Dead": false,
                "Pid": 0,
                "ExitCode": 137,
                "Error": "",
                "StartedAt": "2023-10-27T10:00:00.000000000Z",
                "FinishedAt": "2023-10-27T10:02:30.000000000Z"
            }
        }
    ]
    ```

*   **Check Docker daemon logs:** The Docker daemon or system logs (`journalctl -u docker` or `/var/log/syslog`) might contain messages about the OOM killer activity, providing more context.

### 2. Monitor Container Memory Usage

Once confirmed, understand the container's memory consumption patterns.

*   **Real-time monitoring with `docker stats`:**
    ```bash
    docker stats <container_id_or_name>
    ```
    This command shows live memory usage, including the total memory limit. Pay attention to the `MEM USAGE / LIMIT` column. If it consistently approaches or exceeds the limit before crashing, you're on the right track.
    ```
    CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O         PIDS
    a1b2c3d4e5f6   my-app-container    0.12%     1.98GiB / 2.00GiB     99.00%    1.25MB / 968MB    1.36MB / 0B       8
    ```
    In this example, the container is nearly at its 2GiB limit.

*   **Historical monitoring:** If `docker stats` isn't feasible for a crashing container, you'll need a monitoring solution that records historical metrics (e.g., Prometheus/Grafana, Datadog, or your cloud provider's monitoring tools). This helps identify spikes or gradual memory increases leading up to the crash.

### 3. Review Application Memory Footprint

This is where you dig into your application code and runtime.

*   **Profiling:** Use language-specific profiling tools to identify memory-hungry functions, objects, or data structures. For example, `jemalloc` or `valgrind` for C/C++, `pprof` for Go, Java Mission Control for Java, `memory-profiler` for Python.
*   **Heap Dumps:** Generate a heap dump of your application just before it crashes (if possible) or in a controlled environment. Analyzing the heap dump can reveal memory leaks or inefficient object allocations.
*   **Logs:** Application logs might indicate when certain resource-intensive operations are triggered, correlating with memory spikes.

### 4. Adjust Docker Memory Limits

If your application simply needs more memory, or if the current limits are too restrictive, increase them.

*   **For `docker run`:** Use the `--memory` (or `-m`) flag.
    ```bash
    docker run -d --name my-app-container --memory="4g" my-app:latest
    ```
    This sets a hard limit of 4 gigabytes. You can also add `--memory-swap` to control swap usage. `--memory-swap` should always be greater than or equal to `--memory`. If `--memory-swap` is set to `0` or left unset and `--memory` is specified, the container's swap limit will be set to twice the `--memory` value. If `--memory` is not set, the container can use all available memory and swap.

*   **For Docker Compose:** Add `memory` and `mem_swap` under the service definition.
    ```yaml
    version: '3.8'
    services:
      my-app:
        image: my-app:latest
        deploy:
          resources:
            limits:
              memory: 4g
              # memswap: 8g # Optional: If memory is 4g, memswap defaults to 8g without this line.
                            # Set explicitly if you need a different ratio or no swap.
        environment:
          # JVM specific settings, if applicable
          - JAVA_OPTS=-Xmx3G -Xms1G
    ```
    Note that Docker Compose typically uses the `deploy.resources.limits.memory` for memory limits, which is more robust.

### 5. Optimize Application Memory Usage

This is often the most impactful long-term solution.

*   **Refactor code:**
    *   **Data Structures:** Choose more memory-efficient data structures. For example, using a `set` instead of a `list` if order doesn't matter and you only need unique elements, or a generator/iterator instead of loading an entire dataset into memory.
    *   **Lazy Loading/Streaming:** Instead of loading entire files or database results into memory, process them in chunks or use streaming techniques.
    *   **Garbage Collection Tuning:** For languages like Java or Go, tune the garbage collector settings (e.g., JVM `-Xmx`, `-Xms` flags) to better manage heap space within the container's allocated memory.
    *   **Resource Release:** Ensure all allocated resources (file handles, network connections, large objects) are properly released when no longer needed.
*   **Dependencies:** Review the memory footprint of your application's dependencies. Sometimes a heavy library can be swapped for a lighter alternative.
*   **Reduce Concurrency:** If your application spawns many threads or processes, reducing the number of concurrent operations might lower peak memory usage.

### 6. Consider Host Memory & Other Containers

If you've increased container memory, but the problem persists, or if multiple containers are struggling:

*   **Host Resources:** Is the Docker host itself running out of physical RAM? Check the host's memory usage (`free -h`, `htop`). You might need to add more RAM to the host or migrate to a larger instance.
*   **Other Containers:** Are other containers on the same host consuming too much memory, indirectly causing the OOMKilled for your specific container? Enforce memory limits on *all* containers.

## Code Examples

Here are common ways to set memory limits for Docker containers.

### Docker Run Command with Memory Limit

This example runs a simple Nginx container, limiting its memory to 256 megabytes.

```bash
docker run -d \
  --name my-limited-nginx \
  --memory="256m" \
  nginx:latest
```

To include swap space, you can also specify `--memory-swap`. If `--memory-swap` is omitted, it defaults to twice the `--memory` value. Setting `--memory-swap` to the same value as `--memory` effectively disables swap for the container.

```bash
docker run -d \
  --name my-no-swap-nginx \
  --memory="256m" \
  --memory-swap="256m" \
  nginx:latest
```

### Docker Compose with Memory Limits

Using Docker Compose, memory limits are specified under the `deploy.resources.limits` key for a service. This is the recommended approach for defining resource constraints in a production context.

```yaml
# docker-compose.yml
version: '3.8'

services:
  web_app:
    image: my-custom-webapp:latest
    ports:
      - "80:80"
    deploy:
      resources:
        limits:
          memory: 2g # Set hard memory limit to 2 Gigabytes
          # memswap: 4g # Optional: if not set, defaults to 2 * memory (4g here)
          # memswap: 2g # Optional: if set to same as memory, disables swap for this container
    environment:
      # Example: JVM memory settings for a Java application
      - JAVA_OPTS=-Xmx1536m -Xms512m
```

In the Docker Compose example, the `JAVA_OPTS` environment variable sets the JVM's maximum heap size (`-Xmx`) to 1536MB (1.5GB). It's crucial to ensure that the application's internal memory settings (like JVM heap) are less than or equal to the Docker container's memory limit to prevent the JVM from trying to allocate more than the kernel allows.

## Environment-Specific Notes

The impact and debugging process for OOMKilled can vary slightly depending on your environment.

*   **Local Development (Docker Desktop):** Docker Desktop runs a Linux VM on macOS/Windows. The total memory allocated to this VM can be configured in Docker Desktop settings. If your containers hit OOMKilled here, it's either an individual container limit or the Docker Desktop VM itself is running out of memory. I often increase the Docker Desktop VM memory during local development if I'm running several heavy services.
*   **Cloud Providers (AWS ECS, Azure ACI, GCP GKE, etc.):**
    *   **ECS/ACI:** You define task memory limits directly in your task definition. If a container in a task exceeds its limit, the task will be marked as `STOPPED` with a reason like "OOMKilled". Monitoring tools (CloudWatch for AWS, Azure Monitor) will show memory utilization metrics, making it easier to track historical usage leading up to the OOM.
    *   **Kubernetes (GKE, EKS, AKS):** Kubernetes uses `requests` and `limits` for CPU and memory. An OOMKilled event in Kubernetes means a pod's container exceeded its `memory.limits` value. Kubernetes will then restart the pod, often with an `OOMKilled` reason in `kubectl describe pod`. Monitoring tools like Prometheus/Grafana or cloud-specific dashboards are crucial here for setting appropriate limits and identifying trends.
*   **Bare Metal / Virtual Machines:** If you're running Docker directly on a Linux server, the OOM killer might be more aggressive if the entire host is constrained. Ensure that your Docker daemon itself has sufficient resources and that no other host processes are starving Docker containers.

In all cloud environments, it's vital to have robust monitoring and alerting in place. This allows you to identify containers approaching their memory limits *before* they get OOMKilled, giving you time to react.

## Frequently Asked Questions

**Q: How do I know if my application truly needs more memory or if it has a leak?**
**A:** Use `docker stats` and historical monitoring. If memory usage gradually climbs over time without ever plateauing, even under steady load, it suggests a memory leak. If it spikes quickly during specific operations and then drops (but still hits a limit), it might just need more capacity or optimization for those peak loads. Application-level profiling tools are best for identifying leaks.

**Q: What is the difference between `--memory` and `--memory-swap`?**
**A:** `--memory` sets the hard RAM limit for the container. `--memory-swap` sets the total amount of memory (RAM + swap space) the container can use. If `--memory-swap` is set to the same value as `--memory`, the container will not use any swap space. If `--memory-swap` is not specified, it defaults to twice the `--memory` value, allowing the container to use swap up to that point. If neither are specified, the container can use all available host memory and swap.

**Q: My container gets OOMKilled, but `docker stats` says it's not using much memory. What gives?**
**A:** This can be tricky.
    1.  **Bursts:** The OOM event might happen in a very short burst that `docker stats` (which samples periodically) misses.
    2.  **Host OOM:** The entire host might be OOM. Check `dmesg` or system logs (`journalctl -u docker`) for system-wide OOM killer messages.
    3.  **CGroup Accounting:** Sometimes there can be discrepancies in how memory is reported vs. how the kernel's cgroup sees it, especially with shared libraries or file system caches. Ensure your `docker inspect` shows `OOMKilled: true` before looking elsewhere.
    4.  **Language Runtime Overhead:** For Java applications, the JVM itself consumes memory beyond the heap (`-Xmx`). This "off-heap" memory is for things like metadata, threads, and JIT compilation. The container limit must account for both heap and off-heap memory.

**Q: Should I always set memory limits for my Docker containers?**
**A:** Yes, absolutely. It's a best practice to set memory limits (and CPU limits) for all production containers. This prevents a single misbehaving container from monopolizing host resources, impacting other services, and leading to system instability or unpredictable OOMKilled events. It also helps with resource planning and cost management.

**Q: My application is written in Python, and I'm still seeing OOMKilled. Any specific tips?**
**A:** Python applications, especially those using data science libraries like Pandas or NumPy, can be memory-intensive when processing large datasets. Ensure you're not loading entire files into memory if they're huge. Use iterators, generators, or libraries designed for out-of-core processing. Be mindful of object references that might prevent garbage collection.

## Related Errors
- [docker-exit-code-1](/errors/docker-exit-code-1.html)
- [kubernetes-oomkilled](/errors/kubernetes-oomkilled.html)