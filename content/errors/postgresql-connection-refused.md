# PostgreSQL: connection refused – could not connect to server
> Encountering "connection refused" for PostgreSQL means the client can't reach the server; this guide explains how to fix it by checking server status, configuration, and network.

## What This Error Means

When you encounter the "connection refused – could not connect to server" error with PostgreSQL, it's a clear signal from the operating system's networking stack, not from PostgreSQL itself. Unlike an authentication error (like "password authentication failed"), which indicates you successfully reached the server but failed to log in, "connection refused" means that the client application couldn't even establish a TCP connection to the PostgreSQL server process.

In simple terms, your client tried to knock on the door, but either no one answered, or the door was explicitly slammed shut by the network stack. This is fundamental networking, indicating a problem at the transport layer (TCP/IP) rather than within the application layer (PostgreSQL protocol).

## Why It Happens

This error arises when the client attempts to connect to a specific IP address and port, but there's no active process listening on that port at that address, or an intermediary network device (like a firewall) is actively blocking the connection attempt. It's a binary outcome: either a listener exists and accepts the connection, or it doesn't and the connection is refused.

I've seen this in production when a PostgreSQL service unexpectedly stopped, or after a configuration change prevented it from binding to the expected network interface. It's frustrating because it halts all database operations, but it's also relatively straightforward to diagnose once you understand its nature.

## Common Causes

Based on my experience as an SRE, here are the most frequent culprits behind a PostgreSQL "connection refused" error:

1.  **PostgreSQL Server Not Running:** This is by far the most common cause. The `postgres` daemon simply isn't active on the server.
2.  **Incorrect `listen_addresses` in `postgresql.conf`:** PostgreSQL is configured to listen only on `localhost` (127.0.0.1) while the client is trying to connect from a different IP address, or it's not listening on the required interface. A common misconfiguration is `listen_addresses = 'localhost'` when a remote client needs to connect.
3.  **Incorrect `port` in `postgresql.conf`:** The server is listening on a port different from the one the client is trying to connect to. The default is `5432`.
4.  **Firewall Blocking the Connection:** An operating system firewall (e.g., `ufw`, `firewalld`, `iptables`) or a network firewall (e.g., cloud security groups, corporate firewalls) is preventing inbound connections to the PostgreSQL port.
5.  **Client Application Misconfiguration:** The client is configured with the wrong host IP address or port for the PostgreSQL server.
6.  **Resource Exhaustion (Less Common for "Refused"):** While more likely to cause "connection timeout" or other errors, extreme resource pressure could, in rare scenarios, prevent the PostgreSQL server from binding to its port correctly on startup, leading to a "refused" status for new connections.

## Step-by-Step Fix

Here's a systematic approach to troubleshoot and resolve the "connection refused" error. Follow these steps methodically:

### 1. Verify PostgreSQL Service Status

The first and most critical step is to confirm that the PostgreSQL server process is actually running on the database host.

```bash
# For systems using systemd (most modern Linux distributions)
sudo systemctl status postgresql

# Expected output for a running server:
# ● postgresql.service - PostgreSQL RDBMS
#    Loaded: loaded (/lib/systemd/system/postgresql.service; enabled; vendor preset: enabled)
#    Active: active (running) since ...
#      Docs: man:postgres(1)
#            https://www.postgresql.org/docs/
#  Main PID: 12345 (postgres)
#     Tasks: 8 (limit: 4915)
#    Memory: 25.1M
#    CGroup: /system.slice/postgresql.service
#            ├─12345 /usr/lib/postgresql/13/bin/postgres -D /var/lib/postgresql/13/main -c config_file=/etc/postgresql/13/main/postgresql.conf
#            ├─12347 postgres: 13/main: checkpointer
#            ... (other postgres processes)

# If it's not running, start it:
sudo systemctl start postgresql
sudo systemctl enable postgresql # To ensure it starts on boot

# For systems using pg_ctl (less common for service management, but good for manual checks)
sudo -u postgres pg_ctl status -D /path/to/data/directory
```

If the service is not active, starting it should be your first action. If it fails to start, examine the logs (`journalctl -u postgresql` or PostgreSQL log files) for clues.

### 2. Check PostgreSQL Configuration (`postgresql.conf`)

If the service is running, the next likely culprit is a misconfiguration of `listen_addresses` or `port`.

First, find your `postgresql.conf` file. You can often locate it in `/etc/postgresql/<version>/main/postgresql.conf` on Debian/Ubuntu, or `/var/lib/pgsql/<version>/data/postgresql.conf` on RHEL/CentOS, or by running `psql -c "SHOW config_file;"` if you can connect locally.

