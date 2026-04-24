# Nginx 502 Bad Gateway
> Encountering Nginx 502 Bad Gateway means your Nginx reverse proxy received an invalid response from an upstream server; this guide explains how to diagnose and fix it.

## What This Error Means

The Nginx 502 Bad Gateway error is an HTTP status code indicating that Nginx, acting as a reverse proxy or gateway, received an invalid response from an upstream server it was trying to access while fulfilling a client's request. Essentially, Nginx successfully connected to your backend application (the "upstream" server), but the response it got back wasn't something it could interpret as a valid HTTP response. It's like Nginx asked a question and got gibberish in return.

This isn't an error originating *within* Nginx itself, but rather Nginx reporting an issue in its communication with another server. Think of Nginx as the messenger; the message it received from the backend was malformed or incomplete, preventing it from relaying it properly to the client.

## Why It Happens

The 502 error typically happens because the upstream server, which Nginx is proxying requests to, is experiencing problems. Nginx expects a well-formed HTTP response, including status lines and headers, from the upstream. If the upstream server crashes, becomes overloaded, or simply sends something Nginx doesn't expect (e.g., a partial response, a corrupted stream, or no response at all within a very short timeframe), Nginx throws a 502.

In my experience, this usually points to an issue with the application or service running behind Nginx, rather than a problem with Nginx's core functionality. Nginx is just doing its job by reporting that its peer isn't behaving as expected.

## Common Causes

Diagnosing a 502 requires looking beyond Nginx itself and investigating the health and configuration of your backend services. Here are the most common culprits:

1.  **Upstream Server is Down or Crashed:** This is, by far, the most frequent reason. The backend application server (e.g., Node.js, Python/Django/Flask, PHP-FPM, Java/Spring Boot) might have crashed, stopped, or failed to start. Nginx connects, but nothing is listening or it gets an immediate connection reset.
2.  **Upstream Server Overloaded:** The backend server might be running but is struggling under heavy load (high CPU, memory exhaustion, too many open connections, out of file descriptors). It might accept Nginx's connection but then fail to process the request or respond within a reasonable timeframe. This can sometimes look like a 504 (Gateway Timeout), but if the server sends a malformed or partial response before timing out, Nginx might still register it as a 502.
3.  **Incorrect `proxy_pass` Configuration:** Nginx is configured to proxy requests to the wrong IP address or port, or a hostname that doesn't resolve correctly. While a DNS resolution failure might often result in a "connection refused" or an inability to connect, sometimes an incorrect `proxy_pass` can lead to unexpected responses if it connects to an unintended service.
4.  **Nginx Timeout Settings Too Low:** Your Nginx `proxy_connect_timeout`, `proxy_send_timeout`, or `proxy_read_timeout` values might be too aggressive. If the backend application takes longer than these configured timeouts to respond, Nginx will cut the connection and return a 502. This is particularly common for long-running processes or initial application startup.
5.  **Firewall or Security Group Blocking:** A firewall (either on the Nginx server, the upstream server, or an intermediary network device/security group in a cloud environment) might be blocking Nginx from communicating with the upstream server on the specified port. This often results in a `connect() failed` message in Nginx error logs, but can manifest as a 502 if the connection is allowed but subsequent data transfer is blocked or reset.
6.  **Backend Application Bugs or Errors:** The upstream application might have a bug that causes it to send malformed HTTP headers, an incomplete response body, or crash mid-response. This is especially true for custom applications or specific server configurations (like `php-fpm` or `uwsgi` that crash).
7.  **Resource Exhaustion on Upstream:** Beyond just CPU/memory, the upstream server might be running out of file descriptors, inode space (disk space for files), or available network sockets.
8.  **DNS Resolution Issues:** If `proxy_pass` uses a hostname, Nginx might have trouble resolving that hostname to an IP address, or it might resolve to an incorrect IP.

## Step-by-Step Fix

When a 502 hits, it's time for systematic troubleshooting. Here’s the approach I follow:

### Step 1: Check Upstream Server Status

This is your first port of call. Is the application Nginx is proxying to actually running and healthy?

