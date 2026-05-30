# Kubernetes OOMKilled – pod terminated due to memory limit
> Encountering a Kubernetes OOMKilled error means your pod was terminated for exceeding its memory limit; this guide explains how to diagnose and effectively fix it.

## What This Error Means

When you see a pod in your Kubernetes cluster terminated with an `OOMKilled` status, it stands for "Out Of Memory Killed." This is Kubernetes's way of telling you that one of your containers within that pod tried to consume more memory than it was allocated via its configured `limits.memory` resource setting. The kernel's OOM killer, managed by cgroups, intervenes to prevent the container from starving the entire node of memory, forcibly terminating the process.

This event typically manifests with a `Reason: OOMKilled` in the pod's status and an exit code of `137`. An exit code of `128 + N` usually indicates that a process was terminated by signal `N`. In this case, `128 + 9 = 137`, where signal `9` is `SIGKILL`, a non-catchable signal that immediately terminates a process. It's a clear indicator that the operating system forcibly killed the container process because it ran out of memory.

## Why It Happens

At its core, `OOMKilled` happens because of a mismatch: your application needs more memory than Kubernetes (or rather, the underlying Linux kernel's cgroups) has allowed it. When you define a container in Kubernetes, you can specify `resources.limits.memory` and `resources.requests.memory`.

*   **`requests.memory`**: This is the minimum amount of memory guaranteed to the container. The scheduler uses this value to decide which node a pod can run on, ensuring the node has enough free memory to satisfy all requested resources.
*   **`limits.memory`**: This is the maximum amount of memory the container is allowed to use. If a container attempts to exceed this limit, the Linux kernel's OOM killer will step in and terminate the process.

If no `limits.memory` is set, the container can theoretically use all available memory on the node. However, this is generally a bad practice as a runaway process could destabilize the entire node, leading to multiple pod failures. Most clusters enforce default limits if none are explicitly set.

The `OOMKilled` event isn't necessarily a bug in Kubernetes; it's the system working as designed to enforce resource isolation and prevent a single rogue application from impacting the stability of the entire node and other pods running on it.

## Common Causes

In my experience, `OOMKilled` errors usually boil down to one of a few recurring issues:

1.  **Underestimated Memory Requirements**: This is perhaps the most common cause. The application simply needs more memory to perform its tasks than you've provisioned. This can happen during peak loads, processing large datasets, or when an application's memory footprint grows over time.
2.  **Memory Leaks in Application Code**: A classic software bug where the application continuously allocates memory but fails to release it, leading to a steady increase in memory usage until it hits the limit. I've seen this in long-running services written in various languages, from C++ to Node.js.
3.  **Inefficient Application Code/Libraries**: Sometimes the code isn't leaking, but it's just inefficient. Loading entire large files into memory when only a small part is needed, or using libraries that are memory-intensive, can quickly consume allocated resources. For example, some data processing libraries might copy entire datasets rather than stream them.
4.  **Java Virtual Machine (JVM) Specifics**: Java applications are notorious for memory management complexity. The JVM's heap and off-heap memory usage (e.g., direct byte buffers, thread stacks, JNI code) can be tricky to size. Setting `Xmx` too high can lead to the JVM allocating more memory than the container limit allows, or conversely, if `Xmx` is too low, the application struggles, but the JVM itself, outside the heap, can still exceed the limit. I've personally spent countless hours tuning JVM memory settings (`-Xmx`, `MaxDirectMemorySize`, `MetaspaceSize`) in conjunction with container memory limits.
5.  **Bursty Workloads**: Applications that typically run with low memory but occasionally experience sudden, short-lived spikes in memory usage (e.g., batch processing, report generation, complex query execution) can easily exceed their limits during these bursts.
6.  **Sidecars and Init Containers**: Don't forget any sidecar containers or init containers within your pod. Their memory usage also contributes to the pod's overall resource consumption and can trigger `OOMKilled` if not properly accounted for.

## Step-by-Step Fix

Addressing an `OOMKilled` error requires a systematic approach.

### 1. Identify the Affected Pod and Container

First, pinpoint which pod and specifically which container within that pod is being killed.

```bash
kubectl get pods --all-namespaces -o wide | grep OOMKilled
```

Once you have the pod name and namespace, describe it to get more details:

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Look for the "Events" section at the bottom for `OOMKilled` messages. Also, check the `State` and `Last State` of each container within the pod specification. You'll typically see `Reason: OOMKilled` and `Exit Code: 137`.

### 2. Review Container Logs

Access the logs of the terminated container. Sometimes, the application itself might log an out-of-memory error before Kubernetes steps in, providing clues about what triggered the spike.

```bash
kubectl logs <pod-name> -n <namespace> -c <container-name> --previous
```

The `--previous` flag is crucial as the new pod instance won't have the logs of the terminated one.

### 3. Analyze Current and Historical Memory Usage

This is where you determine if the application truly needs more memory or if there's a leak.

*   **Current Usage (if the pod is restarting):**
    ```bash
    kubectl top pod <pod-name> -n <namespace> --containers
    ```
    This gives you a quick snapshot of live memory usage if the pod manages to run for a bit before being killed again.
*   **Historical Usage (preferred):** Use your cluster's monitoring solution (e.g., Prometheus with Grafana, Datadog, New Relic). Look at the memory usage metrics for the specific container over time, especially leading up to the `OOMKilled` events. Pay attention to trends: is memory steadily climbing (leak), or does it spike suddenly (bursty workload)? Compare the actual usage against the `limits.memory` you've set. In my experience, this historical data is invaluable.

### 4. Adjust Memory Limits (Iterative Approach)

Based on your analysis:

*   **If the application consistently uses memory close to its limit and then gets killed:** This suggests your `limits.memory` is too low. Gradually increase it. A common strategy is to set `requests.memory` to what you *expect* the application to use under normal load and `limits.memory` to 1.2x to 1.5x that value to accommodate minor spikes, provided your nodes have sufficient allocatable memory.
*   **If memory usage grows steadily over time without dropping:** This indicates a potential memory leak. Increasing limits will only delay the problem; you need to investigate the application code.

Modify your Deployment or StatefulSet YAML:

```yaml
# Example snippet from a Deployment/StatefulSet
containers:
- name: my-app
  image: my-repo/my-app:1.0.0
  resources:
    requests:
      memory: "256Mi" # Guaranteed minimum
    limits:
      memory: "512Mi" # Hard limit, OOMKilled if exceeded
```

Apply the changes: `kubectl apply -f your-deployment.yaml`.
Monitor the pod closely after increasing limits. If `OOMKilled` persists, increase again or dive deeper into code.

### 5. Investigate Application Code for Memory Leaks

If historical monitoring points to a memory leak:

*   **Profile your application:** Use language-specific profiling tools (e.g., Java Flight Recorder for JVM, `pprof` for Go, `node --inspect` for Node.js, `valgrind` for C/C++).
*   **Analyze heap dumps:** For JVM apps, trigger a heap dump when memory usage is high and analyze it to find objects that are not being garbage collected.
*   **Review recent code changes:** Did memory usage change after a particular commit?

This step is often the most time-consuming but leads to the most robust solution.

### 6. Consider Horizontal Pod Autoscaling (HPA)

If your application's memory usage is highly variable and correlates with load, and the application is designed to scale horizontally (i.e., more instances handle more load), HPA can be a good solution. HPA can scale the number of pod replicas based on CPU or memory utilization.

You'd typically configure HPA to scale based on average memory *utilization* relative to your `requests.memory`.

### 7. Node Resources and Taints/Tolerations

Finally, ensure your nodes have sufficient aggregate memory to handle the increased requests and limits. If you're consistently running nodes near capacity, increasing limits for one pod might just shift the OOMKilled problem to another, or even cause node-level issues. You might need to add more nodes or use nodes with larger memory capacities. Sometimes, adding a node taint and toleration for resource-hungry applications can ensure they land on dedicated, well-provisioned nodes.

## Code Examples

Here are some concise, copy-paste ready examples for typical troubleshooting and resolution steps.

### Examining Pod Events and Resource Limits

To see details about a specific pod, including its resource requests and limits, and termination events:

```bash
kubectl describe pod my-oomkilled-app-xxxx -n production
```

Output relevant section for `OOMKilled` might look like:

```
...
Containers:
  my-app:
    Container ID:   containerd://...
    Image:          my-repo/my-app:1.0.0
    Image ID:       docker.io/...
    Port:           8080/TCP
    Host Port:      0/TCP
    Limits:
      memory:  512Mi   # This is the limit that was exceeded
    Requests:
      memory:  256Mi
    State:          Terminated
      Reason:       OOMKilled  # The key indicator
      Exit Code:    137        # Signal 9 (SIGKILL)
      Started:      Mon, 29 Feb 2024 10:00:00 -0500
      Finished:     Mon, 29 Feb 2024 10:05:30 -0500
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
      Started:      Mon, 29 Feb 2024 09:50:00 -0500
      Finished:     Mon, 29 Feb 2024 09:55:30 -0500
...
Events:
  Type     Reason     Age                 From               Message
  ----     ------     ----                ----               -------
  Normal   Pulled     2m4s (x3 over 10m)  kubelet            Container image "my-repo/my-app:1.0.0" already present on machine
  Normal   Created    2m4s (x3 over 10m)  kubelet            Created container my-app
  Normal   Started    2m4s (x3 over 10m)  kubelet            Started container my-app
  Warning  OOMKilled  2m4s (x2 over 7m)   kubelet            Container my-app was OOM-killed.
```

### Modifying Memory Resources in a Deployment

To increase the memory limit for a container, edit your Deployment (or StatefulSet, DaemonSet) YAML:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: my-repo/my-app:1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"  # Increased request
          limits:
            cpu: "500m"
            memory: "1Gi"   # Increased limit to 1 Gigabyte
```

Apply the change:

```bash
kubectl apply -f deployment.yaml -n production
```

### Configuring Horizontal Pod Autoscaler (HPA)

To automatically scale your pods based on memory utilization. This example scales between 2 and 10 replicas, targeting an average memory utilization of 80% of the requested memory.

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app-deployment # Must match the deployment name
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80 # Target 80% of `requests.memory`
```

Apply the HPA:

```bash
kubectl apply -f hpa.yaml -n production
```

## Environment-Specific Notes

While the core `OOMKilled` issue is consistent across Kubernetes environments, certain aspects might differ based on where your cluster is running.

### Cloud Environments (AWS EKS, GCP GKE, Azure AKS)

*   **Node Sizing:** Cloud providers offer various instance types. If you're frequently hitting OOMKilled errors across many pods, it might be a sign that your worker nodes are undersized. Consider scaling up to instance types with more memory or adding more nodes.
*   **Managed Services:** If you're running managed databases, message queues, or other stateful services, remember that they consume memory *outside* your Kubernetes cluster. Don't confuse application memory issues with underlying infrastructure limitations.
*   **Cost Implications:** Increasing memory limits directly translates to higher resource requests, which can lead to Kubernetes scheduling pods on more expensive nodes or requiring more nodes overall. Always balance performance with cost.
*   **Autoscaling:** Cloud providers integrate well with cluster autoscalers (e.g., Karpenter, Cluster Autoscaler). Ensure your autoscaler is configured to provision nodes with adequate memory when your cluster needs to grow due to increased resource requests.

### Docker (without Kubernetes)

*   **`docker run -m`:** If you're running containers directly with Docker, the `-m` or `--memory` flag on `docker run` sets the memory limit. This functions similarly to Kubernetes's `limits.memory`. An OOMKilled here means the container exceeded this direct Docker limit.
    ```bash
    docker run -it --memory="512m" my-image
    ```
*   **Docker Compose:** In `docker-compose.yml`, you define limits under the `resources` key for each service.
    ```yaml
    # docker-compose.yml
    services:
      my-app:
        image: my-image
        deploy:
          resources:
            limits:
              memory: 512M
            reservations:
              memory: 256M
    ```
The underlying mechanism (cgroups) is the same, so the troubleshooting principles remain identical: identify usage, review code, increase limits.

### Local Development (Minikube, Kind, Docker Desktop)

*   **Host Resource Contention:** When running Kubernetes locally (e.g., Minikube, Kind, or Docker Desktop's Kubernetes), your cluster shares resources with your host machine. If your laptop only has 16GB of RAM and you're running a few resource-hungry pods, they can quickly deplete the memory available to the local Kubernetes VM, leading to OOMKilled pods or even host instability.
*   **Minikube/Kind VM Limits:** Tools like Minikube allow you to configure the amount of memory allocated to the Kubernetes VM (`minikube start --memory=8192`). If your pods are OOMKilled on a local cluster but not in production, check if your local cluster VM has enough memory. I've often seen developers struggle with this because their local setup is resource-constrained compared to a dedicated cloud environment.
*   **Simplified Monitoring:** You might not have a full Prometheus/Grafana stack on your local dev environment. Rely more on `kubectl top` and `kubectl describe` for quick checks, but remember they offer less historical context.

## Frequently Asked Questions

**Q: What is exit code 137?**
A: Exit code 137 specifically means the process was terminated by signal 9 (SIGKILL). In the context of Kubernetes, this is almost always due to the container exceeding its memory limit and being killed by the kernel's OOM killer.

**Q: Should `requests.memory` and `limits.memory` be the same?**
A: Not necessarily. Setting them equally ensures a fixed memory allocation and deterministic behavior, but it can lead to underutilization if your application has bursty memory needs. A common practice is to set `requests.memory` to the average expected usage and `limits.memory` slightly higher (e.g., 1.2x - 1.5x the request) to allow for temporary spikes without being killed, while still preventing runaway processes. If they are the same, the Quality of Service (QoS) class will be "Guaranteed." If limits are higher than requests, it's "Burstable."

**Q: How do I monitor memory usage effectively in Kubernetes?**
A: The most effective way is to use a cluster-wide monitoring solution like Prometheus and Grafana. Prometheus collects metrics from cAdvisor (which runs on every node) and your applications, while Grafana provides dashboards to visualize historical memory usage, compare it against limits, and identify trends or spikes leading to OOMKilled events.

**Q: Can a pod get OOMKilled even if the node has plenty of free memory?**
A: Yes, absolutely. The `OOMKilled` event is about the container exceeding *its own specific memory limit*, not necessarily the entire node running out of memory. If a pod has a `limits.memory` of 512Mi, and it tries to use 513Mi, it will be killed even if the node has 30GB of free RAM. The limit acts as a hard boundary for that individual container.

**Q: What if I suspect a memory leak in my application, but I'm not a developer?**
A: As an engineer, your role is to provide the developers with clear evidence. Use your monitoring tools to show them charts of memory usage climbing over time until the OOMKilled event. Provide `kubectl describe` output and logs (especially `--previous` logs) that pinpoint the termination. This data is critical for them to diagnose and fix the underlying code issue.

## Related Errors