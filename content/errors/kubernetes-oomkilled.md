# Kubernetes OOMKilled – pod terminated due to memory limit
> Encountering OOMKilled means your container ran out of memory and was terminated; this guide explains how to diagnose and fix it.

## What This Error Means

When you see a pod in your Kubernetes cluster terminated with a `Reason: OOMKilled` or `State: Terminated` and `Exit Code: 137` (or similar, indicating a SIGKILL), it means the container within that pod attempted to use more memory than it was allocated. Kubernetes, specifically the Kubelet agent running on the node, detected this over-consumption and forcibly terminated the container to protect the node and other workloads.

This mechanism is driven by Linux's cgroups (control groups) functionality. When you define `resources.limits.memory` for a container in Kubernetes, the Kubelet configures a cgroup for that container, setting its memory ceiling. If the container's processes exceed this ceiling, the Linux kernel's Out Of Memory (OOM) killer steps in and sends a `SIGKILL` signal to the process, terminating it immediately. From Kubernetes' perspective, the pod has been OOMKilled.

This isn't just about protecting the host system from a runaway process; it's also about enforcing the resource contracts you've defined for your applications. It's a clear signal that your application needs more memory than you've given it, or that there's an underlying issue with its memory management.

## Why It Happens

The `OOMKilled` event typically occurs because a container's actual memory usage surpasses the `memory.limit` specified in its pod definition. Kubernetes offers two key resource parameters for memory:

1.  **`requests.memory`**: This is the amount of memory that Kubernetes *guarantees* for your container. The scheduler uses this value to decide which node to place the pod on, ensuring the node has at least this much memory available.
2.  **`limits.memory`**: This is the maximum amount of memory your container is allowed to consume. If the container tries to allocate memory beyond this limit, it will be OOMKilled.

Here's how it generally plays out:
*   **Scenario 1: `requests` == `limits` (Guaranteed QoS)**: If a container requests 512Mi and has a limit of 512Mi, it gets a "Guaranteed" Quality of Service (QoS) class. While theoretically safer, it can still be OOMKilled if it somehow exceeds this hard limit (e.g., due to kernel overheads or a very aggressive memory allocation pattern right at the edge).
*   **Scenario 2: `requests` < `limits` (Burstable QoS)**: This is common. A container requests 256Mi but has a limit of 512Mi. It's "burstable" because it can use up to 512Mi if available on the node. However, if it pushes past 512Mi, it will be OOMKilled.
*   **Scenario 3: No `requests` or `limits` (BestEffort QoS)**: If neither are set, the container gets a "BestEffort" QoS. It can use as much memory as it wants, provided the node has it. However, in a memory-pressure situation on the node, `BestEffort` pods are the *first* to be considered for eviction by the Kubelet to free up resources. They might also be OOMKilled if they simply try to consume every last byte of memory on the node.

In my experience, the `OOMKilled` error most frequently happens in Scenario 2, where the `limit` was set too low for the application's actual needs, or the application has a memory leak.

## Common Causes

Debugging `OOMKilled` errors often involves looking at both the Kubernetes configuration and the application itself. Here are the most common culprits I've encountered:

*   **Insufficient Memory Limits:** This is the most straightforward cause. The `memory.limit` defined in your pod specification is simply too low for your application's operational needs. Perhaps the application evolved, or a new feature increased its memory footprint, but the limits weren't updated.
*   **Memory Leaks in Application Code:** A bug in the application code causes it to continuously allocate memory without properly releasing it. Over time, the memory usage grows until it hits the Kubernetes limit. I've seen this often with long-running services that process many requests or maintain large caches.
*   **Traffic Spikes or Increased Load:** Your application might run fine under normal load but experiences an `OOMKilled` during peak traffic. Increased requests can mean more concurrent processes, larger in-memory data structures, or more extensive caching, pushing memory usage beyond the limit.
*   **Inefficient Data Structures or Algorithms:** While not strictly a "leak," certain data processing patterns or algorithms can be very memory-intensive. For instance, loading an entire dataset into memory for processing when it could be streamed.
*   **JVM Applications Misconfiguration:** Java applications are notoriously tricky with memory. The JVM's heap size (controlled by flags like `-Xmx`) must be carefully balanced with the container's `memory.limit`. If the JVM heap is set too large relative to the container limit (accounting for off-heap memory, thread stacks, etc.), the container can be OOMKilled even if the heap itself isn't full.
*   **Sidecar Containers:** If your pod includes multiple containers (e.g., an application container and a logging agent sidecar), the total memory used by *all* containers can exhaust the pod's collective limits if not properly managed, or one sidecar might have an issue and consume too much.