*   **Linux Service:** If it's a systemd service, check its status:
    ```bash
    sudo systemctl status <your-application-service>
    ```
    Look for `Active: active (running)` and review recent logs.
    ```bash
    sudo journalctl -u <your-application-service> -f
    ```
*   **Docker Container:** If it's a Docker container, check its status and logs:
    ```bash
    docker ps -a # See if it's running or exited
    docker logs <container-id-or-name>
    ```
*   **Kubernetes Pod:** For Kubernetes deployments, check pod status and logs:
    ```bash
    kubectl get pods -n <namespace>
    kubectl logs <pod-name> -n <namespace>
    kubectl describe pod <pod-name> -n <namespace> # Look for events/restart reasons
    ```
    Pay close attention to recent errors, resource limits, or startup failures in the application logs.

### Step 2: Verify Upstream Connectivity from Nginx Server

From the Nginx server itself, try to directly connect to the upstream application's IP address and port. This bypasses Nginx and tests network connectivity and the upstream's listener.

*   **Using `curl`:**
    ```bash
    curl -v http://<upstream_ip_or_hostname>:<upstream_port>/<health_check_path>
    ```
    Replace placeholders with your actual backend details. For example, `curl -v http://127.0.0.1:8000/health`. Look for the HTTP response code and any body content. If `curl` hangs, it indicates a network issue or an unresponsive application.
*   **Using `telnet` (or `netcat`):**
    ```bash
    telnet <upstream_ip_or_hostname> <upstream_port>
    ```
    If it connects, you'll see a blank screen or a simple prompt. If it says `Connection refused` or `No route to host`, there's a network issue, firewall blocking, or the application isn't listening.

### Step 3: Review Nginx Error Logs

Nginx's `error.log` is gold. It will often give you a much more specific reason for the 502.

*   **Location:** Typically `/var/log/nginx/error.log`. The exact path might vary depending on your OS and Nginx installation (e.g., `/usr/local/nginx/logs/error.log`).
*   **Filter for 502 errors:**
    ```bash
    sudo tail -f /var/log/nginx/error.log | grep "502"
    # Or, to review recent errors:
    sudo grep "502" /var/log/nginx/error.log | tail -n 50
    ```
    Look for messages like:
    *   `upstream prematurely closed connection while reading response header from upstream`
    *   `connect() failed (111: Connection refused) while connecting to upstream`
    *   `recv() failed (104: Connection reset by peer) while reading response header from upstream`
    These messages directly point to the nature of the communication failure.

### Step 4: Examine Nginx Configuration (`proxy_pass`)

Ensure Nginx is configured to pass requests to the correct upstream server.

*   **Locate Configuration:** Nginx configurations are typically in `/etc/nginx/nginx.conf`, and often extended in `/etc/nginx/sites-enabled/` or `/etc/nginx/conf.d/`.
*   **Check `proxy_pass` directives:**
    ```bash
    grep -r "proxy_pass" /etc/nginx/conf.d/ /etc/nginx/sites-enabled/
    ```
    Verify the IP address, hostname, and port are exactly what your backend application is listening on. Even a tiny typo can cause issues.
*   **Test Nginx configuration syntax:**
    ```bash
    sudo nginx -t
    ```
    This command checks for syntax errors without reloading Nginx. If it passes, reload Nginx to apply changes: `sudo systemctl reload nginx`.

### Step 5: Adjust Nginx Proxy Timeouts

If your backend is slow to respond, Nginx might be cutting it off too early. This is a common fix if the backend *is* running, and `curl` tests pass eventually.

*   Increase `proxy_connect_timeout`, `proxy_send_timeout`, and `proxy_read_timeout` in your Nginx configuration. Start with 60s and increase if necessary.
*   Refer to the "Code Examples" section for a snippet. After making changes, run `sudo nginx -t` then `sudo systemctl reload nginx`.

### Step 6: Check Resource Limits on Upstream

An overloaded or resource-starved backend can cause 502s.