Once located, inspect the `listen_addresses` and `port` parameters:

```bash
grep -E "listen_addresses|port" /etc/postgresql/13/main/postgresql.conf
```

*   **`listen_addresses`**:
    *   `'localhost'` or `'127.0.0.1'` means PostgreSQL only accepts connections from the local machine.
    *   `'*'` or `''` (empty string) means listen on all available network interfaces. This is often necessary for remote connections but requires careful firewall configuration.
    *   Specific IP addresses (e.g., `'192.168.1.100'`) mean it listens only on that interface.
    *   **Action:** If your client is remote, ensure `listen_addresses` includes the network interface the client will use, or set it to `'*'` for broad access (with appropriate firewall rules).
*   **`port`**:
    *   Ensure this matches the port your client is attempting to connect to (default is `5432`).

After modifying `postgresql.conf`, you *must* restart the PostgreSQL service for changes to take effect:

```bash
sudo systemctl restart postgresql
```

### 3. Verify Firewall Rules

A firewall, either on the PostgreSQL server's operating system or an external network firewall, can block the connection.

*   **Linux OS Firewalls:**
    *   **UFW (Ubuntu/Debian):**
        ```bash
        sudo ufw status verbose
        # If port 5432 is not allowed, enable it:
        sudo ufw allow 5432/tcp
        sudo ufw reload # Apply changes
        ```
    *   **Firewalld (RHEL/CentOS 7+):**
        ```bash
        sudo firewall-cmd --list-all
        # If port 5432 is not allowed, add it:
        sudo firewall-cmd --permanent --add-port=5432/tcp
        sudo firewall-cmd --reload # Apply changes
        ```
    *   **`iptables` (Older or custom setups):**
        ```bash
        sudo iptables -L -n | grep 5432
        # You'll need to add a rule to the INPUT chain if one doesn't exist.
        # This can be complex; consider using ufw or firewalld if available.
        ```
*   **Network Firewalls (Cloud Security Groups, Corporate Firewalls):**
    *   If your PostgreSQL server is in a cloud environment (AWS, GCP, Azure), check its associated Security Group, Network Access Control List (NACL), or equivalent firewall settings. Ensure inbound rules allow traffic on port 5432 from the IP address range of your client.

### 4. Test Connectivity from the Client

Once you've confirmed the service is running, configuration is correct, and firewalls are open, test basic network connectivity from the client machine.

```bash
# Using netcat (nc) - often installed by default
# Test if the port is open and listening
nc -vz <PG_SERVER_IP> 5432

# Expected output for success:
# Connection to <PG_SERVER_IP> 5432 port [tcp/*] succeeded!

# Using telnet (install if not present: sudo apt install telnet or sudo yum install telnet)
# Try to establish a raw TCP connection
telnet <PG_SERVER_IP> 5432

# Expected output for success:
# Trying <PG_SERVER_IP>...
# Connected to <PG_SERVER_IP>.
# Escape character is '^]'.
# (Then you can type something and press Enter, it will likely disconnect or show garbage)

# If it fails with "Connection refused" here, the issue is still on the server side (firewall, listen_addresses, or service down).
# If it hangs, it might be a network path issue or a firewall silently dropping packets ("connection timeout" is likely).
```

### 5. Attempt Connection with `psql` from Client

Finally, try connecting with the `psql` client from the machine where your application runs, specifying all connection parameters explicitly.

```bash
psql -h <PG_SERVER_IP> -p 5432 -U <USERNAME> -d <DATABASE_NAME>
```

Replace `<PG_SERVER_IP>`, `<USERNAME>`, and `<DATABASE_NAME>` with your specific details. If this works, your client application should also be able to connect, assuming its connection string is identical.

## Code Examples

Here are some concise, copy-paste ready code examples for common checks and fixes.

**1. Check PostgreSQL Service Status:**

```bash
sudo systemctl status postgresql
```

**2. Start PostgreSQL Service:**

```bash
sudo systemctl start postgresql
```

**3. Restart PostgreSQL Service after config changes:**

```bash
sudo systemctl restart postgresql
```

**4. Inspect `postgresql.conf` for `listen_addresses` and `port`:**

```bash
grep -E "listen_addresses|port" /etc/postgresql/13/main/postgresql.conf # Adjust path/version
```

**5. Allow PostgreSQL port through UFW firewall:**

```bash
sudo ufw allow 5432/tcp
sudo ufw reload
```

**6. Allow PostgreSQL port through Firewalld:**

