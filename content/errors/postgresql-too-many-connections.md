# PostgreSQL FATAL: remaining connection slots are reserved
> Encountering "FATAL: remaining connection slots are reserved" means your PostgreSQL database has hit its max_connections limit; this guide explains how to fix it.

## What This Error Means

This error message, `FATAL: remaining connection slots are reserved`, indicates a critical state in your PostgreSQL database. It means that the database server has reached its configured maximum number of concurrent connections (`max_connections`), and critically, *even the reserved slots for superusers are now in use or unreachable*.

PostgreSQL reserves a small number of connection slots (typically 2-4) for superusers by default. This is a safeguard, allowing an administrator to connect and troubleshoot even when the database is overwhelmed with regular user connections. When you see this specific `FATAL` error, it signifies that not only have all regular connection slots been exhausted, but these superuser slots are also either already in use, or the server is so resource-starved that it cannot even accept new superuser connections. Essentially, your database is effectively unreachable for new connections, preventing applications and even administrators from connecting.

## Why It Happens

PostgreSQL allocates a certain amount of memory and other resources for each active connection. The `max_connections` parameter is a crucial configuration setting that limits the total number of concurrent client connections the PostgreSQL server will accept. This limit is in place to prevent the server from becoming overloaded, exhausting its system resources (like RAM or CPU), and potentially crashing.

When the number of incoming connection requests exceeds the `max_connections` limit, PostgreSQL rejects any new connection attempts. If the server is still somewhat functional, it might respond with a less severe message indicating `max_connections` was reached. However, the `FATAL: remaining connection slots are reserved` message usually points to a more dire situation where the server is completely saturated or struggling significantly, indicating a severe resource bottleneck or a runaway process consuming all available slots.

In my experience, this often points to an application misconfiguration or an unexpected spike in demand that the current database sizing or configuration cannot handle.

## Common Causes

Identifying the root cause is the first step to a lasting fix. Here are the most common culprits I've encountered that lead to this `FATAL` error:

1.  **Insufficient `max_connections`:** The simplest cause is that the configured `max_connections` value in `postgresql.conf` is simply too low for your application's actual needs or current workload. As applications scale or traffic increases, this value often needs adjustment.
2.  **Lack of Connection Pooling (or Misconfigured Pooling):**
    *   **No Pooling:** Applications that establish a new database connection for every single request, without reusing them, are prime candidates for quickly exhausting `max_connections`.
    *   **Misconfigured Pool:** Even with a connection pool, if the pool's `max_size` is set too high (e.g., greater than `max_connections` or if multiple application instances each have large pools), it can collectively overwhelm the database.
3.  **Unclosed Connections/Connection Leaks:** Application code that opens database connections but fails to close them properly (e.g., due to unhandled exceptions, incorrect `finally` blocks, or poor resource management) will lead to an accumulation of "leaked" connections that never return to the pool or are released, eventually consuming all available slots. I've seen this in production when developers forget to properly manage resource lifecycles.
4.  **Long-Running Queries or Transactions:** Queries or transactions that take an unusually long time to complete can hold connections open for extended periods, reducing the availability of slots for other incoming requests. This is especially problematic with heavy analytical queries run during peak operational hours.
5.  **Spikes in Application Traffic:** Sudden, unexpected bursts of user activity or background jobs (e.g., batch processing, report generation) can temporarily drive up the demand for database connections beyond the server's capacity.
6.  **Idle but Active Connections:** Connections that are "idle in transaction" (e.g., waiting for user input within a transaction) or simply idle but not explicitly closed can still hold a connection slot, preventing new connections. While `idle` connections are usually fine, `idle in transaction` can be a problem.
7.  **External Monitoring Tools:** Sometimes, aggressive monitoring tools or health checks that open and close connections frequently can contribute, especially if they are not correctly configured.

## Step-by-Step Fix

Addressing this `FATAL` error requires a combination of immediate relief (if possible) and long-term configuration changes. Always proceed with caution, especially when modifying production systems.

### Step 1: Immediate Diagnosis (If Superuser Access is Possible)

If you can still connect as a superuser (e.g., `postgres` user) to the database, even briefly, you can gather crucial information. Sometimes, the reserved slots are still functional, allowing you to peek in.

1.  **Check Current Connections:**
    ```sql
    SELECT pid, usename, application_name, client_addr, backend_start, state, query_start, state_change, wait_event_type, wait_event
    FROM pg_stat_activity
    WHERE state IS NOT NULL AND pid <> pg_backend_pid()
    ORDER BY backend_start;
    ```
    Look for a high number of active or idle connections, especially from specific `application_name` or `client_addr`. This query helps identify connection leaks or problematic applications.

2.  **Check `max_connections`:**
    ```sql
    SHOW max_connections;
    ```
    Note down the current configured limit.

