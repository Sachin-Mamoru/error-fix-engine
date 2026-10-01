# SQLAlchemy: Cannot connect to database
> Encountering "Cannot connect to database" means SQLAlchemy failed to establish a connection to the specified database; this guide explains how to fix it.

## What This Error Means

When SQLAlchemy throws a "Cannot connect to database" error, it's a fundamental signal that your application could not establish a communication channel with the intended database server. This isn't an issue with a malformed query or incorrect data; it's a failure at the most basic level of network connectivity or database server availability. It means that the initial handshake required to create a session between your Python application and the database simply did not complete.

This error typically manifests as an exception from the underlying database driver (e.g., `psycopg2.OperationalError`, `mysql.connector.Error`, `cx_Oracle.DatabaseError`) wrapped by SQLAlchemy, indicating a problem like "connection refused," "host unreachable," or "timeout."

## Why It Happens

This error happens for a variety of reasons, generally falling into three categories:
1.  **Network Issues:** The application server cannot reach the database server's IP address and port. This could be due to routing problems, firewalls, or DNS resolution failures.
2.  **Database Server State:** The database server itself is not running, is overloaded, or is not configured to accept connections from your application's host.
3.  **Authentication/Authorization:** While less common for a *connection* error (usually leading to an `AuthenticationFailed` or similar after connection), sometimes misconfigured database users or access rules can present as a connection refusal at certain layers. More often, this is a distinct error, but worth a quick check if other steps fail.

In my experience, this error is almost always a configuration problem, either with the database server, the network path, or the connection string itself.

## Common Causes

Let's break down the frequent culprits behind this persistent error:

