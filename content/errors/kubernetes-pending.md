# Kubernetes pod stuck in Pending state
> Encountering a Kubernetes pod stuck in Pending state means it cannot be scheduled onto a node due to resource constraints or other underlying node issues; this guide explains how to fix it.

## What This Error Means

When a Kubernetes pod enters the `Pending` state, it signifies that the Kubernetes scheduler has not yet found a suitable node within the cluster to run the pod. This isn't an error in the traditional sense, but rather an indication that the cluster cannot currently satisfy all of the pod's scheduling requirements. The pod isn't crashing, nor are its containers failing to start; it's simply waiting to be placed.

Unlike states like `CrashLoopBackOff` or `Error`, which suggest issues with the application code or container runtime, `Pending` points to an infrastructure-level challenge. The scheduler continuously attempts to find a node that meets criteria such as requested CPU and memory, node selectors, taints/tolerations, and available ports. Until such a node is identified and confirmed, the pod will remain in `Pending`.

In my experience, `Pending` pods are often a wake-up call that your cluster resources are either insufficient or improperly configured for the workload you're trying to deploy. It's a proactive measure by Kubernetes to prevent oversubscription or deployment onto incompatible nodes, which could lead to instability.

## Why It Happens

The core reason a pod gets stuck in `Pending` is that the Kubernetes scheduler, `kube-scheduler`, cannot place it on any available node. The scheduler operates based on a series of predicates (filters) and priorities (rankings).

1.  **Predicates:** These are "hard" requirements. If a node fails any predicate, it's immediately excluded. Examples include:
    *   `PodFitsResources`: Does the node have enough free CPU and memory (allocatable) to satisfy the pod's requests?
    *   `HostPortPredicate`: Is the requested host port already in use on the node?
    *   `MatchNodeSelector`: Does the node have all the labels specified by the pod's `nodeSelector`?
    *   `TaintTolerationPredicate`: Does the pod tolerate all taints present on the node?
    *   `PodFitsHost`: Does the pod explicitly request a specific host that is not available or ready?
    *   `VolumeZonePredicate`: For persistent volumes, is the node in the correct availability zone/region?

2.  **Priorities:** After filtering, the remaining nodes are ranked based on "soft" requirements, such as spreading pods across nodes, favoring nodes with fewer pods, or nodes with specific resource types. While priorities influence *which* node a pod lands on, they don't prevent scheduling entirely.

If no node passes *all* of the necessary predicates, the scheduler cannot make a decision, and the pod remains in `Pending` indefinitely. This usually means a fundamental mismatch between what your pod needs and what your cluster can provide. I've seen this happen frequently in production environments where resource quotas are tightly managed or when a sudden spike in deployments exhausts available capacity.

## Common Causes

Identifying the exact reason for a `Pending` pod requires careful investigation. Based on what I've encountered, these are the most common culprits:

*   **Insufficient Node Resources (CPU/Memory):** This is by far the most frequent cause. Your pod requests more CPU or memory than any node currently has available (after accounting for already running pods and system overhead). Even if a node shows "free" memory, it might not be enough to satisfy the pod's request, especially for `requests` values which are reserved.
*   **Node Selector Mismatch:** The pod's definition includes a `nodeSelector` or `nodeAffinity` rule that specifies a label (e.g., `disktype: ssd`, `gpu: true`) that no node in the cluster possesses, or all matching nodes are already at full capacity.
*   **Taints and Tolerations:** A node might have a `taint` (e.g., `node-role.kubernetes.io/master:NoSchedule`) that prevents pods from being scheduled on it unless the pod explicitly defines a `toleration` for that specific taint.
*   **Unbound Persistent Volume Claims (PVCs):** If your pod requires a `PersistentVolumeClaim` (PVC), and that PVC remains in a `Pending` state (meaning it hasn't successfully bound to a `PersistentVolume`), the pod waiting for it will also remain `Pending`. This often indicates issues with your storage provisioner, StorageClass, or available PVs.
*   **Node Not Ready/Unreachable:** The scheduler will only consider nodes that are in a `Ready` state. If all nodes are `NotReady` or if there are networking issues preventing the `kube-scheduler` from communicating with nodes, pods will remain `Pending`.
*   **HostPort Conflict:** If a pod requests a specific `hostPort` and that port is already in use on all suitable nodes, the pod will remain `Pending`.
*   **Pod Anti-affinity Conflicts:** If a pod has a `podAntiAffinity` rule that prevents it from being scheduled on the same node as another specific pod, and all available nodes already host one of the forbidden pods, it will not be scheduled.

## Step-by-Step Fix

Troubleshooting a `Pending` pod is typically a methodical process of elimination. Here’s how I usually approach it:

### 1. Identify the Problematic Pod

First, you need to know which pod is stuck.

```bash
kubectl get pods --all-namespaces -o wide
```

Look for any pods in the `Pending` state. Note down the pod's name and its namespace.

### 2. Get Detailed Pod Events

This is the most critical step. Kubernetes will usually tell you exactly why a pod isn't scheduling in its events log.

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Scroll down to the `Events` section. Look for messages from the `kube-scheduler` or `default-scheduler`. Common messages include:

*   `0/X nodes are available: Y insufficient cpu, Z insufficient memory.`
*   `0/X nodes are available: Y node(s) had taints that the pod didn't tolerate.`
*   `0/X nodes are available: Y node(s) didn't match node selector.`
*   `persistentvolumeclaim "my-pvc" is not bound.`

This output almost always gives you the specific predicate failure.

### 3. Check Node Resources (if `insufficient cpu/memory` is the issue)

If the events indicate resource constraints, investigate your nodes:

*   **List Nodes:**
    ```bash
    kubectl get nodes
    ```
    Ensure all nodes are `Ready`.

*   **Check Node Allocatable Resources and Usage:**
    ```bash
    kubectl describe node <node-name>
    ```
    Examine `Allocatable` resources (CPU, Memory) and compare them with `Capacity`. Then, check the `Allocated resources` section to see how much of the allocatable resources are currently being used by pods.

*   **View Live Node Resource Usage (requires `metrics-server`):**
    ```bash
    kubectl top nodes
    ```
    This gives you a quick overview of current CPU and memory consumption across your cluster. If `kubectl top` doesn't work, install `metrics-server`.

*   **Action:** If resources are genuinely scarce, you have a few options:
    *   **Increase Cluster Size:** Add more nodes to your cluster.
    *   **Scale Down Other Workloads:** Terminate or scale down less critical deployments to free up resources.
    *   **Adjust Pod Requests/Limits:** Reduce the `resources.requests.cpu` and `resources.requests.memory` in your pod's YAML. Be cautious, as this might impact performance.
    *   **Identify Misconfigured Pods:** Look for pods that are requesting excessive resources unnecessarily.

### 4. Examine Node Selectors, Affinity, and Tolerations

If the events point to node selectors or taints:

*   **Review Pod Spec:**
    ```bash
    kubectl get pod <pod-name> -n <namespace> -o yaml
    ```
    Look for `nodeSelector`, `affinity` (nodeAffinity, podAffinity, podAntiAffinity), and `tolerations` sections.

*   **Check Node Labels and Taints:**
    ```bash
    kubectl describe node <node-name>
    ```
    Compare the node's `Labels` and `Taints` with your pod's requirements.

*   **Action:**
    *   **Modify Pod Spec:** Adjust the `nodeSelector` or `tolerations` to match available nodes, or remove them if they're too restrictive.
    *   **Modify Node Labels/Taints:** Add/remove labels from nodes or update taints if it's an operational decision.

### 5. Persistent Volume Claim (PVC) Issues

If the `describe pod` output mentions an unbound PVC:

*   **Inspect PVC Status:**
    ```bash
    kubectl get pvc <pvc-name> -n <namespace>
    kubectl describe pvc <pvc-name> -n <namespace>
    ```
    Check its status (`Pending`, `Bound`) and events.

*   **Action:**
    *   **Check StorageClass:** Ensure the `StorageClass` referenced by the PVC (or the default if none specified) exists and is correctly configured.
    *   **Verify Provisioner:** Confirm that your storage provisioner is running and healthy (e.g., `csi-provisioner` pods).
    *   **Available PVs:** If using static provisioning, ensure `PersistentVolume` objects exist and match the PVC's requirements.

### 6. Review Kube-scheduler Logs (Advanced)

If `kubectl describe pod` provides no useful information (rare), or you suspect a scheduler issue itself, check the scheduler's logs.

```bash
kubectl get pods -n kube-system -l component=kube-scheduler
kubectl logs <kube-scheduler-pod-name> -n kube-system
```
Look for errors or warnings related to scheduling decisions.

## Code Examples

Here are some common commands and YAML snippets you might use when troubleshooting or adjusting:

### Get Pod Details

```bash
# Get all pods in default namespace
kubectl get pods

# Get all pods across all namespaces
kubectl get pods --all-namespaces

# Get detailed information about a specific pod in a specific namespace
kubectl describe pod my-nginx-deployment-abcde -n default
```

### Check Node Information

```bash
# Get summary of all nodes
kubectl get nodes

# Get detailed information about a specific node
kubectl describe node worker-node-1

# View current CPU/Memory usage of nodes (requires metrics-server)
kubectl top nodes
```

### Example Pod Manifest Adjustments

**Original Pod (potential Pending due to resource/node constraints):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - name: my-container
    image: my-repo/my-app:1.0
    resources:
      requests:
        memory: "2Gi"  # Requests 2GB memory
        cpu: "1"       # Requests 1 CPU core
```

**Scenario 1: Insufficient Resources**

If `kubectl describe pod` shows "insufficient cpu" or "insufficient memory", you might need to reduce the requests (if your application can handle it) or add more nodes.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app-reduced
spec:
  containers:
  - name: my-container
    image: my-repo/my-app:1.0
    resources:
      requests:
        memory: "512Mi" # Reduced memory request
        cpu: "250m"    # Reduced CPU request (0.25 core)
```

**Scenario 2: Node Selector Mismatch**

If `kubectl describe pod` shows "didn't match node selector", you might need to remove or modify the `nodeSelector`.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app-with-selector
spec:
  nodeSelector:
    kubernetes.io/hostname: specific-worker-node-1 # Pod requires this specific node
  containers:
  - name: my-container
    image: my-repo/my-app:1.0
    # ... (resources omitted for brevity)
```
To fix this, either update `kubernetes.io/hostname` to an existing node, or, if the requirement is not strict, remove the `nodeSelector` entirely.

**Scenario 3: Taints and Tolerations**

If `kubectl describe pod` shows "had taints that the pod didn't tolerate", you need to add a toleration to your pod.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app-with-toleration
spec:
  tolerations:
  - key: "special-purpose"        # Key of the taint
    operator: "Exists"            # Matches any value for this key
    effect: "NoSchedule"          # Effect of the taint (e.g., NoSchedule, PreferNoSchedule)
  containers:
  - name: my-container
    image: my-repo/my-app:1.0
    # ... (resources omitted for brevity)
```

## Environment-Specific Notes

The general troubleshooting steps apply across environments, but certain aspects become more prominent depending on where your Kubernetes cluster is running.

### Cloud Providers (EKS, GKE, AKS, DigitalOcean, etc.)

*   **Autoscaling:** Cloud environments often leverage cluster autoscaling. If pods are `Pending` due to insufficient resources, ensure your Cluster Autoscaler (if configured) has the correct permissions, is monitoring the right node groups, and isn't hitting any maximum capacity limits for your node pools or underlying instance types. I've often seen cases where the ASG maximum is too low, or it's trying to provision an instance type that isn't available in the specified region/zone.
*   **Managed Services:** For services like EKS, GKE, or AKS, issues with `kube-scheduler` itself are rare, as it's a managed component. Focus your attention on node health, resource availability, and specific cloud resource quotas (e.g., maximum instances, persistent disk limits).
*   **Storage Provisioning:** PVCs often rely on cloud-specific CSI drivers. Ensure your IAM roles/service accounts have the necessary permissions to provision storage volumes (e.g., EBS, Persistent Disk, Azure Disks).
*   **Networking:** Confirm your nodes have proper network connectivity within your VPC/VNet, especially to the API server and other cluster components. Incorrect security group rules or network ACLs can cause nodes to appear `NotReady`.

### Docker Desktop / Minikube (Local Development)

*   **Resource Limits of the VM:** For local development environments like Docker Desktop or Minikube, the most common cause of `Pending` pods is the underlying virtual machine running out of resources. You're operating on a single "node" (the VM), so there's no flexibility for the scheduler to place the pod elsewhere.
*   **Adjust VM Settings:** You need to increase the CPU and memory allocated to your Docker Desktop VM or Minikube instance.
    *   **Docker Desktop:** Go to Docker Desktop Settings -> Resources.
    *   **Minikube:** Use `minikube config set memory 8192` and `minikube config set cpus 4`, then `minikube delete` and `minikube start`.
*   **Single-Node Cluster:** Remember that these are single-node clusters by default. If your pod has advanced scheduling requirements (like anti-affinity or multiple node selectors), they might be impossible to satisfy in such a limited setup.

### On-Premise / Bare Metal

*   **Manual Provisioning:** On-premise clusters typically require manual node provisioning. Ensure that newly added nodes are correctly registered with the cluster, have all necessary Kubernetes components running (kubelet, kube-proxy, container runtime), and are genuinely `Ready`.
*   **Hardware Resources:** Physical resource limitations are a strict boundary. Carefully plan your resource requests/limits against actual server capacity.
*   **Storage:** Persistent Volume provisioning for PVCs can be more complex without integrated cloud storage. Solutions like NFS, Ceph, or iSCSI must be correctly set up and integrated with a `StorageClass` or static PVs. I've frequently debugged `Pending` pods where the storage backend was either full or improperly configured for volume provisioning.
*   **Network Configuration:** Pay close attention to network configuration, especially for multi-node setups and CNI plugins. Ensure all nodes can communicate, and that services like DNS are reachable.

## Frequently Asked Questions

**Q: What's the difference between a pod in `Pending` and a pod in `ContainerCreating`?**
A: A pod in `Pending` means the Kubernetes scheduler hasn't found a suitable node to run it on yet. It hasn't even started the process of downloading images or creating containers. A pod in `ContainerCreating` means it has been scheduled to a node, but the `kubelet` on that node is still in the process of starting its containers. This might involve pulling images, mounting volumes, or running init containers.

**Q: How can I prevent pods from getting stuck in `Pending` proactively?**
A: Proactive measures include:
    1.  **Accurate Resource Requests/Limits:** Set realistic CPU and memory `requests` for your pods.
    2.  **Cluster Autoscaling:** Implement and configure cluster autoscaling to automatically add nodes when resource pressure is high.
    3.  **Monitoring:** Regularly monitor your cluster's resource utilization (`kubectl top nodes`, Prometheus/Grafana dashboards) to identify potential bottlenecks before they cause `Pending` pods.
    4.  **Resource Quotas:** Use `ResourceQuota` objects to limit the total resources a namespace can consume, preventing one team from monopolizing resources.

**Q: Can a `Pending` pod eventually start on its own without intervention?**
A: Yes, it can. If cluster resources become available (e.g., another pod terminates, a node scales down/up, an unhealthy node becomes `Ready`), the `kube-scheduler` will continuously re-evaluate `Pending` pods and attempt to schedule them. However, if the issue is a fundamental mismatch (like an impossible `nodeSelector`), it will remain `Pending` indefinitely.

**Q: What if `kubectl describe pod` doesn't show any events or useful information?**
A: This is rare but indicates a deeper problem.
    *   **API Server Issues:** The `kube-apiserver` might be unhealthy or unreachable, preventing event propagation.
    *   **Kube-scheduler Issues:** The `kube-scheduler` itself might be down or misconfigured. Check its logs in the `kube-system` namespace.
    *   **Networking:** There might be network issues preventing `kube-scheduler` from communicating with the API server or nodes.

**Q: My pod is `Pending`, but `kubectl top nodes` shows plenty of free resources. Why?**
A: `kubectl top nodes` shows current resource *usage*, not *allocatable* resources for scheduling. The scheduler considers `requests` rather than actual usage. Even if a node shows low usage, it might not have enough *available capacity* to satisfy the pod's `requests` after accounting for existing `requests` from other pods. Additionally, `nodeSelectors`, `tolerations`, `hostPorts`, or `PVC` issues could be the problem, which aren't reflected in `kubectl top`. Always consult `kubectl describe pod` for the actual scheduling failure reason.

## Related Errors

*   [kubernetes-crashloopbackoff](/errors/kubernetes-crashloopbackoff.html)
*   [kubernetes-oomkilled](/errors/kubernetes-oomkilled.html)