## Step-by-Step Fix

Diagnosing and fixing an `OOMKilled` error is a methodical process. Follow these steps:

1.  ### **Identify the OOMKilled Pod and Event**
    First, confirm the pod was indeed OOMKilled.
    ```bash
    kubectl get pods -n <your-namespace>
    ```
    Look for pods in a `CrashLoopBackOff` state or those that have recently restarted. Then, check the events for the specific pod:
    ```bash
    kubectl describe pod <pod-name> -n <your-namespace>
    ```
    In the "Events" section, you're looking for entries like:
    ```
    Events:
      Type     Reason     Age                  From               Message
      ----     ------     ----                 ----               -------
      Warning  OOMKilled  3m5s (x2 over 4m3s)  kubelet, ip-xxxx   Container my-app was OOM-killed.
      Normal   Created    3m5s (x2 over 4m3s)  kubelet, ip-xxxx   Created container my-app
      Normal   Started    3m5s (x2 over 4m3s)  kubelet, ip-xxxx   Started container my-app
    ```
    This clearly indicates an OOMKilled event.

2.  ### **Inspect Previous Container Logs**
    An OOMKilled pod is terminated abruptly by the kernel, so it might not write specific "out of memory" messages just before it dies. However, the logs leading up to the termination can offer clues about increasing memory usage or other problems.
    ```bash
    kubectl logs <pod-name> --previous -n <your-namespace>
    ```
    Look for:
    *   Application-specific memory warnings.
    *   Large object allocations.
    *   Garbage collection events (for JVM applications) that might indicate stress.
    *   Any messages indicating increasing load or resource contention.

3.  ### **Review Pod Resource Definitions**
    Check the memory `requests` and `limits` currently configured for your application's container:
    ```bash
    kubectl get pod <pod-name> -o yaml -n <your-namespace>
    ```
    Navigate to `spec.containers[].resources` and note the `memory` values under `requests` and `limits`.

4.  ### **Monitor Current and Historical Memory Usage**
    This is critical. You need to understand how much memory your application *actually* uses under normal and peak loads.

    *   **Live Monitoring (requires Metrics Server):**
        ```bash
        kubectl top pod <pod-name> -n <your-namespace> --containers
        ```
        This gives you a real-time snapshot. Run this multiple times or monitor over a period to see trends.
    *   **Monitoring Tools (Prometheus, Grafana, Datadog, etc.):** If you have a cluster-wide monitoring solution, check the historical memory usage graphs for the affected pod or deployment. Look for steady growth, sudden spikes, or usage consistently nearing the configured `memory.limit`. In my experience, this historical data is invaluable for understanding the application's true memory profile.

5.  ### **Adjust Memory Limits (Carefully and Iteratively)**
    Based on your monitoring data, you have two primary options:

    *   **Increase `memory.limit`**: If your application's observed memory usage consistently approaches or exceeds the limit, and you've ruled out obvious leaks, increase the `memory.limit` (and usually `memory.request` proportionally). For example, if your app typically uses 400Mi but has a 512Mi limit and gets OOMKilled, try increasing the limit to 768Mi or even 1Gi.
        **Important:** Increase in small, controlled increments (e.g., 25-50% at a time). Deploy the change, monitor, and repeat. Don't just double it blindly, as this can lead to other issues like node starvation or increased costs.

    *   **Optimize Application Memory Usage**: If increasing limits doesn't resolve the issue, or if the memory usage continues to grow indefinitely, you likely have a memory leak or inefficient code. This requires application-level debugging:
        *   **Profiling**: Use tools specific to your programming language (e.g., Java profilers like JVisualVM/JProfiler, Go pprof, Node.js heap snapshots) to identify memory leaks or large object allocations.
        *   **Configuration**: For JVM apps, ensure `max heap size (-Xmx)` is set appropriately, leaving room for off-heap memory, native libraries, and the JVM itself (typically 20-30% less than the container `memory.limit`).

6.  ### **Consider Kubernetes Autoscaling**
    If `OOMKilled` mainly occurs during traffic spikes, consider:
    *   **Horizontal Pod Autoscaler (HPA)**: Scales the number of pod replicas based on CPU or memory utilization. If your memory usage scales with load, HPA can proactively add more pods before existing ones are OOMKilled.
    *   **Vertical Pod Autoscaler (VPA)**: Can provide recommendations for `requests` and `limits` based on observed usage. It can even automatically update these for you, though this needs careful consideration in production.

## Code Examples

Here are common snippets you'll use when dealing with `OOMKilled` issues.

### Defining Memory Limits in a Deployment

