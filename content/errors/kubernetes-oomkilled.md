# Kubernetes OOMKilled – pod terminated due to memory limit
> Encountering OOMKilled means your container exceeded its memory limit; this guide explains how to diagnose and fix it.

## What This Error Means

When a Kubernetes pod is `OOMKilled` (Out Of Memory Killed), it signifies that one of its containers has consumed more memory than was allocated to it via its resource `limits` definition. The Linux kernel's Out-Of-Memory (OOM) killer, under the direction of the Kubernetes kubelet, forcefully terminates the process(es) within that container. This is not a graceful shutdown; it's an abrupt termination designed to protect the overall stability of the node and other workloads running on it.

You'll typically see this manifesting as a pod that enters a `CrashLoopBackOff` state, repeatedly starting and then getting terminated shortly after. Checking the pod's status with `kubectl describe pod <pod-name>` will often reveal an `OOMKilled` reason in the `Last State` of the container, along with an exit code of `137` (which often indicates a SIGKILL signal).

## Why It Happens

Kubernetes uses Linux cgroups (control groups) to manage and isolate resources for containers. When you define `resources.limits.memory` in your pod specification, you're instructing Kubernetes (and the underlying cgroups mechanism) to cap the memory available to that container.

Here's a breakdown of the mechanics:

1.  **Memory Limits:** You specify a hard upper bound on memory usage. For example, `limits.memory: "512Mi"`.
2.  **Memory Requests:** You can also specify `requests.memory`. This value is used by the Kubernetes scheduler to decide which node to place the pod on, ensuring the node has at least that much memory available. If no `limits.memory` is specified, the limit defaults to the node's total memory, which is usually undesirable.
3.  **Kernel Intervention:** The kubelet constantly monitors container resource usage. If a container attempts to allocate memory beyond its `limits`, the Linux kernel's OOM killer is invoked.
4.  **Termination:** The OOM killer selects and terminates a process (or processes) within the over-consuming container to reclaim memory, leading to the `OOMKilled` status. This aggressive approach prevents a single misbehaving container from destabilizing the entire node.

In my experience, many engineers initially confuse `requests` with `limits`. Remember, `requests` are for scheduling, `limits` are for runtime enforcement. If your `requests` are too low, your pod might get scheduled on a node with insufficient *actual* free memory, but the `OOMKilled` event itself is triggered by hitting the `limits`.

## Common Causes

Identifying the root cause of an `OOMKilled` event often involves looking at your application's behavior and your Kubernetes configuration.

*   **Underestimated Application Memory Usage:** This is the most frequent culprit. The application simply needs more memory than you've given it. This could be due to:
    *   **Increased Data Volume:** Processing larger datasets or handling more concurrent requests than anticipated.
    *   **Complex Operations:** Workloads like image processing, large-scale data analytics, or complex queries can temporarily spike memory consumption.
    *   **Startup Peaks:** Some applications consume significantly more memory during startup (e.g., loading caches, initializing large data structures) than during steady-state operation.
*   **Memory Leaks:** The application code itself might have a bug where it continuously allocates memory without properly releasing it. Over time, the memory footprint grows until it hits the limit. I've seen this in production when long-running services gradually consume more RAM.
*   **Incorrect `resources.limits.memory` Configuration:**
    *   **Too Low:** The configured limit is simply too restrictive for the application's normal operation.
    *   **Missing:** If no memory limit is set, the container can theoretically consume all available memory on the node, potentially leading to the node's OOM killer being invoked, which could affect multiple pods. While the container itself won't show `OOMKilled` in its status, it's still a dangerous scenario.
*   **Sidecar Containers:** If you have sidecar containers in your pod (e.g., logging agents, service meshes), their memory usage can add to the overall pod footprint. It's easy to overlook their resource requirements.
*   **External Factors:** While less common directly causing `OOMKilled`, sometimes issues like heavy network traffic or resource contention on the node can indirectly exacerbate memory pressure within a container, pushing it over its limit.

