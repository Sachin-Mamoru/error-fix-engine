# PostgreSQL error: password authentication failed for user
> Encountering "password authentication failed for user" means your PostgreSQL server rejected login credentials; this guide explains how to fix it.

## What This Error Means

This error message, `FATAL: password authentication failed for user "your_user"`, indicates that your PostgreSQL server successfully received a connection request from a client but then denied access. Crucially, this is not a network connectivity problem (like "connection refused"), but rather an authentication issue. The server *heard* you, but didn't *trust* you. It means either the username or password provided by the client application was incorrect, or the `pg_hba.conf` configuration file on the server side didn't permit the attempted authentication method or client IP address for that user.

## Why It Happens

At its core, "password authentication failed" is a security mechanism doing its job. PostgreSQL is designed to ensure that only authorized users can access databases. When this error appears, it's because the credentials supplied by the client didn't match what the server expected, or the server's security policy (`pg_hba.conf`) prevented the connection for that specific user, database, and client IP combination. In my experience, it's often a simple typo or a mismatch between client and server expectations rather than a malicious attempt.

## Common Causes

Troubleshooting this error usually boils down to checking a few key areas:

1.  **Incorrect Password:** This is by far the most frequent cause. A typo, an outdated password in the client's configuration, or a recent password change on the server not yet updated in the application.
2.  **Incorrect Username:** Similar to passwords, an application might be configured with the wrong PostgreSQL username. Remember that PostgreSQL usernames are case-sensitive by default unless quoted.
3.  **`pg_hba.conf` Restrictions:** The `pg_hba.conf` (host-based authentication) file dictates which hosts can connect, to which databases, with which users, and using which authentication method. If your client's connection attempt doesn't match an allowed rule:
    *   **Wrong Authentication Method:** The client might be trying to connect using, say, `md5` password authentication, but `pg_hba.conf` expects `scram-sha-256`, `peer`, or `ident` for that specific connection type.
    *   **IP Address Mismatch:** The client's IP address might not be permitted by any rule for the specified user and database. This is common when connecting from a new machine or when a server's IP changes.
    *   **User/Database Restrictions:** The `pg_hba.conf` rules might explicitly deny a specific user access to a particular database, or `all` connections to `all` databases.
4.  **Client Driver/ORM Configuration Issues:** Sometimes, the application layer (e.g., a Python ORM like SQLAlchemy, a Java JDBC driver, or a Node.js `pg` module) isn't correctly picking up the credentials from environment variables or configuration files, leading to it sending default or incorrect values to the database.
5.  **Password Changes Not Propagated:** In environments with multiple services or microservices, a password change in the database might not have been updated across all dependent applications, leading to cascading authentication failures.
6.  **SSL/TLS Mismatch:** While less common for *this specific error*, a misconfigured SSL mode (`sslmode=require` on client, but server not configured for SSL, or vice versa) can sometimes lead to authentication issues, though it often manifests differently.

## Step-by-Step Fix

Here’s a practical approach I use to diagnose and resolve "password authentication failed" errors.

1.  **Verify Client-Side Credentials:**
    *   **Double-check your application's configuration:** Review the database connection string, environment variables, or configuration files (`.env`, `config.js`, `application.properties`) for the PostgreSQL username and password. Ensure there are no typos, extra spaces, or incorrect casing.
    *   **Test with `psql` locally:** Attempt to connect using the `psql` command-line client from the *same machine* where your application is running, mimicking its connection parameters. This isolates the issue from your application's code.

        ```bash
        # Try connecting from the client machine where your application runs
        # Replace placeholders with your actual values
        psql -h your_db_host -p 5432 -U your_user -d your_database
        ```
        When prompted, carefully enter the password. If this fails, you've confirmed the credentials are the problem.