This YAML snippet shows how to set `requests` and `limits` for a container. Remember, `memory.limit` is where the OOM killer draws the line.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-web-app
  labels:
    app: my-web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-web-app
  template:
    metadata:
      labels:
        app: my-web-app
    spec:
      containers:
      - name: app-container
        image: my-registry/my-web-app:1.2.0
        resources:
          requests:
            memory: "256Mi" # Guaranteed memory for scheduling
            cpu: "220m"
          limits:
            memory: "512Mi" # Max memory allowed before OOMKilled
            cpu: "500m"
        ports:
        - containerPort: 8080
```

### Checking Pod Events for OOMKilled

```bash
# Get all events in a namespace, filtered by reason=OOMKilled
kubectl get events -n production --field-selector reason=OOMKilled

# Describe a specific pod to see its full event history
kubectl describe pod my-web-app-76c7648f8c-j9smz -n production
```

### Viewing Previous Logs from an OOMKilled Pod

```bash
# Retrieve logs from the container that was OOMKilled (assuming it restarted)
kubectl logs my-web-app-76c7648f8c-j9smz --previous -n production
```

### Monitoring Live Memory Usage (requires Metrics Server)

```bash
# See current memory usage for a specific pod
kubectl top pod my-web-app-76c7648f8c-j9smz -n production

# See current memory usage for all pods in a namespace
kubectl top pod -n production
```

## Environment-Specific Notes

The impact and debugging approach for `OOMKilled` can vary slightly based on your Kubernetes environment.

*   **Cloud Providers (EKS, GKE, AKS):** In large cloud clusters, a single OOMKilled pod is often a pod-specific issue. However, if you see many pods being OOMKilled across different applications, it might indicate broader node resource starvation. You might need to provision larger nodes, implement cluster autoscaling, or review your overall resource allocation strategy. Over-provisioning nodes can mask memory issues for a while but is costly. I've seen teams throw larger nodes at the problem only to discover the root application memory leak much later when costs became too high.
*   **Docker Desktop / Minikube (Local Development):** These local environments typically run Kubernetes within a VM on your laptop, with limited allocated resources. It's very common to hit OOMKilled errors if you haven't explicitly increased the memory allocated to Docker Desktop or Minikube. By default, they often start with 2GB-4GB, which can be quickly exhausted by even a few development-grade services. Always check and adjust the memory settings in Docker Desktop preferences or your Minikube start command (`minikube start --memory=Xg`).
*   **On-Premise / Bare Metal:** Without the elasticity of cloud, careful capacity planning and monitoring are even more critical. If nodes consistently run low on memory, you might need to add physical RAM to hosts or add more nodes to the cluster. The principles of setting requests/limits and monitoring remain the same, but the scaling options are different.

## Frequently Asked Questions

**Q: What's the difference between `memory.requests` and `memory.limits`?**
A: `memory.requests` are used by the Kubernetes scheduler to decide which node a pod can run on, guaranteeing that amount of memory will be available. `memory.limits` define the absolute maximum memory a container can consume; if it exceeds this, the kernel's OOM killer terminates the container.

**Q: Will increasing `memory.limit` always solve an `OOMKilled` issue?**
A: No. While it can resolve issues where the limit was simply set too low, it won't fix a fundamental memory leak in your application. If there's a leak, increasing the limit only delays the inevitable `OOMKilled` until the application consumes the new, higher limit. It's crucial to find the root cause.

**Q: How can I determine the optimal memory limits for my application?**
A: The best approach is empirical:
1.  Start with a reasonable `memory.request` and `memory.limit` based on local testing or similar applications.
2.  Deploy the application.
3.  Monitor its memory usage under typical and peak loads using `kubectl top` and your cluster's monitoring tools.
4.  Set the `memory.request` to slightly above the average observed usage and the `memory.limit` to 20-30% higher than the peak observed usage to allow for bursts.
5.  Iterate and adjust as your application evolves.

**Q: Can a node OOMKill a pod even if the pod is within its configured limits?**
A: This is less common but possible in extreme situations, particularly if the node itself is under severe memory pressure, and its own system processes or other components are struggling. In such cases, the `kubelet` might initiate evictions to reclaim node resources, prioritizing `BestEffort` pods first, then `Burstable` pods that are exceeding their requests. However, a container being directly `OOMKilled` by the Linux kernel is almost always due to it exceeding its *own* `memory.limit`.

## Related Errors

- [kubernetes-crashloopbackoff](/errors/kubernetes-crashloopbackoff.html)
- [docker-oomkilled](/errors/docker-oomkilled.html)