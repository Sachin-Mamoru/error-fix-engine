# Nginx 502 Bad Gateway
> Encountering Nginx 502 Bad Gateway means your reverse proxy received an invalid response from an upstream server; this guide explains how to fix it.

## What This Error Means

The Nginx 502 Bad Gateway error indicates that Nginx, acting as a reverse proxy, received an invalid response from the upstream server it was trying to communicate with. Think of Nginx as a middleman between the client (web browser) and your actual application server (e.g., a PHP-FPM pool, a Gunicorn/UWSGI Python application, a Node.js process, or another web server). When a client requests a resource, Nginx forwards that request to the upstream server. If the upstream server replies with something Nginx doesn't understand as a valid HTTP response, or if it simply crashes before responding, Nginx shows a 502.

It's important to differentiate this from other errors:
*   **504 Gateway Timeout:** This means Nginx didn't receive *any* response from the upstream server within a specified timeout period. The connection might have been made, but the upstream was too slow to respond or completely hung.
*   **Connection Refused:** Nginx couldn't even establish a connection to the upstream server. This often points to the upstream service not running or a firewall blocking the connection.

A 502 suggests that Nginx *did* connect, but what came back was unusable.

## Why It Happens

At its core, a 502 Bad Gateway happens because the upstream application server, which Nginx is proxying requests to, failed to fulfill the request properly. This failure isn't necessarily a network issue between Nginx and the upstream, but rather a problem within the upstream application itself or how Nginx is configured to interact with it. Nginx successfully initiated communication but then encountered a non-HTTP response, an incomplete response, or the upstream server crashed mid-request.

Common scenarios involve an upstream service that is either down, overloaded, misconfigured, or experiencing internal errors that prevent it from sending a well-formed HTTP response back to Nginx.

## Common Causes

In my experience, 502s typically boil down to one of these recurring issues:

1.  **Upstream Server is Down or Crashed:** This is, by far, the most frequent cause. The application server (e.g., PHP-FPM, Gunicorn, Node.js process) that Nginx is trying to proxy requests to is simply not running, has crashed, or is restarting.
2.  **Upstream Server Overloaded/Unresponsive:** The application server is running but is under such heavy load (high CPU, memory exhaustion, too many open connections, slow database queries) that it cannot process requests in a timely manner or respond correctly. While this often leads to a 504 timeout, it can also manifest as a 502 if the upstream process terminates unexpectedly due to resource limits during processing.
3.  **Nginx Timeouts Are Too Short:** Nginx has configured timeouts (e.g., `proxy_read_timeout`, `fastcgi_read_timeout`) that are shorter than the time your upstream application needs to process certain requests. If the upstream application is working on a long-running task, Nginx will cut off the connection and return a 502 (or 504, depending on the exact timing).
4.  **Incorrect Nginx Configuration:**
    *   `proxy_pass` directive points to the wrong IP address or port for the upstream server.
    *   Incorrect FastCGI, uWSGI, or SCGI parameters are passed, leading the upstream to misinterpret the request or respond incorrectly.
    *   Nginx is configured to expect a certain protocol (e.g., FastCGI) but the upstream server is responding with something else (e.g., plain HTTP, or internal error messages).
5.  **Resource Limits on Upstream or Nginx:**
    *   **Upstream:** The application server hits limits on open file descriptors, available memory, or CPU, leading to crashes or inability to respond.
    *   **Nginx:** Less common for 502s, but Nginx itself could run into file descriptor limits or memory issues if handling a massive number of concurrent connections or very large buffers.
6.  **FastCGI/uWSGI Protocol Errors:** When Nginx communicates with PHP-FPM via FastCGI, or Python applications via uWSGI, protocol-level errors from the application can cause a 502. This often happens if PHP-FPM crashes, or if a Python script prints unhandled errors directly to `stdout` instead of returning a proper HTTP response.

## Step-by-Step Fix

Troubleshooting a 502 requires a systematic approach, often starting from the upstream server and working back to Nginx.

1.  ### **Check Upstream Server Status First**
    This is your absolute first step. A 502 nearly always points to the application behind Nginx.
    *   **Is your application service running?** For systemd-managed services (like PHP-FPM, Gunicorn, Node.js applications configured as services):
        ```bash
        sudo systemctl status php7.4-fpm # Example for PHP-FPM
        sudo systemctl status my-gunicorn-app # Example for Gunicorn
        ```
        Look for `active (running)` status. If it's `inactive` or `failed`, start it:
        ```bash
        sudo systemctl start php7.4-fpm
        ```
    *   **If using Docker/Kubernetes:**
        ```bash
        docker ps -a # Check if containers are running or exited
        kubectl get pods -o wide # Check pod status in Kubernetes
        ```
        If the service isn't running, this is your immediate fix.

