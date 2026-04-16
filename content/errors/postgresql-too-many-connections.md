# PostgreSQL FATAL: remaining connection slots are reserved
> Encountering "FATAL: remaining connection slots are reserved" means your PostgreSQL database has hit its max_connections limit; this guide explains how to identify and resolve this critical issue.

## What This Error Means

This `FATAL` error indicates that your PostgreSQL database server has reached its configured limit for concurrent client connections. No new client connections can be established because all available slots are occupied. The "remaining connection slots are reserved" part refers to a small number of slots typically set aside for superusers. When even these reserved slots are inaccessible, or the system is so saturated it won't even grant regular connections, it signifies a critical bottleneck, preventing any further application interaction with the database.

## Why It Happens

PostgreSQL uses a vital configuration parameter called `max_connections` to cap the total number of simultaneous client connections it will accept. This limit is essential for preventing the database server from being overwhelmed by too many connections, each consuming system resources like memory and CPU. When the actual number of incoming connection requests surpasses the `max_connections` value, PostgreSQL rejects any subsequent attempts, leading to the `FATAL` error you see.

## Common Causes

In my experience, this error frequently surfaces due to one or more of these reasons:

1.  **Application Connection Leaks:** This is often the primary suspect. Applications might be opening database connections but failing to close them properly after use. Over time, these idle or "leaked" connections accumulate, gradually consuming all available slots until `max_connections` is hit. I've seen this in production when application code paths handling errors or specific edge cases neglect to close their database handles.
2.  **Sudden Traffic Spikes:** A sudden, unexpected surge in user traffic, background jobs, or even misconfigured cron jobs can flood the database with connection requests, quickly exhausting the `max_connections` limit.
3.  **Ineffective Connection Pooling:** While connection pooling is generally a good practice, a poorly configured or inefficient pool can still cause issues. For instance, a pool with too many idle connections or one that doesn't release connections fast enough can still put undue pressure on the database.
4.  **Long-Running or Hung Queries/Transactions:** Individual queries or transactions that execute for an unusually long time, or get stuck due to deadlocks or application logic errors, will hold onto their database connections indefinitely, contributing to the connection count.
5.  **Insufficient `max_connections` Configuration:** Sometimes, the `max_connections` parameter is simply set too low for the current application workload, server resources, or architectural design. This is particularly common after application scaling or migration to a new environment without adjusting database parameters.
6.  **Excessive Background Workers:** PostgreSQL extensions or tools like `pg_cron` that spawn numerous background processes can also consume connection slots. If these are misconfigured or experiencing issues, they can contribute significantly to the overall connection count.

## Step-by-Step Fix

Addressing this error typically involves immediate relief measures combined with long-term preventative adjustments.

1.  **Inspect Active Connections (If Possible):**
    If you can still connect as a superuser (which has reserved slots), use `psql` to view current connections with `pg_stat_activity`. This is your first step to understanding who or what is consuming connections.

    ```sql
    psql -U your_superuser_username -d your_database_name
    ```
    Once connected, run:
    ```sql
    SELECT pid, datname, usename, client_addr, application_name, backend_start, state, query_start, query
    FROM pg_stat_activity
    WHERE datname = current_database() -- Filter for current database
    ORDER BY backend_start DESC;
    ```
    Look for numerous connections from specific applications, long `query_start` times, or a high number of `idle` connections.

2.  **Terminate Stalled/Idle Connections (Emergency Only):**
    *   **WARNING:** Terminating connections abruptly can cause application errors, data inconsistencies, or rollback active transactions. Use this method only if absolutely necessary and with caution.
    *   If you identify connections that are clearly stuck or idle and can be safely terminated, use `pg_terminate_backend()`.
    ```sql
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = 12345; -- Replace 12345 with the PID you want to terminate
    ```
    In extreme cases where the database is completely unresponsive, a server restart might be the only immediate recourse.

3.  **Locate `postgresql.conf`:**
    The `max_connections` setting is defined in your PostgreSQL server's main configuration file, `postgresql.conf`. To find its exact location, connect via `psql` (if possible) and run:

    ```sql
    SHOW config_file;
    ```
    This will provide the full path, such as `/etc/postgresql/14/main/postgresql.conf`.

4.  **Modify `max_connections` in `postgresql.conf`:**
    *   Open the `postgresql.conf` file using a text editor (e.g., `sudo nano /path/to/postgresql.conf`).
    *   Find the `max_connections` parameter. It might be commented out with a `#`.
    *   Uncomment it (if necessary) and increase its value.
        *   **Crucial Note:** Avoid setting this value excessively high. Each connection consumes system memory. A sensible approach is to incrementally increase the value, typically aiming for 100-300 connections for many applications, depending on your server's available RAM and CPU. For example, if it was `100`, try `150` or `200`.

    ```ini
    # Connections
    max_connections = 200		# (example: increase from 100 to 200)
    ```