```bash
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

**7. Test network connectivity from client to server:**

```bash
nc -vz <PG_SERVER_IP> 5432
```

**8. Connect using `psql` client:**

```bash
psql -h <PG_SERVER_IP> -p 5432 -U myuser -d mydb
```

## Environment-Specific Notes

The "connection refused" error manifests similarly across environments, but the specific tools and configurations to check can differ.

### Cloud Environments (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL)

In managed cloud database services, you generally don't control the operating system or `postgresql.conf` directly.

*   **Security Groups/Network Access:** This is almost always the first place to check.
    *   **AWS RDS:** Ensure the Security Group attached to your RDS instance allows inbound traffic on port 5432 from the IP address or security group of your application server.
    *   **GCP Cloud SQL:** Verify authorized networks are configured correctly, allowing connections from your client IPs.
    *   **Azure Database for PostgreSQL:** Check server firewall rules to ensure your client's IP address or virtual network is allowed access.
*   **Public vs. Private IP:** Confirm if your application is trying to connect via a public IP (if allowed and configured) or a private IP within the VPC/VNet (often requiring VPC peering or a direct connection).
*   **Connection String:** Double-check the host, port, username, and database name in your application's connection string against the cloud provider's console.

### Docker/Kubernetes

Containerized environments introduce an extra layer of networking abstraction.

*   **Docker:**
    *   **Port Mapping:** Ensure the Docker container port (e.g., `5432`) is correctly mapped to a host port (e.g., `docker run -p 5432:5432 ...`). If the client is external to the host, it needs to connect to the *host's* port.
    *   **Network:** Check if containers are on the same Docker network if they need to communicate using container names.
    *   **Logs:** Check the PostgreSQL container logs (`docker logs <container_id>`) for startup issues.
*   **Kubernetes:**
    *   **Service Definition:** Ensure your PostgreSQL Pod is exposed via a Kubernetes Service (e.g., `ClusterIP`, `NodePort`, `LoadBalancer`). The client needs to connect to the Service's IP and port, not directly to the Pod IP (unless it's an internal Pod-to-Pod connection).
    *   **Network Policies:** If network policies are in place, they might be blocking traffic to the PostgreSQL Pods.
    *   **Ingress/Egress:** For external access, ensure your Ingress controller or LoadBalancer is correctly configured to route traffic to the PostgreSQL Service.
    *   **Logs:** Check Pod logs (`kubectl logs <pod_name>`) for PostgreSQL errors.
    *   **`kubectl get svc` / `kubectl describe svc`:** Use these to inspect the service's configuration and endpoint.

### Local Development

For local setups, troubleshooting is usually simpler as there are fewer network hops.

*   **Localhost vs. 127.0.0.1:** Ensure consistency. `localhost` typically resolves to `127.0.0.1`.
*   **OS Firewall:** The primary culprit is often the local OS firewall (Windows Defender Firewall, macOS Gatekeeper). Temporarily disabling it (for testing only!) can help isolate the issue.
*   **Multiple PostgreSQL Installations:** I've occasionally seen conflicts where multiple PostgreSQL instances are installed and only one is running, or they're trying to use the same port. Use `netstat -tulnp | grep 5432` to see what process is listening.

## Frequently Asked Questions

**Q: Is "connection refused" an authentication error?**
**A:** No. A "connection refused" error means the client could not even establish a TCP/IP connection to the PostgreSQL server. An authentication error ("password authentication failed," "no pg_hba.conf entry") occurs *after* a connection has been established, when the server actively rejects the login attempt.

**Q: Why does it work when I connect from `localhost` but not from a remote machine?**
**A:** This is almost always due to either the `listen_addresses` parameter in `postgresql.conf` being set to `localhost` or `127.0.0.1`, or a firewall on the server or network blocking remote connections on port 5432.

**Q: What is the default port for PostgreSQL?**
**A:** The default port for PostgreSQL is `5432`. It's defined by the `port` parameter in `postgresql.conf`.

**Q: How can I find the `postgresql.conf` file?**
**A:** If you can connect to PostgreSQL locally (e.g., `psql -U postgres`), you can run `SHOW config_file;` from the `psql` prompt. Otherwise, common locations include `/etc/postgresql/<version>/main/postgresql.conf` (Debian/Ubuntu) or `/var/lib/pgsql/<version>/data/postgresql.conf` (RHEL/CentOS).

**Q: Can client-side SSL/TLS configuration cause this error?**
**A:** Not directly. SSL/TLS negotiation happens after the TCP connection is established. If SSL/TLS were the issue, you'd likely get a different error related to certificate validation or cipher mismatches, not "connection refused."

## Related Errors
- [kubernetes-connection-refused](/errors/kubernetes-connection-refused.html)
- [linux-address-in-use](/errors/linux-address-in-use.html)