2.  ### **Examine Nginx Error Logs**
    Nginx will log information about *why* it received a bad gateway response.
    *   The primary Nginx error log is usually located at `/var/log/nginx/error.log` (this path can vary based on your Nginx configuration).
    *   Use `tail -f` to watch the log in real-time while trying to reproduce the error:
        ```bash
        tail -f /var/log/nginx/error.log
        ```
    *   Look for messages like:
        *   `upstream prematurely closed connection`
        *   `connect() failed (111: Connection refused)` (though this usually leads to 504 or direct connection refused, it can manifest as 502 in some Nginx versions/configs)
        *   `upstream timed out`
        *   `No such file or directory` (often related to FastCGI socket paths)
        *   `recv() failed`
    These messages provide crucial clues about the interaction between Nginx and the upstream.

3.  ### **Examine Upstream Application Logs**
    Once Nginx logs indicate a problem with the upstream, dive into the upstream application's own logs. These will tell you *why* the application failed to respond correctly.
    *   **PHP-FPM:** Look at `/var/log/php-fpm/www-error.log` or similar (check your `php-fpm.conf` or pool config for `error_log` directive).
    *   **Python (Gunicorn/uWSGI):** Application logs often go to `stdout`/`stderr` of the process, which might be redirected to files configured in your `systemd` service unit, `gunicorn.conf`, or `uwsgi.ini`.
    *   **Node.js:** Similar to Python, check where `stdout`/`stderr` is logged.
    *   **Docker/Kubernetes:** Use `docker logs <container-id>` or `kubectl logs <pod-name>` respectively.
    Look for unhandled exceptions, memory errors, segmentation faults, database connection issues, or any stack traces. This is where you'll find the root cause of the application's failure.

4.  ### **Verify Nginx Configuration**
    A misconfiguration in Nginx can direct requests to the wrong place or expect the wrong protocol.
    *   **Check `proxy_pass` or `fastcgi_pass`:** Ensure it points to the correct IP address/hostname and port, or the correct Unix socket path, for your upstream application.
    *   **Validate Nginx syntax:** Always run a syntax check after making changes:
        ```bash
        sudo nginx -t
        ```
        If it reports successful, reload Nginx:
        ```bash
        sudo systemctl reload nginx
        ```
    *   Review `include` directives to ensure all relevant configuration files are loaded.

5.  ### **Adjust Nginx Timeout Settings**
    If Nginx logs show "upstream timed out" and your application logs indicate long-running processes (e.g., complex reports, bulk operations), increase Nginx's timeout values.
    *   `proxy_connect_timeout`: Time to establish a connection with the upstream.
    *   `proxy_send_timeout`: Time for Nginx to send a request to the upstream.
    *   `proxy_read_timeout`: Time Nginx waits for a response from the upstream *after* sending the request. This is often the critical one for 502s related to slow applications.
    *   For FastCGI, look at `fastcgi_read_timeout`.
    Increase these incrementally, keeping in mind that extremely long timeouts can tie up Nginx worker processes.

6.  ### **Review System Resource Limits**
    Sometimes, the issue isn't the application code itself but the environment it runs in.
    *   **Open File Descriptors (FDs):** If the application or Nginx hits its `ulimit -n` (max open files) limit, it can fail. Check `ulimit -n` for the user running the processes.
    *   **Memory/CPU:** Monitor the upstream application's resource usage. High memory consumption can lead to `OutOfMemory` errors and process termination, resulting in a 502. `top`, `htop`, `free -h` are your friends here. I've seen this in production when a background process unknowingly started consuming all available memory, starving the main web application.
    *   **Swap usage:** Excessive swap usage can slow down a system dramatically, contributing to timeouts.

## Code Examples

Here are common Nginx configuration adjustments that often resolve 502 errors related to timeouts or buffering.

### Increasing Nginx Proxy Timeouts

This is relevant when Nginx proxies HTTP requests to another HTTP server (e.g., Gunicorn, Node.js app).
Add these directives to your `http` block, `server` block, or specific `location` block.

```nginx
http {
    # ... other http settings ...

    # Default timeout settings for all proxy passes
    proxy_connect_timeout 60s;
    proxy_send_timeout    60s;
    proxy_read_timeout    180s; # Increase this for slow backend responses

    server {
        listen 80;
        server_name example.com;

        location / {
            proxy_pass http://my_upstream_app; # e.g., http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # You can override timeouts for a specific location if needed
            # proxy_read_timeout 300s;
        }

        # ... other locations ...
    }
}
```

### Adjusting FastCGI Buffering and Timeout

This applies when Nginx communicates with a FastCGI process, most commonly PHP-FPM. Adjusting buffers can help with large PHP responses, while `fastcgi_read_timeout` addresses slow PHP script execution.

```nginx
server {
    listen 80;
    server_name example.com;
    root /var/www/html;
    index index.php index.html;

    location ~ \.php$ {
        try_files $uri =404;
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock; # Or your specific PHP-FPM socket
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;

        # Increase FastCGI buffer sizes for large PHP responses
        fastcgi_buffers 16 16k; # Default might be 8 4k or 8 8k
        fastcgi_buffer_size 32k; # Size of the first buffer

        # Increase timeout for slow PHP scripts
        fastcgi_read_timeout 300; # Default is 60s, increase if scripts take longer
    }

    # ... other locations ...
}
```

Remember to run `sudo nginx -t` and `sudo systemctl reload nginx` after any configuration changes.

## Environment-Specific Notes

