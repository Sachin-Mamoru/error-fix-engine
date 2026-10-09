# ConnectionRefusedError: [Errno 111] Connection refused
> Encountering `ConnectionRefusedError: [Errno 111] Connection refused` in Python means your application's attempt to connect to a network service was explicitly denied by the target; this guide explains how to diagnose and fix it.

## What This Error Means

The `ConnectionRefusedError: [Errno 111] Connection refused` is a common network-related exception in Python, particularly when your application tries to establish a TCP/IP connection to another service. The `Errno 111` specifically indicates that the connection attempt was actively rejected by the target machine.

Unlike a `TimeoutError`, where the connection attempt simply receives no response from the target within a specified duration, `ConnectionRefusedError` means the target machine *received* your request but explicitly chose *not* to accept it. Think of it like knocking on someone's door: a timeout is when no one answers, while a connection refused is when someone opens the door just enough to say "I'm not letting you in."

In my experience, this error is a clear signal that something fundamental is preventing the communication channel from being established. It’s not about data integrity or protocol errors yet; it’s about the very first handshake failing.

## Why It Happens

At its core, `ConnectionRefusedError` happens because the intended destination for your network request either isn't listening for connections on the specified port, or it has been configured to actively reject them. The underlying operating system, upon receiving the SYN packet from your client, attempts to forward it to a process bound to that port. If no process is listening, or if a firewall explicitly denies the connection, the OS sends back a RST (reset) packet, which your Python application then interprets as a `ConnectionRefusedError`.