*   **Incorrect Database Host or Port:** This is probably the most common oversight. A typo in the hostname (e.g., `localhoost` instead of `localhost`), an outdated IP address, or the wrong port number (e.g., using `5432` for MySQL instead of `3306`, or vice-versa for PostgreSQL) will prevent any connection from being established.
*   **Database Server Not Running:** The database service itself might be stopped, crashed, or simply hasn't been started. If the server isn't listening, no client can connect.
*   **Firewall Blocking Connection:** Both the client (your application's server) and the database server can have firewalls. A firewall on the database server might be blocking incoming connections on the database port from your application's IP address. Similarly, an outbound firewall on your application server could prevent it from initiating connections to the database.
*   **Incorrect User/Password (less common for *connection*, but can manifest):** While typically leading to an authentication error, a severely misconfigured user or access policy on the database side could theoretically refuse the connection outright. Always double-check credentials.
*   **DNS Resolution Issues:** If you're using a hostname instead of an IP address, your application server might be failing to resolve the hostname to the correct IP. This can happen with misconfigured DNS servers or specific network segments.
*   **Database Server Connection Limits:** The database server might have reached its maximum allowed concurrent connections. New connection attempts will then be rejected until existing connections are freed up.
*   **Network Latency or Instability:** In highly distributed systems, transient network issues, high latency, or packet loss can cause connection attempts to time out.
*   **Incorrect Database Name:** Although usually leading to a "database does not exist" type error after connection, if the driver tries to connect to a specific initial database *during* the connection phase and that database is somehow unavailable or inaccessible, it might manifest as a connection error.

## Step-by-Step Fix

Here’s a methodical approach to diagnose and resolve the "Cannot connect to database" error:

1.  **Verify Database Server Status:**
    *   **Is the database running?** Access the server where your database is hosted. For PostgreSQL, check with `sudo systemctl status postgresql` or `pg_ctl status`. For MySQL, `sudo systemctl status mysql` or `mysqld status`.
    *   **Is it listening on the correct port and interface?** Use `netstat -tulnp | grep <port>` (e.g., `netstat -tulnp | grep 5432` for PostgreSQL) to confirm the database process is listening on the expected port and interface (e.g., `0.0.0.0` or specific IP). If it's listening only on `127.0.0.1` (localhost) but your application is on a different server, that's a problem.

2.  **Check Network Connectivity from Application Server:**
    *   **Ping the database host:** From your application server, try to `ping` the database host.
        ```bash
        ping your_database_host.com
        ```
        If `ping` fails, it's a fundamental network reachability issue (DNS, routing, or the host is down).
    *   **Test port connectivity:** Use `telnet` or `nc` (netcat) to check if the database port is open and accessible from your application server.
        ```bash
        telnet your_database_host.com your_database_port # e.g., telnet db.example.com 5432
        # OR
        nc -zv your_database_host.com your_database_port
        ```
        If `telnet` connects (you see a blank screen or a database banner) or `nc` reports "succeeded!", then the network path and port are open. If it hangs or refuses connection, a firewall or network issue is likely.

3.  **Inspect Your SQLAlchemy Connection String:**
    *   **Double-check host, port, database name, user, and password.** Even a single character typo can cause failure.
    *   **Ensure the driver is correct.** `postgresql`, `mysql`, `mssql`, etc.
    *   **Are environment variables correct?** If you're constructing the string from environment variables, ensure they are correctly set in the environment where your application runs.

4.  **Examine Firewalls:**
    *   **Database Server Firewall:** Check `ufw status` (Ubuntu/Debian) or `firewall-cmd --list-all` (CentOS/RHEL) on the database server to ensure the database port (`5432` for PostgreSQL, `3306` for MySQL) is open to incoming connections from your application server's IP address (or the appropriate network range).
    *   **Application Server Firewall:** Less common for outbound connections, but ensure no outbound rules are blocking traffic to the database port.
    *   **Cloud Provider Security Groups/Network ACLs:** If using a cloud provider (AWS, Azure, GCP), verify that the security groups (AWS), network security groups (Azure), or firewall rules (GCP) associated with both your application server and database server allow traffic on the database port.

5.  **Test with Native Client:**
    *   From your application server, try connecting to the database using its native command-line client (e.g., `psql` for PostgreSQL, `mysql` for MySQL).
        ```bash
        # For PostgreSQL
        psql -h your_database_host -p your_database_port -U your_user -d your_database_name

        # For MySQL
        mysql -h your_database_host -P your_database_port -u your_user -p your_database_name
        ```
        If the native client can connect, it narrows the problem down to your Python application's configuration or environment. If it can't, the issue is definitely outside your Python code, likely network or database server-side.

6.  **Review Database Logs:**
    *   Check the database server logs (e.g., `/var/log/postgresql/` or `/var/log/mysql/`) for any connection attempts or error messages that might give more specific clues. Database logs often provide detailed reasons for connection refusals.

7.  **Check Database Connection Limits:**
    *   If your database server is under heavy load, it might be hitting its maximum connection limit. Check `max_connections` in your database configuration (e.g., `postgresql.conf`, `my.cnf`) and current connection counts.

## Code Examples

Here’s a basic SQLAlchemy connection attempt that demonstrates how to catch a connection error:

```python
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, DBAPIError
import os

# Example connection string (PostgreSQL)
# Using environment variables is best practice
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mydatabase")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Attempting to connect to: {DATABASE_URL.split('@')[1]}") # Print without credentials

try:
    # create_engine will not immediately connect unless you perform an operation
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5}) # Add a timeout for faster feedback

    # To force a connection and test it immediately, call .connect() or perform a simple query
    with engine.connect() as connection:
        # If we reach here, connection was successful
        result = connection.execute(sqlalchemy.text("SELECT 1"))
        print(f"Connection successful! Result: {result.scalar()}")

except OperationalError as e:
    print(f"SQLAlchemy OperationalError: Failed to connect to database.")
    print(f"Error details: {e}")
    print("Common causes: incorrect host/port, database not running, firewall blocking.")
except DBAPIError as e:
    print(f"SQLAlchemy DBAPIError: An error occurred during database interaction.")
    print(f"Error details: {e}")
    print("This usually indicates a problem with the underlying DB driver.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

This example demonstrates setting up an engine, attempting a connection, and specifically catching `OperationalError` which is the typical parent class for connection issues from SQLAlchemy's perspective. Adding `connect_timeout` can be helpful in development to fail faster instead of waiting for default system timeouts.

## Environment-Specific Notes

The "Cannot connect to database" error can behave differently and require distinct troubleshooting steps depending on your deployment environment.

*   **Local Development (e.g., `localhost`):**
    *   **Common culprits:** For `localhost` connections, the most frequent issues are the database service not running, or using an incorrect port if you have multiple database instances.
    *   **Firewall:** Your local machine's firewall (e.g., Windows Defender, macOS firewall, `ufw` on Linux) might be blocking connections even to `localhost` if not configured properly, though this is rare for default setups.
    *   **Credentials:** Ensure your user has access to `localhost` without requiring specific host-based authentication rules. In my experience, I've sometimes forgotten to set up a password for `postgres` user locally, leading to authentication errors that masquerade as connection problems.

*   **Docker/Docker Compose:**
    *   **Network:** This is a major area. Containers run in isolated networks.
        *   If using Docker Compose, services communicate via their service names (e.g., `db` instead of `localhost`). Your connection string's host should be the *service name* of your database container.
        *   Ensure your application container and database container are on the *same network*. Docker Compose handles this by default for services in the same `docker-compose.yml`.
        *   **Port Mapping:** The port you expose in `ports:` in `docker-compose.yml` (e.g., `5432:5432`) is for *host access*. Inside the Docker network, containers communicate directly via their internal database port (e.g., `5432` for Postgres).
    *   **DNS:** Docker's internal DNS usually works well for service names, but ensure no custom DNS resolver is breaking this.
    *   **Example `docker-compose.yml` fragment:**
        ```yaml
        services:
          app:
            build: .
            environment:
              DATABASE_URL: postgresql://user:password@db:5432/mydatabase # 'db' is the service name
            depends_on:
              - db
          db:
            image: postgres:13
            environment:
              POSTGRES_DB: mydatabase
              POSTGRES_USER: user
              POSTGRES_PASSWORD: password
            ports:
              - "5432:5432" # For host access, not usually needed for inter-container communication
        ```

*   **Cloud Environments (AWS, Azure, GCP, etc.):**
    *   **Security Groups/Network ACLs:** This is the *number one* cause in cloud environments. You *must* configure inbound rules on your database's security group (AWS), network security group (Azure), or firewall rules (GCP) to allow traffic on the database port from your application server's IP address or the security group/network that your application instance resides in. I've spent countless hours debugging this in production environments.
    *   **Private Endpoints/VPC Peering:** If your database is in a private network or a different VPC, ensure that VPC peering or private endpoints are correctly configured and that routing tables allow traffic between your application's network and the database's network.
    *   **IAM Roles/Service Principals:** While usually for authentication, sometimes misconfigured IAM roles for database access can lead to connection issues.
    *   **Public vs. Private IPs:** Be very careful whether you're using a public IP (often dynamic and less secure) or a private IP/DNS name. Ensure your application can resolve and reach the chosen IP/DNS.
    *   **Load Balancers:** If connecting via a load balancer, ensure the load balancer is healthy and correctly routing to the database instances.

## Frequently Asked Questions

**Q: Is "Cannot connect to database" always a network issue?**
A: Not exclusively, but it's very often a network or database server availability issue. It implies that the initial TCP handshake couldn't complete. If the database server is running but rejects the connection (e.g., due to `pg_hba.conf` rules in PostgreSQL or `bind-address` in MySQL), it's still often perceived as a "connection refused" at the network layer.

**Q: How do I check if my database server is listening on the correct port?**
A: On the database server, use `netstat -tulnp | grep <port>` (Linux/macOS) or `Get-NetTCPConnection -State Listen | Where-Object LocalPort -eq <port>` (PowerShell on Windows). Look for an entry with `0.0.0.0:<port>` or `<database_server_ip>:<port>`.

**Q: What if I can connect with `psql`/`mysql` command line tools, but not my SQLAlchemy application?**
A: This strongly suggests the issue is within your application's environment or code.
    *   **Environment Variables:** Are `DB_HOST`, `DB_PORT`, etc., set correctly for your application's process?
    *   **User Permissions:** Is the user your application runs as able to connect (e.g., does it have the necessary network permissions)?
    *   **Connection String:** Is the connection string built exactly as expected by SQLAlchemy, matching what the native client uses?
    *   **Python Environment:** Are all necessary Python database drivers (e.g., `psycopg2`, `mysqlclient`) installed in your application's virtual environment?

**Q: My application is in Docker and my database is also in Docker. How do they connect?**
A: If using Docker Compose, use the database service name as the host in your connection string (e.g., `postgresql://user:pass@db_service_name:5432/mydatabase`). Docker's internal DNS resolves service names within the same Docker network. If you're running containers manually, ensure they are connected to the same user-defined network (e.g., `docker run --network my-net ...`).

**Q: I'm seeing "connection timed out" instead of "connection refused". What's the difference?**
A: "Connection refused" usually means the connection request reached the database server, but the server actively rejected it (e.g., no process listening on that port, or a firewall on the server explicitly blocked it). "Connection timed out" means the client sent a connection request, but received no response within a certain period. This often indicates a more fundamental network path issue where the packets aren't even reaching the database server, perhaps due to a routing issue, a very restrictive firewall further up the network, or the database host being entirely unreachable.

## Related Errors
*(none)*