## Step-by-Step Fix

Addressing an `OOMKilled` error requires a systematic approach of diagnosis, monitoring, and iterative adjustment.

1.  **Diagnose the Specific Event:**
    Start by understanding *when* and *why* the termination happened.
    ```bash
    # Check pod status and events for OOMKilled reason
    kubectl describe pod <pod-name> -n <namespace>
    ```
    Look for sections like `Last State`, `Reason: OOMKilled`, and `Exit Code: 137`. Also, check the `Events` section for related messages.

    ```bash
    # View logs from the previous, terminated container
    kubectl logs --previous <pod-name> -n <namespace>
    ```
    The logs *just before* termination can often provide clues about what the application was doing at the time of the memory spike. Sometimes, the application itself logs an "out of memory" error before Kubernetes kills it.

2.  **Monitor Actual Memory Usage:**
    You need to understand how much memory your application *actually* uses over time, including peaks.

    ```bash
    # (Requires Metrics Server installed in your cluster)
    # Get current memory usage for your pod
    kubectl top pod <pod-name> -n <namespace>
    ```
    This gives you a snapshot. For a historical view, use your cluster's monitoring solution (e.g., Prometheus/Grafana, Datadog, cloud provider monitoring tools like Google Cloud Monitoring or AWS CloudWatch). Look at memory usage graphs for the affected pod over several days, paying attention to average usage, percentile usage (e.g., 90th or 99th percentile), and any sudden spikes corresponding to OOMKilled events.

3.  **Adjust Memory Limits (Iteratively):**
    Once you have a better idea of your application's actual memory footprint, you can adjust the limits.

    *   **Increase `limits.memory`:** Increment your pod's `resources.limits.memory` in your Deployment, StatefulSet, or Pod manifest.
        *   **How much?** A common strategy is to take the 90th or 95th percentile of observed memory usage and add a buffer (e.g., 10-20%). Avoid setting the limit to just the peak usage, as that leaves no headroom.
        *   **Monitor after change:** Deploy the change and meticulously monitor the pod again. Don't assume the problem is solved; look for stability and ensure you haven't just moved the OOM point slightly higher.
    *   **Consider `requests.memory`:** Ensure `requests.memory` is set to a value close to your application's baseline memory usage. If `requests` are too low, your pod might get scheduled on a node that doesn't have enough *guaranteed* memory, leading to other issues, though not directly `OOMKilled`. Setting `requests` and `limits` to the same value creates a "Guaranteed" QoS class pod, which can be beneficial for critical workloads.

4.  **Optimize Application Code and Configuration:**
    If simply increasing limits isn't sustainable or reveals a deeper issue, you might need to look inside the container.
    *   **Profile for Memory Leaks:** Use language-specific profiling tools (e.g., Java Flight Recorder, Go pprof, Python memory profilers) to identify memory leaks or inefficient memory usage patterns in your application.
    *   **Application-Specific Settings:** Adjust internal memory settings. For JVM-based applications, this might mean tuning `Xmx` and `Xms` heap settings. For databases, review cache sizes.
    *   **Reduce Concurrency:** If your application processes multiple items concurrently, reducing the concurrency level might lower peak memory usage.

5.  **Scale Horizontally (If Applicable):**
    If the issue is due to increased load, and your application is stateless, consider scaling out by increasing the number of replicas (`replicas`) in your Deployment. This distributes the load across more pods, potentially reducing the memory pressure on individual instances.

## Code Examples

Here's a concise example of a Kubernetes Deployment manifest snippet demonstrating how to set memory `requests` and `limits`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-webapp
  labels:
    app: my-webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-webapp
  template:
    metadata:
      labels:
        app: my-webapp
    spec:
      containers:
      - name: webapp-container
        image: my-registry/my-webapp:v1.2.3
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi" # This is the critical setting for OOMKilled
            cpu: "500m"