2.  **Inspect `pg_hba.conf` on the PostgreSQL Server:**
    *   **Locate the file:** The `pg_hba.conf` file's location varies by operating system and PostgreSQL version. You can find its path by running `SHOW hba_file;` in a `psql` session (if you can connect as a superuser) or by looking in common locations like `/etc/postgresql/X.Y/main/pg_hba.conf` (Debian/Ubuntu) or within the `PGDATA` directory.
    *   **Understand `pg_hba.conf` rules:** Each line in `pg_hba.conf` specifies an access rule:
        `TYPE DATABASE USER ADDRESS METHOD [OPTIONS]`
        *   `TYPE`: `local` (Unix socket), `host` (TCP/IP), `hostssl` (TCP/IP with SSL), `hostnossl` (TCP/IP without SSL).
        *   `DATABASE`: The database(s) the rule applies to (e.g., `all`, `mydb`, `replication`).
        *   `USER`: The user(s) the rule applies to (e.g., `all`, `myuser`).
        *   `ADDRESS`: The client IP address(es) allowed (e.g., `127.0.0.1/32`, `0.0.0.0/0` for all IPv4).
        *   `METHOD`: The authentication method (e.g., `md5`, `scram-sha-256`, `trust`, `peer`, `ident`).
    *   **Identify the relevant rule:** Look for a line that matches your connection attempt (client IP, user, database). Ensure the `METHOD` is appropriate. For remote connections, `md5` or `scram-sha-256` are common. Avoid `trust` in production.
    *   **Common fix:** If your application connects from a remote IP (i.e., not `localhost`), ensure there's a `host` entry. If `md5` is failing and you want to use a more secure method, ensure `scram-sha-256` is configured. If you're trying to connect from a container and `pg_hba.conf` only allows `127.0.0.1`, you'll need to update it.
        ```
        # Example pg_hba.conf entry
        # TYPE  DATABASE        USER            ADDRESS                 METHOD
        host    all             all             0.0.0.0/0               scram-sha-256
        ```
        This example allows all users from any IPv4 address to connect to any database using `scram-sha-256` authentication. While convenient for testing, for production, I typically restrict `ADDRESS` to specific IP ranges.

3.  **Reload PostgreSQL Configuration:** After any change to `pg_hba.conf`, you *must* reload the PostgreSQL configuration for changes to take effect.
    ```bash
    # On systems using systemd (e.g., Ubuntu, CentOS)
    sudo systemctl reload postgresql

    # Or using pg_ctl
    pg_ctl reload -D /path/to/your/data/directory
    ```

4.  **Check PostgreSQL Server Logs:** The server logs provide invaluable detail. Look for `FATAL: password authentication failed for user "..."` and examine the lines immediately preceding it. They often include the client IP address and the database being targeted, which helps narrow down which `pg_hba.conf` rule is failing. Log locations typically include `/var/log/postgresql/`, or you can check `journalctl -u postgresql` on systemd-based systems.

5.  **Reset Password (If Unsure):** If you've tried everything and are still unsure about the correct password, or if you suspect it might have been compromised, reset it. You'll need superuser access.
    ```sql
    -- Connect as a superuser (e.g., 'postgres')
    ALTER USER your_user WITH PASSWORD 'new_strong_password';
    ```
    Immediately update all client applications and services with this new password.

## Code Examples

Here are some concise, copy-paste ready code snippets for common scenarios:

**1. `pg_hba.conf` for basic remote access:**

```ini
# Add this line to pg_hba.conf to allow connections from any IPv4 address
# using scram-sha-256 for all users to all databases.
# WARNING: 0.0.0.0/0 is insecure for most production systems without further restrictions.
# Replace with specific IP/range like 192.168.1.0/24 or your application server's IP.
host    all             all             0.0.0.0/0               scram-sha-256
```

**2. Reload PostgreSQL service:**

```bash
# For systems using systemd (e.g., Ubuntu 18.04+, CentOS 7+)
sudo systemctl reload postgresql
```

**3. Resetting a PostgreSQL user's password:**

```sql
-- Connect to your PostgreSQL database with a superuser (e.g., 'postgres')
-- Replace 'my_app_user' and 'SuperSecretPa$$w0rd'
ALTER USER my_app_user WITH PASSWORD 'SuperSecretPa$$w0rd';
```

**4. Testing connection with `psql`:**

```bash
# Connect to a remote host 'db.example.com' with user 'my_app_user' to 'app_db'
psql -h db.example.com -p 5432 -U my_app_user -d app_db

# Connect locally to user 'postgres'
psql -U postgres -d postgres
```

## Environment-Specific Notes

The "password authentication failed" error can manifest differently or require distinct troubleshooting steps depending on your deployment environment.