*   **CPU/Memory:** Use `top`, `htop`, `free -h` to monitor backend server resources.
*   **Disk Space:** `df -h` to check available disk space. `df -i` for inode usage.
*   **Open File Descriptors:** `ulimit -n` for the user running the application, or check system-wide limits. `lsof -p <pid_of_app_process> | wc -l` to see how many file descriptors your app is using.

### Step 7: Consider FastCGI/WSGI/uWSGI Specifics

If your backend is PHP-FPM, Gunicorn, uWSGI, etc., these specific application servers have their own configurations and logs.

*   **PHP-FPM:** Check `php-fpm` logs (e.g., `/var/log/php-fpm/error.log`), ensure the correct socket or port is configured, and check `request_terminate_timeout`. Nginx communicates via `fastcgi_pass`.
*   **Python (Gunicorn/uWSGI):** Ensure the WSGI server is running, listening on the correct socket/port, and that its workers aren't crashing. Check their respective logs.

### Step 8: Restart Nginx and Upstream

Sometimes, transient issues or a corrupted state can be resolved with a simple restart.

*   Restart your backend application: `sudo systemctl restart <your-application-service>`
*   Restart Nginx: `sudo systemctl restart nginx`

## Code Examples

Here are common Nginx configuration snippets you might use to resolve 502 errors.

### Nginx Proxy Timeout Configuration

Adjust these values within your `http` block for global effect or within a specific `server` or `location` block.

```nginx
# /etc/nginx/nginx.conf or /etc/nginx/conf.d/proxy.conf
http {
    # ... other http settings ...

    # Timeout for connecting to the upstream server
    proxy_connect_timeout       10s; # Default is 60s, but often set lower for responsiveness. Increase if needed.
    # Timeout for Nginx to send a request to the upstream server
    proxy_send_timeout          10s; # Default is 60s
    # Timeout for Nginx to read a response from the upstream server
    proxy_read_timeout          60s; # Default is 60s. Increase significantly for slow applications (e.g., 120s, 300s).

    # Buffer settings can also help with larger responses
    proxy_buffer_size           128k;
    proxy_buffers               4 256k;
    proxy_busy_buffers_size     256k;

    server {
        listen 80;
        server_name myapp.example.com;

        location / {
            proxy_pass http://my_backend_upstream;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # You can override global timeouts for specific locations if necessary
            # proxy_read_timeout 180s;
        }

        # Example for PHP-FPM using FastCGI
        location ~ \.php$ {
            fastcgi_pass unix:/var/run/php/php-fpm.sock; # Or a TCP address like 127.0.0.1:9000
            fastcgi_index index.php;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            include fastcgi_params;

            # FastCGI specific timeouts
            fastcgi_read_timeout 300s; # Adjust if PHP scripts are long-running
        }
    }
    upstream my_backend_upstream {
        server 127.0.0.1:8000; # Replace with your actual backend server
        # server backend.example.com:8000;
        # server unix:/var/run/my_app.sock; # For Unix sockets
    }
}
```

### Checking Nginx Configuration Syntax and Reloading

```bash
# Check configuration syntax before reloading
sudo nginx -t

# Reload Nginx to apply changes (doesn't drop connections)
sudo systemctl reload nginx

# Restart Nginx (drops existing connections, use if reload fails or for deeper reset)
# sudo systemctl restart nginx
```

### Direct Upstream Connectivity Test

```bash
# Test a basic HTTP GET request to your backend's health endpoint
curl -vvv http://127.0.0.1:8000/health

# Test if a port is open and listening
nc -vz 127.0.0.1 8000
# Or using telnet
telnet 127.0.0.1 8000
```

## Environment-Specific Notes

The 502 error manifests similarly across environments, but the tools and specific steps to diagnose vary.

### Cloud Environments (AWS, GCP, Azure)

*   **Security Groups/Network ACLs:** This is the #1 culprit in cloud environments. Ensure that the security group attached to your Nginx instance allows outbound traffic to the upstream server's IP and port, and that the upstream server's security group allows inbound traffic from the Nginx instance. I've spent countless hours debugging "phantom" 502s only to find a missing inbound rule.
*   **Internal Load Balancers:** If your Nginx proxies to an internal Load Balancer (e.g., AWS ALB, GCP Internal HTTP(S) Load Balancer), check the LB's health checks for its target groups. If the LB itself thinks the backend is unhealthy, Nginx will eventually get a bad response.
*   **Managed Services:** For managed databases, message queues, or serverless functions, consult their specific monitoring dashboards and logs for errors or throttling.