```
In this example, the `webapp-container` is guaranteed 256 MiB of memory by the scheduler and will be terminated by the kernel's OOM killer if its memory usage exceeds 512 MiB.

To check the previous logs of an OOMKilled pod, which can be invaluable for debugging:
```bash
# Replace 'my-webapp-abcde-12345' with your actual pod name
kubectl logs --previous my-webapp-abcde-12345 -n default
```

## Environment-Specific Notes

The general principles of diagnosing and fixing OOMKilled remain consistent across environments, but certain aspects differ.

*   **Cloud Kubernetes (GKE, EKS, AKS):**
    *   **Monitoring:** Cloud providers offer integrated monitoring solutions (e.g., Google Cloud Monitoring, AWS CloudWatch Container Insights) that can provide detailed metrics on pod and container memory usage over time. These are often more robust than basic `kubectl top` commands.
    *   **Node Sizing:** While `OOMKilled` is about *container* limits, sometimes consistently needing much larger limits for many pods can indicate that your underlying *nodes* are undersized. Cloud environments make it easy to scale node sizes or implement cluster autoscaling. Be aware that larger nodes mean higher costs.
    *   **Cost Management:** Be mindful that increasing memory limits significantly can lead to higher cloud bills if it causes pods to be scheduled on more expensive node types or prevents efficient packing of pods.

*   **Docker Desktop / Minikube (Local Development):**
    *   **Host Limits:** Your local Kubernetes environment (Docker Desktop, Minikube, kind) runs within a VM or directly on your machine with a fixed amount of allocated resources. If you're experiencing `OOMKilled` locally, ensure your Docker Desktop or Minikube VM is configured with enough RAM to comfortably run your test workloads. Increasing container limits might hit the *host VM's* limits, causing other issues.
    *   **Resource Contention:** Local development machines often run many other applications. This can lead to resource contention with your local Kubernetes cluster, making OOMKilled events harder to debug as the problem might not be with your application but with the overall system's resource availability.
    *   **Simplicity:** Local debugging is often simpler. You can quickly iterate on code changes and test new resource limits without full deployment cycles.

## Frequently Asked Questions

**Q: What's the difference between OOMKilled and CrashLoopBackOff?**
A: `OOMKilled` is a *reason* for a container terminating. `CrashLoopBackOff` is a *state* that a pod enters when one of its containers repeatedly crashes and restarts. An `OOMKilled` event is a very common reason a pod ends up in `CrashLoopBackOff`.

**Q: Should `requests.memory` and `limits.memory` always be the same?**
A: Not necessarily. Setting them equal gives your pod a "Guaranteed" QoS class, meaning it receives dedicated resources and is less likely to be evicted under node memory pressure. However, it can lead to underutilization if your application's average memory usage is much lower than its peak. A common practice is to set `requests.memory` to your application's average or baseline usage and `limits.memory` to its typical peak usage plus some buffer.

**Q: How do I find the actual memory usage of my application inside the container?**
A: `kubectl top pod <pod-name>` (if Metrics Server is installed) provides a high-level view. For more detailed insights, you might need to exec into the container (`kubectl exec -it <pod-name> -- bash`) and use Linux tools like `ps aux` or `top`, or application-specific profiling tools for a deeper dive into process memory.

**Q: Can CPU limits cause OOMKilled?**
A: Indirectly, yes. If your application is CPU-bound and constantly throttled by CPU limits, it might take longer to process tasks, potentially leading to a backlog of data in memory that eventually exceeds its memory limit. However, a direct `OOMKilled` is always a memory-related issue.

**Q: What if increasing memory limits doesn't help or leads to unsustainably large limits?**
A: This strongly suggests a memory leak or inefficient resource usage within your application. You need to focus on profiling and optimizing your application code. Continuously increasing limits without addressing the underlying issue is a temporary fix that will eventually hit a ceiling or become cost-prohibitive.

## Related Errors