*   **Cloud (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL):**
    *   **`pg_hba.conf`:** In managed cloud environments, you rarely directly edit `pg_hba.conf`. Instead, you manage access through the cloud provider's console. For instance, on AWS RDS, you configure security groups (firewalls) to allow inbound connections from specific IP addresses or other security groups. Ensure your client's IP is allowed by the database's security group/firewall rules.
    *   **Password Management:** Passwords are reset via the cloud console or CLI, not usually with `ALTER USER` directly from `psql` unless connecting as the master user.
    *   **IAM Authentication:** Cloud providers often offer IAM-based authentication (e.g., AWS IAM database authentication). If you're using this, ensure your IAM roles and policies are correctly configured and that your client is using the correct token generation method. This bypasses traditional password authentication entirely.
    *   **Logs:** Access logs through the cloud provider's logging service (CloudWatch, Cloud Logging, Azure Monitor).

*   **Docker/Kubernetes:**
    *   **Environment Variables:** Credentials are often passed to the PostgreSQL container via environment variables (e.g., `POSTGRES_USER`, `POSTGRES_PASSWORD`). Verify these are correctly set in your `docker-compose.yml`, Kubernetes Deployment, or `docker run` command.
    *   **`pg_hba.conf`:** If you've customized your PostgreSQL Docker image, `pg_hba.conf` might be bind-mounted from the host or included in your Dockerfile. Ensure it permits connections from other containers within the Docker network or from the host if necessary.
    *   **Network Configuration:** Ensure your application container can reach the PostgreSQL container. This often involves ensuring they are on the same Docker network or using correct service names in Kubernetes.
    *   **Secrets Management:** In Kubernetes, use `Secrets` to manage database credentials securely, and ensure your deployments are correctly referencing them.

*   **Local Development:**
    *   **`pg_hba.conf` is Key:** When developing locally, `pg_hba.conf` is the most common culprit. Many default installations might use `peer` or `ident` authentication for `local` (Unix socket) connections, meaning it trusts the system user. If you're trying to connect via TCP/IP (`-h localhost`) and `pg_hba.conf` only has `peer` rules for `local`, you'll get an authentication error.
    *   **`ident` vs. `md5`/`scram-sha-256`:** If you're using `ident`, PostgreSQL expects the connecting operating system user to match the database user. If they don't, it will fail. Changing your `host` rule to `md5` or `scram-sha-256` for `127.0.0.1/32` is a common fix for local TCP/IP connections.
    *   **Default Users:** Remember that the default `postgres` user usually has no password set by default (or it's `peer` authenticated) on fresh installations. You might need to set one with `ALTER USER postgres WITH PASSWORD '...'`.

## Frequently Asked Questions

**Q: Why did this error start happening suddenly?**
**A:** This often happens due to a recent change: a password rotation was not fully propagated to all clients, an application was redeployed with outdated connection strings, a server's IP address changed requiring a `pg_hba.conf` update, or an automated `pg_hba.conf` update removed a necessary rule. Always check recent changes in your infrastructure.

**Q: Is "password authentication failed" a firewall issue?**
**A:** No, not directly. If you're seeing "password authentication failed," it means the network connection to the PostgreSQL server was successfully established. A firewall issue would typically result in a "connection refused" or "connection timed out" error, as the client wouldn't even reach the authentication stage.

**Q: Can I just use `trust` authentication to fix this?**
**A:** While `trust` authentication will certainly bypass the password prompt and resolve the error, it is **highly insecure** for any production or shared environment. `trust` allows any user who can connect to the server (based on `pg_hba.conf` rules) to log in as any PostgreSQL user without a password. Only use `trust` sparingly for specific, tightly controlled local development scenarios, and understand the risks.

**Q: How do I find the `pg_hba.conf` file on my server?**
**A:** If you can connect to `psql` as a superuser (e.g., the `postgres` user), you can run `SHOW hba_file;` to get the exact path. Otherwise, common locations include `/etc/postgresql/X.Y/main/pg_hba.conf` (where X.Y is your PostgreSQL version), or within your PostgreSQL data directory (e.g., `/var/lib/postgresql/X.Y/main/`).

**Q: My application is in a Docker container, and PostgreSQL is on the host. How do I configure `pg_hba.conf`?**
**A:** Your Docker container will likely connect from an IP address within Docker's internal network (e.g., `172.17.0.x`). You need a `pg_hba.conf` entry that allows connections from this subnet. A common, broad rule for testing is `host all all 172.17.0.0/16 scram-sha-256`, or you can allow all IPv4 with `0.0.0.0/0` (with appropriate security considerations).

## Related Errors
- [postgresql-connection-refused](/errors/postgresql-connection-refused.html)