### Docker/Kubernetes

*   **Docker:**
    *   **Container Status & Logs:** Always start with `docker ps -a` and `docker logs <container_name_or_id>` for the backend application container. Check if it's continuously restarting (`restarting (X)`) or unhealthy.
    *   **Network:** Verify Nginx can reach the backend container. If they're on the same Docker network, `proxy_pass http://<service_name>:<port>;` should work. If not, check exposed ports and bridge networks.
*   **Kubernetes:**
    *   **Pod Status:** `kubectl get pods -n <namespace>` is your friend. Look for `CrashLoopBackOff` or `Error` states.
    *   **Pod Logs & Events:** `kubectl logs <pod-name> -n <namespace>` and `kubectl describe pod <pod-name> -n <namespace>` are crucial. Look for `OOMKilled` (out-of-memory), `Liveness probe failed`, `Readiness probe failed`.
    *   **Service & Endpoints:** Ensure your Kubernetes `Service` object correctly targets your backend pods, and that `kubectl get endpoints <service-name> -n <namespace>` shows healthy pod IPs.
    *   **Network Policies:** Verify no network policies are inadvertently blocking traffic between Nginx (or your Ingress controller) and the backend service.
    *   **DNS:** Kubernetes DNS resolution (`<service-name>.<namespace>.svc.cluster.local`) is fundamental; ensure your `proxy_pass` uses correct service names.

### Local Development

*   **Port Conflicts:** Ensure your backend application isn't trying to use a port already occupied by another service.
*   **Local Firewall:** Your OS firewall (e.g., `ufw` on Linux, Windows Defender Firewall, macOS firewall) might be blocking connections between Nginx and your application.
*   **Environment Variables:** Check that environment variables for your application are correctly set, especially database connections or other external service URLs. A misconfigured backend might crash silently.

## Frequently Asked Questions

**Q: Is the 502 error always a backend problem?**
A: Primarily, yes. The 502 signifies that Nginx received an invalid response *from* the backend. While Nginx itself might be misconfigured (e.g., incorrect `proxy_pass` or overly aggressive timeouts), the root cause is almost always the backend application not responding correctly or consistently.

**Q: What's the difference between 502 Bad Gateway and 504 Gateway Timeout?**
A: A **502 Bad Gateway** means Nginx successfully connected to the upstream server but received an invalid or unexpected response. A **504 Gateway Timeout** means Nginx waited for a response from the upstream server but did not receive *any* response within its configured timeout period. In a 504 scenario, the upstream might be too slow or completely unresponsive.

**Q: How can I prevent 502 errors from happening?**
A: Proactive monitoring is key. Implement robust health checks for your backend applications, use monitoring tools to track CPU, memory, and error rates, and set up alerts for high error rates or service downtime. Ensure proper resource provisioning, implement graceful shutdowns for applications, and use adequate Nginx timeouts to prevent premature disconnections for long-running requests.

**Q: My application logs show success, but Nginx still gives a 502. Why?**
A: This can be tricky. It often means your application completed its processing but failed *during* the response phase (e.g., writing the HTTP headers or body) or Nginx's connection to the application was reset by an intermediary network device or operating system limits. Check Nginx's `error.log` for clues like `upstream prematurely closed connection`. Resource limits (file descriptors, memory) on the backend can also cause this if the application runs out of resources while trying to send the response.

**Q: Can a firewall cause a 502?**
A: Yes. If a firewall between Nginx and the upstream server blocks the connection or resets it after initial setup, Nginx might interpret this as an invalid response or a premature connection closure, leading to a 502. The Nginx error logs might show `connect() failed (111: Connection refused)` or `recv() failed (104: Connection reset by peer)`.

## Related Errors

- [nginx-504](/errors/nginx-504.html)
- [kubernetes-crashloopbackoff](/errors/kubernetes-crashloopbackoff.html)