5.  **Restart PostgreSQL Server:**
    Changes to `max_connections` require a full PostgreSQL server restart to take effect.

    ```bash
    sudo systemctl restart postgresql
    # Or, depending on your operating system and PostgreSQL version:
    # sudo systemctl restart postgresql@14-main
    # sudo /etc/init.d/postgresql restart
    # sudo service postgresql restart
    ```

6.  **Monitor and Optimize:**
    After applying the change and restarting, continuously monitor your database connections using `pg_stat_activity` and integrate server resource monitoring.
    *   **Application-Level Fixes:** The most robust long-term solution involves addressing the root cause in your application. Ensure proper connection management, implement robust connection pooling within your application or using an external pooler (like PgBouncer), and optimize any long-running or inefficient queries.
    *   **Scaling:** If your application genuinely requires a very high connection count and your `max_connections` is already high, you might be hitting hardware limitations. Consider scaling up your database instance (more RAM/CPU) or exploring architectural changes like read replicas for read-heavy workloads.

## Code Examples

**1. Discovering the `postgresql.conf` file path:**
```sql
SHOW config_file;
```

**2. Querying active (non-idle) connections:**
```sql
SELECT pid, usename, datname, client_addr, application_name, state, query_start, query
FROM pg_stat_activity
WHERE state != 'idle' AND usename != 'postgres' -- Exclude superuser for clearer view of app connections
ORDER BY query_start DESC;
```

**3. Example of editing `postgresql.conf` with `nano`:**
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```
(Within the editor, locate `max_connections`, adjust the value, then save and exit: Ctrl+O, Enter, Ctrl+X.)

**4. Restarting the PostgreSQL service:**
```bash
sudo systemctl restart postgresql
# For specific versions/clusters, it might be:
# sudo systemctl restart postgresql@14-main
```

## Environment-Specific Notes

*   **Cloud Providers (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL):**
    *   Direct `postgresql.conf` file editing via SSH is typically **not possible**.
    *   You manage database parameters through the cloud provider's console or CLI tools. Look for "Parameter Groups" (AWS RDS), "Database flags" (GCP Cloud SQL), or "Server parameters" (Azure Database for PostgreSQL).
    *   Changing `max_connections` often necessitates a database instance restart, which the cloud console usually handles or prompts you for. Plan for brief downtime.
    *   Cloud providers frequently derive `max_connections` from the instance's memory size. Increasing it might require scaling up your instance class. For example, AWS RDS calculates `max_connections` based on instance memory divided by a certain value.

*   **Docker/Containerized Environments:**
    *   If PostgreSQL is running in a Docker container, the `postgresql.conf` file lives inside the container.
    *   The most common and recommended way to modify `max_connections` is by passing it as an environment variable (e.g., `POSTGRES_MAX_CONNECTIONS=200` to the `postgres` official image) when starting the container.
    *   Alternatively, you can mount a custom `postgresql.conf` file from your host into the container at the appropriate path (e.g., `/etc/postgresql/postgresql.conf` or `/var/lib/postgresql/data/postgresql.conf`).
    *   A container restart (e.g., `docker restart your_pg_container_name` or `docker-compose restart db`) is required for changes to take effect.

*   **Local Development:**
    *   The `postgresql.conf` file is usually located within your specific PostgreSQL data directory (e.g., `/usr/local/var/postgres` if installed via Homebrew on macOS, or `/var/lib/postgresql/data` on Linux).
    *   For testing, you can often be more liberal with `max_connections`, but still be mindful of your local machine's resources.
    *   Restarting the local server is straightforward, commonly `pg_ctl restart` or `brew services restart postgresql`.

## Frequently Asked Questions

**Q: Can I set `max_connections` to an extremely high number?**
**A:** No, that's not advisable. Each connection consumes a significant amount of RAM and other system resources. Setting `max_connections` too high can lead to your server running out of memory, excessive swapping to disk, and drastically degraded performance, potentially causing server instability or crashes. It's a balance between capacity and resource availability.

**Q: Will increasing `max_connections` permanently solve the issue?**
**A:** Not necessarily. While it provides immediate relief and more breathing room, if the underlying problem is an application connection leak, inefficient queries, or lack of proper connection pooling, simply increasing the limit will only defer the problem. The available connections will eventually fill up again. Always investigate and address the root cause.

**Q: What is the impact of restarting PostgreSQL to apply the changes?**
**A:** Restarting the PostgreSQL service will forcefully terminate all existing database connections, cause a brief period of downtime, and roll back any transactions that were in progress. Always plan restarts during maintenance windows or periods of low application traffic to minimize user impact.

**Q: When should I consider an external connection pooler like PgBouncer?**
**A:** For applications with high traffic, microservices architectures, or many application instances connecting to a single database, an external connection pooler like PgBouncer is highly recommended. It acts as an intelligent intermediary, managing a fixed, optimized set of connections to PostgreSQL, allowing your applications to connect to PgBouncer with many "virtual" connections without overwhelming the database itself.

## Related Errors
- [postgresql-connection-refused](/errors/postgresql-connection-refused.html)
- [redis-max-clients](/errors/redis-max-clients.html)