# Kubernetes pod stuck in Pending state
> Encountering a Kubernetes pod stuck in Pending state means your pod cannot be scheduled onto a node; this guide explains how to fix it.

## What This Error Means

When a Kubernetes pod is in the `Pending` state, it means the Kubernetes scheduler has not yet successfully assigned it to a node. This isn't a runtime error where your application crashed, nor does it indicate a problem with your container image. Instead, it signifies that the pod is waiting for a suitable node to become available and ready to host it. Think of it as a flight waiting for an open gate or enough seats on a plane. The pod is defined, the API server knows about it, but the scheduler, the component responsible for placing pods, hasn't found a home for it yet. In my experience, this state often points to resource constraints or a mismatch between what the pod requires and what the cluster's nodes can provide.

## Why It Happens

The Kubernetes scheduler constantly monitors the API server for new pods that do not have an assigned node. When it finds one, it attempts to assign it to the most suitable node in the cluster. This process involves two main phases:

1.  **Filtering:** The scheduler identifies a subset of nodes that are capable of running the pod. This involves checking factors like:
    *   Node health (is it `Ready`?)
    *   Resource availability (does the node have enough CPU, memory, GPU capacity to satisfy the pod's `requests`?)
    *   Pod affinity/anti-affinity rules
    *   Node selectors and taints/tolerations
    *   Volume availability (if the pod requires specific storage)
2.  **Scoring:** For the nodes that pass the filtering phase, the scheduler assigns a score based on various factors to find the "best" fit. This might include spreading pods across nodes, packing pods onto fewer nodes, or favoring nodes with certain labels.

If, at any point, the filtering phase results in *zero* available nodes, or if no node can meet the pod's requirements, the pod will remain indefinitely in the `Pending` state. I've seen this in production when a sudden spike in deployments outstripped cluster capacity, leaving many new pods stranded.

## Common Causes

Based on countless hours troubleshooting Kubernetes clusters, here are the most frequent reasons a pod gets stuck in `Pending`:

*   **Insufficient Resources:** This is by far the most common culprit. The pod's definition includes `resources.requests` for CPU and/or memory, and no node in the cluster has enough available, unallocated capacity to satisfy these requests. The scheduler won't place a pod if it can't guarantee its requested resources.
*   **Node Taints and Pod Tolerations Mismatch:** Nodes can be "tainted" to repel certain pods unless those pods have a matching "toleration." For example, a node might be tainted with `node-role.kubernetes.io/master:NoSchedule`. If your pod doesn't have a toleration for this taint, it won't be scheduled on a master node.
*   **Node Selectors or Node Affinity Rules:** Pods can specify a `nodeSelector` or more complex `nodeAffinity` rules to restrict them to specific nodes (e.g., `nodeSelector: kubernetes.io/os: linux`). If no node matches these criteria, the pod will remain pending.
*   **PersistentVolumeClaim (PVC) Unbound:** If your pod requires a `PersistentVolumeClaim` (PVC) and that PVC isn't bound to an available `PersistentVolume` (PV), the pod will wait. This often happens if there's no storage class configured, no PVs available, or a dynamic provisioner failed to create one.
*   **Insufficient Cluster Capacity:** Even without explicit resource requests, if all nodes are at or near their maximum pod capacity, new pods may remain pending until existing pods terminate or new nodes are added.
*   **Node Not Ready or Unreachable:** A node might be unhealthy, in a `NotReady` state, or completely offline. The scheduler will not consider such nodes for new pod assignments. Nodes that have been explicitly `cordoned` or `drained` will also prevent new pods from being scheduled.
*   **Pod Anti-Affinity Rules:** A pod might have an anti-affinity rule preventing it from being scheduled on a node where other specific pods (e.g., from the same deployment) are already running. If there are no other suitable nodes, it will wait.
*   **Kube-scheduler Issues:** While less common, a misconfigured or unhealthy `kube-scheduler` component itself can prevent pods from being scheduled. This would typically affect *all* new pods.

## Step-by-Step Fix

When I encounter a pod stuck in `Pending`, I follow a systematic approach. Here’s my go-to troubleshooting guide:

1.  **Inspect Pod Events:** This is your first and most crucial step. The Kubernetes API server records events related to pod lifecycle.
    ```bash
    kubectl describe pod <pod-name> -n <namespace>
    ```
    Look for the `Events` section at the bottom of the output. Often, you'll find messages like `FailedScheduling` followed by a clear explanation: "0/X nodes are available: Insufficient cpu," "node(s) had taints that the pod didn't tolerate," or "node(s) didn't match node selector." These messages are gold.

2.  **Check Node Resources and Status:** If the events point to resource issues, investigate your nodes.
    *   **Node Status:** Ensure all nodes are `Ready`.
        ```bash
        kubectl get nodes
        ```
    *   **Node Capacity and Allocatable:** Describe a node to see its total capacity and `Allocatable` resources (what's available for pods after system daemons).
        ```bash
        kubectl describe node <node-name>
        ```
    *   **Current Usage:** Use `kubectl top nodes` (requires the Metrics Server to be installed in your cluster) to see real-time CPU and memory usage across your nodes. This helps identify genuinely overloaded nodes.
        ```bash
        kubectl top nodes
        ```

3.  **Review Pod Resource Requests and Limits:** If "Insufficient CPU/memory" is the error, check the pod's specification.
    *   Examine the `resources.requests` and `resources.limits` for the containers within the pod.
    *   Are the requests too high? Could they be reduced to fit available node capacity?
    *   Are there other pods on the nodes with very high requests leaving no room?

4.  **Verify Taints and Tolerations:** If events mention "node(s) had taints that the pod didn't tolerate," this is your next focus.
    *   **Node Taints:** Get the taints on your nodes:
        ```bash
        kubectl describe node <node-name> | grep Taints:
        ```
    *   **Pod Tolerations:** Check your pod's `tolerations` field in its YAML definition. Does it have a toleration for the specific taint on the desired node?

5.  **Check Node Selectors and Affinity Rules:** If events suggest "node(s) didn't match node selector," verify these.
    *   **Pod Selectors/Affinity:** Review the pod's `nodeSelector` or `affinity` rules in its YAML.
    *   **Node Labels:** Check the labels on your nodes to ensure they match the pod's requirements:
        ```bash
        kubectl get nodes --show-labels
        kubectl describe node <node-name> | grep Labels:
        ```

6.  **Examine PersistentVolumeClaims (PVCs):** If your pod needs storage, and the issue might be related to it, check the PVC status.
    *   ```bash
        kubectl describe pvc <pvc-name> -n <namespace>
        kubectl get pv
        ```
    *   Ensure the PVC is `Bound` to a PV. If it's `Pending`, the storage provisioning itself is the problem.

7.  **Consider Scaling Up or Downsizing:**
    *   If nodes are genuinely full and your applications require the requested resources, you might need to add more nodes to your cluster.
    *   Alternatively, if certain pods are requesting more resources than they actually need, consider reducing their `requests` to free up capacity.

8.  **Check for Cordoned or Drained Nodes:** Nodes that have been `cordoned` (`SchedulingDisabled`) or `drained` will not accept new pods.
    ```bash
    kubectl get nodes
    ```
    Look for `SchedulingDisabled` in the `STATUS` column. If a node is intentionally cordoned, you'll need to `uncordon` it or scale your deployments to other available nodes.

## Code Examples

Here are some commands and YAML snippets that are essential for diagnosing and resolving `Pending` pods.

**1. Inspecting a specific pod's events:**
```bash
kubectl describe pod my-pending-pod -n my-namespace
```

**2. Viewing node resource usage (requires Metrics Server):**
```bash
kubectl top nodes
```

**3. Describing a node to check capacity, allocatable resources, and taints/labels:**
```bash
kubectl describe node worker-node-1
```

**4. Example Pod YAML with resource requests/limits (a common cause of `Pending`):**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: busybox-resource-heavy
spec:
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c", "echo Hello, Kubernetes! && sleep 3600"]
    resources:
      requests:
        memory: "2Gi" # Pod requests 2 Gigabytes of memory
        cpu: "1"      # Pod requests 1 CPU core
      limits:
        memory: "2.5Gi"
        cpu: "1.5"
```
*Self-correction:* If this pod is pending with "Insufficient memory," you'd need to either reduce the `memory` request or add a node with at least 2Gi free allocatable memory.

**5. Example Pod YAML with a `nodeSelector` and `tolerations`:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-worker-pod
spec:
  containers:
  - name: cuda-container
    image: nvidia/cuda:11.4.0-base-ubuntu20.04
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 1
  nodeSelector:                     # Pod will only run on nodes with this label
    gpu-type: nvidia-tesla-v100
  tolerations:                      # Pod will tolerate this taint
  - key: "dedicated"
    operator: "Equal"
    value: "gpu-node"
    effect: "NoSchedule"
```
*Self-correction:* If this pod is pending, I'd check if any nodes have *both* the `gpu-type: nvidia-tesla-v100` label *and* if they don't, I'd also check if they have the `dedicated=gpu-node:NoSchedule` taint, and if the pod has the `toleration` for it.

## Environment-Specific Notes

The nuances of troubleshooting `Pending` pods can vary slightly depending on your Kubernetes environment.

*   **Cloud Providers (AWS EKS, GCP GKE, Azure AKS):**
    *   **Auto-scaling:** In managed Kubernetes services, clusters often use node auto-scaling groups or node pools. If pods are pending due to resource constraints, verify that your auto-scaler is properly configured, has permission to add nodes, and hasn't hit any cloud provider limits (e.g., maximum instances in a region, subnet IP exhaustion). I've often seen pending pods when an auto-scaling group was configured with too small of a `maxSize`.
    *   **Cloud-specific Taints:** Some cloud providers add taints to specific node types (e.g., spot instances, GPU nodes). Ensure your pods needing these nodes have the appropriate tolerations.
    *   **Networking:** In some cloud CNIs (like AWS VPC CNI), a node might run out of available IP addresses for pods, even if it has CPU/memory. This can lead to pods pending or failing to start.

*   **Docker Desktop / Minikube / Kind (Local Development):**
    *   **Resource Allocation:** These are typically single-node clusters running inside a VM or container on your local machine. The most common cause of `Pending` here is simply that the underlying VM/container hasn't been allocated enough CPU or RAM from your host machine.
    *   **Quick Fix:** Increase the CPU/memory allocated to your Docker Desktop, Minikube, or Kind instance. For Minikube, commands like `minikube config set memory 8192` and `minikube config set cpu 4` followed by `minikube start` are typical.
    *   **Single Node Limitations:** With only one node, resource contention is immediate. If you have multiple demanding pods, they will compete directly.

*   **On-Premise / Bare Metal:**
    *   **Fixed Resources:** Unlike cloud environments, on-premise clusters have physically fixed hardware resources. Scaling means manually adding new physical or virtual machines and joining them to the cluster.
    *   **Network Stability:** Ensure that network connectivity is stable between the control plane and worker nodes. Network issues can make nodes appear `NotReady`, preventing scheduling.
    *   **Storage Provisioning:** If using on-premise storage, ensure your `PersistentVolume` (PV) and `StorageClass` configurations are robust and that your storage solution is healthy and can provision volumes as needed.

## Frequently Asked Questions

**Q: My pod is stuck in Pending, but `kubectl describe pod` shows "0/X nodes are available: Insufficient memory." What should I do?**
A: This means no node has enough free allocatable memory to satisfy your pod's `resources.requests.memory`. You have a few options:
1.  **Reduce Requests:** Edit your pod's YAML to lower the `memory` request (if your application can genuinely run with less).
2.  **Add Nodes:** Scale up your cluster by adding more worker nodes.
3.  **Clean Up:** Identify and terminate unnecessary pods on existing nodes to free up memory.
4.  **Check `kubectl top nodes`:** Verify which nodes are truly memory-constrained to confirm the diagnosis.

**Q: I see "node(s) had taints that the pod didn't tolerate." How do I fix this?**
A: This indicates your pod is trying to schedule on a node with a specific taint, but your pod's definition doesn't include a `toleration` for it.
1.  **Add Toleration:** If your pod *is* intended to run on a tainted node, add the matching `tolerations` entry to your pod's `spec` in its YAML. For example, if the node has `dedicated=gpu:NoSchedule`, you'd add:
    ```yaml
      tolerations:
      - key: "dedicated"
        operator: "Equal"
        value: "gpu-node"
        effect: "NoSchedule"
    ```
2.  **Remove Taint:** If the node taint is unintentional or no longer necessary, remove it from the node using `kubectl taint nodes <node-name> <key>-`.

**Q: What if `kubectl describe pod` doesn't show any events?**
A: This is quite unusual but can happen. If there are truly no events, consider these possibilities:
1.  **API Server/Scheduler Health:** Check the health of your control plane components: `kubectl get componentstatuses`. If the scheduler is unhealthy, it won't process new pods.
2.  **Pod Definition Issues:** While less common for `Pending`, ensure your pod YAML is syntactically valid and doesn't contain any fundamental errors that prevent the API server from fully processing it, although this would typically result in a different status like `CrashLoopBackOff` if it attempted to run.
3.  **Time Lags:** In very large or slow clusters, there might be a slight delay, but events usually appear quickly. If still blank after a minute or two, investigate control plane health.

**Q: Can a `Pending` pod ever eventually get scheduled on its own?**
A: Yes, absolutely. If the underlying cause is transient, the scheduler will continuously attempt to place the pod. For example:
*   If another pod terminates and frees up resources, your pending pod might then be scheduled.
*   If your cluster auto-scales and a new node joins, the scheduler might place the pending pod there.
However, if the cause is a persistent misconfiguration (e.g., incorrect node selector, missing toleration, or chronic resource shortage without auto-scaling), it will remain `Pending` indefinitely until you intervene.

## Related Errors