This often points to an issue with the server-side component (the service you're trying to connect to) rather than the client-side, though client configuration or network issues can certainly contribute.

## Common Causes

Based on years of debugging this in various environments, here are the most frequent culprits for a `ConnectionRefusedError`:

1.  **The Target Service Is Not Running:** This is by far the most common reason. If you're trying to connect to a database (e.g., PostgreSQL, Redis), an API server, or a message queue (e.g., RabbitMQ), and that service's process isn't active on the target machine, there's nothing to accept the connection.
2.  **Incorrect Hostname or IP Address:** Your Python application might be configured to connect to the wrong IP address or hostname. The target machine exists, but it's not the one hosting the service you need.
3.  **Incorrect Port Number:** The service is running, but your application is trying to connect on the wrong port. For example, trying to connect to a web server on port 8080 when it's listening on 80.
4.  **Firewall Blocking the Connection:**
    *   **Local Firewall:** A firewall on the *client* machine (where your Python app is running) might be blocking outgoing connections to the target port.
    *   **Server Firewall:** A firewall on the *target* machine might be blocking incoming connections on the service's port.
    *   **Network Firewall/Security Group:** In cloud environments, network-level firewalls (like AWS Security Groups, Azure Network Security Groups, or GCP Firewall Rules) are frequently the cause, preventing traffic from reaching the target instance or service.
5.  **Service Binding to Wrong Interface:** The target service might be configured to listen only on a specific network interface (e.g., `127.0.0.1` for localhost only) while your client is trying to connect via an external IP address. Conversely, it might be binding to `0.0.0.0` but a firewall is blocking external access.
6.  **DNS Resolution Issues:** If you're using a hostname, a DNS issue could cause it to resolve to the wrong IP address, leading your application to attempt a connection to an unintended target.

## Step-by-Step Fix

When `ConnectionRefusedError` strikes, I approach it systematically. Here's my typical troubleshooting flow:

### Step 1: Verify the Target Service Status

The first and most important step is to confirm the target service is actually running on the correct machine.

*   **For services on Linux/Unix systems:**
    ```bash
    # Check if the service is active (e.g., PostgreSQL)
    sudo systemctl status postgresql

    # Or for any process listening on a specific port (e.g., 5432 for Postgres)
    sudo netstat -tulnp | grep 5432
    # Or, using lsof
    sudo lsof -i :5432
    ```
    You should see output indicating the service is `active (running)` and that a process is listening on the expected port. If not, start the service.

*   **For Docker containers:**
    ```bash
    # List running containers
    docker ps

    # Check logs of a specific container
    docker logs <container_id_or_name>
    ```
    Ensure your container is `Up` and check its logs for startup failures.

### Step 2: Check Host and Port Configuration

Double-check the hostname/IP address and port number your Python application is trying to connect to. This might be in your code, environment variables, or a configuration file.

*   **In your Python code:** Look for `host`, `port`, `address`, `server` parameters.
*   **Environment Variables:** Check `DATABASE_URL`, `REDIS_HOST`, etc.
*   **Config Files:** `settings.py`, `.env`, `config.ini`.

Then, from the *client* machine (where your Python app runs), try to manually test the connection to the target host and port.

```bash
# Test raw TCP connection (replace <host> and <port>)
# On Linux/macOS
nc -vz <host> <port>
# Example: nc -vz mydatabase.example.com 5432

# On older systems or if nc is not available, use telnet
telnet <host> <port>
# Example: telnet myapi.example.com 8000
```
If `nc` or `telnet` immediately shows "Connection refused" or fails, it confirms the issue is outside your Python application itself and deep in the network layer or the target service. If it hangs, it might indicate a firewall blocking, leading to a timeout rather than a refusal.

### Step 3: Inspect Firewalls (Client, Server, Network)

Firewalls are a frequent cause of `ConnectionRefusedError`, especially when moving between development and production environments.

*   **On the Client Machine:**
    *   **Linux (ufw):** `sudo ufw status` – ensure outgoing connections on your port aren't blocked.
    *   **Windows:** Windows Defender Firewall might be blocking your Python application.
    *   **macOS:** System Preferences > Security & Privacy > Firewall.
*   **On the Target Server Machine:**
    *   **Linux (ufw):** `sudo ufw status` or `sudo ufw allow <port_number>/tcp` to open the port.
    *   **Linux (firewalld):** `sudo firewall-cmd --list-all` or `sudo firewall-cmd --zone=public --add-port=<port_number>/tcp --permanent` then `sudo firewall-cmd --reload`.
    *   **Linux (iptables):** `sudo iptables -L -n` – look for `REJECT` rules.
*   **Cloud Provider Security Groups/Network Firewalls:**
    *   **AWS Security Groups:** Ensure the security group attached to your target instance (EC2, RDS, ElastiCache) has an inbound rule allowing TCP traffic on the correct port from the IP address or security group of your client instance. I've wasted many hours on this.
    *   **Azure Network Security Groups (NSGs):** Check inbound security rules.
    *   **GCP Firewall Rules:** Verify rules allowing ingress traffic.

### Step 4: Network Connectivity and DNS Resolution

Basic network reachability should be confirmed.

*   **Ping:** `ping <target_host_or_ip>` – ensures basic IP-level connectivity. If `ping` fails, you have a deeper network routing problem.
*   **DNS Check:** If using a hostname, verify it resolves to the correct IP.
    ```bash
    # On Linux/macOS
    dig <hostname>
    nslookup <hostname>
    ```
    Ensure the resolved IP matches your expectation for the target service.

### Step 5: Review Service Binding Configuration

Sometimes, the service itself is running, but it's configured to listen only on `127.0.0.1` (localhost) while your Python application is trying to connect to its external IP.

*   **PostgreSQL:** Check `listen_addresses` in `postgresql.conf`. It should be `*` or the specific IP addresses your client connects from, not just `localhost`.
*   **Redis:** Check `bind` directive in `redis.conf`.
*   **Web Servers (e.g., Gunicorn, Uvicorn):** Ensure they are binding to `0.0.0.0` if you intend for them to be accessible externally.

### Step 6: Check Logs of the Target Service

When all else fails, the logs of the *target service* itself are invaluable. They can reveal:
*   Why the service failed to start.
*   Why it couldn't bind to a port.
*   Explicit messages about rejecting connections.

Look for logs from the time your Python application attempted to connect.

## Code Examples

Here are simple Python code snippets that might raise this error and how to handle it.

```python
import socket
import requests
import sys

# Example 1: Basic socket connection attempt
def test_raw_socket_connection(host, port):
    print(f"Attempting raw socket connection to {host}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(f"Successfully connected to {host}:{port} via raw socket.")
        s.close()
    except ConnectionRefusedError:
        print(f"Error: Connection refused for {host}:{port}. Is the service running and accessible?", file=sys.stderr)
    except socket.gaierror:
        print(f"Error: Host '{host}' not found or unreachable.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

# Example 2: HTTP GET request using 'requests' library
def test_http_connection(url):
    print(f"Attempting HTTP GET to {url}...")
    try:
        response = requests.get(url, timeout=5) # Add a timeout for robustness
        response.raise_for_status() # Raise an exception for bad status codes
        print(f"Successfully fetched {url}. Status: {response.status_code}")
    except requests.exceptions.ConnectionError as e:
        if "Connection refused" in str(e):
            print(f"Error: Connection refused for {url}. Is the web server running and accessible?", file=sys.stderr)
        else:
            print(f"Error: A general connection error occurred for {url}: {e}", file=sys.stderr)
    except requests.exceptions.Timeout:
        print(f"Error: Request to {url} timed out.", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"An HTTP request error occurred: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    # This will likely cause ConnectionRefusedError if nothing is listening on 127.0.0.1:9999
    test_raw_socket_connection("127.0.0.1", 9999)

    # This will likely cause ConnectionRefusedError if no web server is running
    # or accessible at this URL, or if a firewall blocks it.
    test_http_connection("http://localhost:8000")
    test_http_connection("http://nonexistent-service.example.com:8080")
```

## Environment-Specific Notes

The `ConnectionRefusedError` can manifest differently or have specific common causes depending on your deployment environment.

### Local Development

*   **Forgot to start the service:** This is the most common issue. You're trying to connect to a local database (e.g., `redis-server`, `pg_ctl start`) or a local API service, but you simply forgot to start its process in a separate terminal.
*   **Localhost vs. IP:** Ensure your application is connecting to `127.0.0.1` or `localhost` if the service is meant to be local-only. Sometimes developers configure services to listen on `0.0.0.0` but then forget to account for a local firewall.
*   **Development Server Port Conflicts:** Another service might already be using the port your application or its target service expects. Use `netstat -tulnp` or `lsof -i :<port>` to check.

### Docker/Containers

*   **Port Mappings (`-p`):** Did you map the container's internal port to the host's external port correctly? `docker run -p 8000:8000 myapp` maps container port 8000 to host port 8000. If you try to access `localhost:8000` but the container is listening on 8080, you'll get a refusal.
*   **Container Networking:**
    *   **Bridge Network:** If containers are on the default `bridge` network, they might need to refer to each other by container name (with Docker DNS) or by their internal IP addresses.
    *   **Custom Bridge Network:** For inter-container communication, I highly recommend creating a custom bridge network (`docker network create my-network`) and connecting all relevant containers to it. Then, containers can resolve each other by their service names. Trying to connect to `localhost` from *inside* one container to another often fails.
    *   **Host Network:** Using `--network host` for a container means it shares the host's network stack, which bypasses some Docker networking complexities but can introduce port conflicts.
*   **Service Not Running Inside Container:** Just because the container is `Up` doesn't mean the service *inside* it is running correctly. Check `docker logs <container_id>`.

### Cloud Environments (AWS, Azure, GCP, etc.)

*   **Security Groups / Network Security Groups / Firewall Rules:** This is the *number one* cause of `ConnectionRefusedError` in cloud environments.
    *   **Ingress Rules:** Your EC2 instance's Security Group, RDS instance's Security Group, or Azure VM's NSG must have an inbound rule allowing TCP traffic on the correct port from the source IP range or security group where your Python application is running. Be specific, avoid `0.0.0.0/0` in production unless absolutely necessary.
    *   **Egress Rules:** Less common for `ConnectionRefused`, but confirm your client's security group allows outbound traffic to the target service.
*   **Public vs. Private IPs:** Are you trying to connect to a private IP from outside the VPC/VNet? Or to a public IP from within the same private network (which might be routed via the internet, or blocked)?
*   **VPC/VNet Peering:** If services are in different VPCs/VNets, ensure peering connections are set up correctly and routing tables updated.
*   **Managed Services:** For services like AWS RDS, Azure SQL Database, or GCP Cloud SQL, confirm the firewall/security group associated with the database allows connections from your compute instances.

## Frequently Asked Questions

**Q: Is `ConnectionRefusedError` the same as `TimeoutError`?**
**A:** No, they are distinct. `ConnectionRefusedError` means the target explicitly sent a refusal. `TimeoutError` means the connection attempt received no response at all within a specified duration, often because the target is down, network is congested, or a firewall silently drops packets.

**Q: How can I debug this in a production environment without direct shell access?**
**A:** Focus heavily on logs. Check the logs of both your client application and the target service. For cloud environments, meticulously review all firewall and security group rules. Network monitoring tools, if available, can also show if packets are being dropped or reset.

**Q: My service *is* running, but I still get the error. What gives?**
**A:** This usually points to a misconfigured firewall, an incorrect port number in your client application, or the target service binding to the wrong network interface (e.g., `127.0.0.1` instead of `0.0.0.0` or a specific external IP). Use `netstat -tulnp` on the server to confirm what IP address the service is listening on for the given port.

**Q: It works on my development machine, but not in Docker/on the server. Why?**
**A:** This is almost always a networking or firewall issue. On your dev machine, local firewalls might be more permissive, or the service might be binding to `localhost` which works fine. In Docker, it's often port mapping or inter-container networking. On a server, it's typically a server-side firewall (e.g., `ufw`, `iptables`) or a cloud security group/network firewall blocking the incoming connection.

**Q: Can a DNS issue cause `ConnectionRefusedError`?**
**A:** Yes. If a hostname resolves to an incorrect IP address (e.g., an old IP, or an IP where no service is running), your application will attempt to connect to that wrong address. If a machine exists at that address but doesn't have the expected service listening, it will refuse the connection.

## Related Errors