3.  **Check PostgreSQL Logs:**
    The PostgreSQL server logs (typically found in `/var/log/postgresql/` or your data directory's `log` subdirectory) will contain numerous entries related to connections being refused due to `max_connections`. Look for timestamped entries around the time the issue started. This can also reveal which applications are trying to connect.

### Step 2: Emergency Connection Termination (Use with Extreme Caution!)

If you can connect as a superuser and identify specific idle or problematic connections that are not critical, you can terminate them to free up slots. This is a temporary measure to gain access and should *not* be a regular solution.

```sql
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'problem_user' AND state = 'idle';
```
Replace `'problem_user'` with the actual username identified in `pg_stat_activity`. Be extremely careful, terminating active connections can lead to data inconsistencies or application failures. Only terminate `idle` connections if you're sure.

### Step 3: Increase `max_connections` (Primary Fix)

This is often the most direct way to resolve the issue, but it comes with a caveat: increasing `max_connections` consumes more RAM. Each connection requires a certain amount of shared buffer, work memory, and other resources.

1.  **Locate `postgresql.conf`:**
    The configuration file is typically found in your PostgreSQL data directory (e.g., `/etc/postgresql/14/main/postgresql.conf` on Debian/Ubuntu, or `/var/lib/pgsql/data/postgresql.conf` on CentOS/RHEL). You can find its location by connecting to PostgreSQL and running `SHOW config_file;`.

2.  **Edit `postgresql.conf`:**
    Open the file with a text editor (e.g., `sudo nano /etc/postgresql/14/main/postgresql.conf`).
    Find the line `max_connections = 100` (or whatever value is set).
    Increase this value. A common starting point might be 200, 300, or even more, depending on your server's resources and application demand. A general rule of thumb is to allow for your application's max pool size *plus* some overhead for admin tools, but not so much that you exhaust system RAM.

    ```ini
    # postgresql.conf snippet
    max_connections = 200 # increased from 100
    ```

    *Self-Correction:* Remember to also review `shared_buffers`, `work_mem`, and `maintenance_work_mem` when significantly increasing `max_connections`, as these parameters directly impact memory usage per connection.

3.  **Restart PostgreSQL:**
    Changes to `max_connections` require a full database restart to take effect.
    On `systemd`-based systems (most modern Linux distributions):
    ```bash
    sudo systemctl restart postgresql
    # Or for a specific version:
    sudo systemctl restart postgresql@14-main
    ```
    On macOS with Homebrew:
    ```bash
    brew services restart postgresql
    ```
    For `pg_ctl`:
    ```bash
    pg_ctl restart -D /path/to/your/data/directory
    ```
    After the restart, verify the new `max_connections` value using `SHOW max_connections;`.

### Step 4: Implement or Tune Connection Pooling

This is a critical long-term solution.

1.  **Application-Side Pooling:** Most modern application frameworks (e.g., Spring Boot with HikariCP, Node.js with `pg` module and `node-postgres-pool`, Python with `psycopg2` and `conn_pool`) have built-in connection pooling. Ensure it's enabled and configured correctly.
    *   Set a reasonable `max_pool_size` for your application instances. The sum of all application pool sizes should ideally not exceed `max_connections`.
2.  **External Connection Poolers:** For more complex environments or multiple applications connecting to the same database, consider using an external connection pooler like PgBouncer or Pgpool-II. These tools sit between your applications and PostgreSQL, multiplexing connections and presenting a much smaller, stable number of connections to the database, significantly reducing the load.

### Step 5: Optimize Application Code and Queries

Review application code for connection leaks. Profile queries to identify long-running ones and optimize them using better indexes, query rewrites, or by scheduling them during off-peak hours.

## Code Examples

Here are some concise, copy-paste ready code examples for diagnosis and modification:

1.  **Check current `max_connections`:**
    ```sql
    SHOW max_connections;
    ```

2.  **List all active and idle connections (excluding your own session):**
    ```sql
    SELECT pid, usename, application_name, client_addr, backend_start, state, query_start, state_change, wait_event_type, wait_event
    FROM pg_stat_activity
    WHERE state IS NOT NULL AND pid <> pg_backend_pid()
    ORDER BY backend_start;
    ```

3.  **Terminate a specific backend process (replace `<PID>` with the actual process ID):**
    ```sql
    SELECT pg_terminate_backend(12345);
    ```
    *(Always verify the PID first and ensure it's not a critical process.)*

4.  **Example `postgresql.conf` modification (increase `max_connections`):**
    ```ini
    #------------------------------------------------------------------------------
    # CONNECTIONS AND AUTHENTICATION
    #------------------------------------------------------------------------------

    # - Connection Settings -

    listen_addresses = '*'          # what IP address(es) to listen on;
                                    # comma-separated list of addresses;
                                    # defaults to 'localhost'; use '*' for all
                                    # (change requires restart)
    port = 5432                     # (change requires restart)
    max_connections = 250           # (change requires restart)
                                    # (normally 100 or less; too high may cause memory
                                    # exhaustion problems)
    ```

5.  **Restart PostgreSQL service on Linux (using `systemd`):**
    ```bash
    sudo systemctl restart postgresql
    ```
    or for a specific version:
    ```bash
    sudo systemctl restart postgresql@15-main
    ```

## Environment-Specific Notes

The approach to managing `max_connections` can vary significantly based on your deployment environment.

### Cloud Providers (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL)

*   **Configuration:** You cannot directly edit `postgresql.conf` on these managed services. Instead, you modify `max_connections` via their respective console, CLI, or API.
    *   **AWS RDS:** Use "Parameter Groups." You'll likely need to create a custom parameter group, modify `max_connections` there, and then apply it to your DB instance.
    *   **GCP Cloud SQL:** Edit the instance configuration, specifically the "Database flags" or "Parameters."
    *   **Azure Database for PostgreSQL:** Use the "Server parameters" blade in the Azure portal.
*   **Restart:** Applying parameter group changes or database flags often requires a scheduled maintenance window or an immediate database restart via the cloud provider's console.
*   **Scaling:** Cloud environments often automatically scale `max_connections` based on instance size (e.g., more RAM usually means a higher default `max_connections`). If you hit this limit frequently, consider scaling up your database instance (e.g., to a larger instance type with more RAM and CPU).

### Docker / Containerized Environments

*   **Configuration:**
    *   **Environment Variables:** For simple Docker setups, you can often pass `max_connections` as an environment variable to the PostgreSQL container, especially if using an official image. For example, in `docker-compose.yml`:
        ```yaml
        services:
          db:
            image: postgres:15
            environment:
              POSTGRES_DB: mydb
              POSTGRES_USER: user
              POSTGRES_PASSWORD: password
              PGDATA: /var/lib/postgresql/data/pgdata
              # Set max_connections via command or entrypoint script
              POSTGRES_INITDB_ARGS: "--max-connections=200" # Not directly for max_connections, but for other init flags
            command: ["postgres", "-c", "max_connections=250"] # This is how I usually set it
        ```
    *   **Custom `postgresql.conf`:** For more control, mount a custom `postgresql.conf` file into the container at `/etc/postgresql/postgresql.conf` or `/var/lib/postgresql/data/postgresql.conf`.
*   **Restart:** A simple `docker restart <container_id>` or `docker-compose restart db` will apply the changes.
*   **Orchestration:** In Kubernetes, `max_connections` would typically be managed via a ConfigMap that's mounted as a volume, or set through environment variables specified in the Deployment manifest.

### Local Development Environment

*   **Configuration:** You'll typically be directly editing the `postgresql.conf` file as described in Step 3.
*   **Restart:** Use your local system's service manager (`brew services restart postgresql` on macOS, `sudo systemctl restart postgresql` on Linux, or `pg_ctl` directly).
*   **Troubleshooting:** Local environments are great for quickly reproducing and testing changes without affecting production, but they often have fewer resources. Keep `max_connections` reasonable.

## Frequently Asked Questions

**Q: Can I increase `max_connections` indefinitely to solve this problem?**
**A:** No, increasing `max_connections` too much can lead to severe performance degradation and even instability. Each connection consumes system resources (primarily RAM, but also CPU and file descriptors). If you set it too high, your server might run out of memory and crash, or become extremely slow due to excessive context switching and memory swapping. Always balance the `max_connections` setting with your server's available RAM and CPU.

**Q: What's a good value for `max_connections`?**
**A:** There's no one-size-fits-all answer. It highly depends on your server's hardware, workload, and whether you're using connection pooling. For a dedicated database server, values between 100-500 are common. If you use a robust external connection pooler like PgBouncer, you might keep `max_connections` on the PostgreSQL server relatively low (e.g., 50-100) as PgBouncer will manage the high volume of client connections. Monitor your system's memory and CPU usage after increasing the value.

**Q: How do connection pools help prevent this error?**
**A:** Connection pools are crucial. Instead of each application request opening and closing a new database connection, the pool maintains a fixed set of open connections. When the application needs a connection, it "borrows" one from the pool. When done, it "returns" it. This significantly reduces the overhead of connection establishment and, more importantly, limits the maximum number of concurrent connections from the application to the database to the pool's configured size, effectively preventing connection storms that could exhaust `max_connections`.

**Q: Why does PostgreSQL reserve connection slots for superusers?**
**A:** This is a vital fail-safe mechanism. Even when your database is completely overwhelmed by regular connections, the reserved superuser slots (controlled by the `superuser_reserved_connections` parameter, default usually 2-4) allow an administrator to connect using a superuser role (like `postgres`). This access enables them to diagnose the problem, terminate problematic connections, or make configuration changes to bring the database back to a healthy state, without needing to fully restart the server immediately. The `FATAL` error means even these slots are now effectively unavailable.

**Q: Does using an external connection pooler like PgBouncer or Pgpool-II solve this problem permanently?**
**A:** External connection poolers are an excellent solution for managing and multiplexing connections, and they can significantly mitigate the `max_connections` issue. By sitting in front of PostgreSQL, they accept many client connections but maintain only a smaller, fixed number of connections to the actual database server. This offloads connection management from PostgreSQL and reduces its resource consumption. However, they don't solve underlying issues like poorly optimized queries or genuine resource bottlenecks if your `max_connections` is already very high and the server is struggling. They are a powerful tool, not a magic bullet.

## Related Errors
*() *