The context of your deployment environment significantly impacts how you troubleshoot and resolve 502 errors.

### Cloud Environments (AWS, GCP, Azure, etc.)

*   **Load Balancers:** If you're using a cloud load balancer (e.g., AWS ALB/NLB, GCP Load Balancer), check its target group health checks. If an instance or pod is failing health checks, the load balancer might stop sending traffic to it, but direct Nginx requests could still hit it. A 502 might mean Nginx received a bad response, but the load balancer also timed out or marked the target unhealthy.
*   **Security Groups/Firewalls:** Ensure that the security groups (AWS) or firewall rules (GCP/Azure) allow Nginx to connect to the upstream application's port on the backend instance. While this often manifests as a connection refused (not 502), a misconfigured rule could theoretically disrupt the response flow.
*   **Instance Health:** Confirm the cloud instance running your upstream application is healthy and has sufficient resources. Check CPU utilization, memory, and disk I/O metrics provided by your cloud provider.

### Docker and Containerized Environments

*   **Container Status:** Use `docker ps -a` or `docker-compose ps` to see if your application container has stopped or is restarting in a loop (`Exited`, `Restarting`). `docker logs <container-id>` is invaluable for application-level errors.
*   **Networking:**
    *   **Port Mapping:** Is the port inside the container correctly mapped to the host port, and is Nginx trying to connect to the correct host port?
    *   **Docker Networks:** If Nginx and the upstream app are in different Docker containers, ensure they are on the same Docker network or Nginx is configured to use the correct service name/IP for inter-container communication. Using service names in `docker-compose.yml` makes this easier.
    *   *Personal experience:* I've often forgotten to link containers or put them on the same network, leading Nginx to try and connect to a non-existent host or port.
*   **Resource Limits:** Docker containers can have CPU and memory limits. If the upstream application hits these limits, it can crash, leading to a 502.

### Kubernetes

*   **Pod Status & Logs:** `kubectl get pods` will show you if your application pods are in a `Running` state. Look for `CrashLoopBackOff`, `Error`, or `Pending` states. `kubectl describe pod <pod-name>` can give details on why a pod isn't running. `kubectl logs <pod-name>` will show the application's standard output/error, which is critical for debugging.
*   **Readiness/Liveness Probes:** Misconfigured or failing `readiness` probes can cause an Ingress controller (which acts as Nginx) to stop routing traffic to an unhealthy pod, but if Nginx *does* route and the app is struggling, a 502 can occur.
*   **Service & Endpoint Configuration:** Ensure your Kubernetes `Service` correctly targets your application pods via labels, and that the `Endpoints` are showing the correct pod IPs. An `Ingress` resource often routes to a `Service`, which then load balances across pods.

### Local Development

*   **Simple Restart:** Often, a simple restart of the application server (e.g., `npm start`, `python app.py`, `php -S localhost:8000`) resolves local 502s if the application crashed.
*   **Port Conflicts:** Ensure your application isn't trying to run on a port already in use, or that Nginx isn't trying to proxy to the wrong port.
*   **Firewalls:** Your local machine's firewall could be blocking Nginx from communicating with your local application.
*   **Environment Variables:** Check `.env` files or other local configuration for correct database connections, API keys, etc., that might cause your application to fail.

## Frequently Asked Questions

**Q: What's the fundamental difference between a 502 Bad Gateway and a 504 Gateway Timeout?**
**A:** A **502 Bad Gateway** means Nginx successfully connected to the upstream server, but the upstream returned an invalid or unparseable response, or crashed. Nginx *received something* but couldn't use it. A **504 Gateway Timeout** means Nginx *did not receive any response at all* from the upstream server within its configured timeout period. The upstream was either too slow, completely unresponsive, or Nginx couldn't establish a connection within the connection timeout.

**Q: Can client-side issues cause an Nginx 502?**
**A:** Indirectly, yes. While the 502 itself originates from the upstream server's failure to Nginx, a malformed, excessively large, or highly resource-intensive request from a client could cause the upstream application to crash or become unresponsive, leading to a 502 for that request or subsequent ones. However, the error isn't *due to* the client's network or browser itself.

**Q: My application works perfectly when I access it directly (bypassing Nginx), but I get a 502 through Nginx. Why?**
**A:** This strongly points to an Nginx configuration issue, timeout settings, or network/firewall problems specifically between Nginx and your application. When you access it directly, you're not subject to Nginx's proxy settings, timeouts, or network routes. Check Nginx's `proxy_pass` directive, its timeout values, and ensure no firewalls block Nginx's outbound connection to the application.

**Q: How can I prevent 502 errors from recurring in a production environment?**
**A:** Proactive measures are key. Implement robust monitoring for your upstream applications (CPU, memory, process health, error rates, log aggregators). Use health checks (Liveness/Readiness probes in Kubernetes, load balancer health checks) to automatically remove unhealthy instances. Optimize your application for performance, especially long-running tasks. Configure Nginx timeouts generously enough for typical application response times, but not so long that it ties up Nginx resources unnecessarily. Finally, ensure your deployment process includes thorough testing and rollback capabilities.

## Related Errors