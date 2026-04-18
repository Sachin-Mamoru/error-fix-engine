# MySQL ERROR 1049: Unknown database 'X'
> Encountering MySQL ERROR 1049 means the database you're trying to connect to or operate on doesn't exist on the server; this guide explains how to fix it.

As a software engineer, I've encountered `MySQL ERROR 1049: Unknown database 'X'` more times than I care to admit, both in local development and production environments. While seemingly straightforward, pinpointing the exact cause can sometimes involve digging through layers of configuration and environment variables. This error indicates that the MySQL server you're connected to cannot find a database with the specific name provided. It's not an authentication issue (like ERROR 1045) or a connectivity issue (like "Can't connect to MySQL server"), but rather a clear message from the server that the requested database simply isn't there.

## What This Error Means

When you see `MySQL ERROR 1049: Unknown database 'X'`, it means the MySQL server process you're connected to has been asked to perform an operation on a database named 'X', but it cannot find any database matching that name. The database 'X' might be specified in your application's connection string, a command-line argument, or a SQL `USE X;` statement.

Crucially, this error implies that the connection *to the MySQL server itself* was successful. The server is up and running, and your client was able to establish a connection. The problem arises *after* the connection is made, when the server attempts to locate or switch to the specified database. Think of it like trying to find a specific book in a library that you've successfully entered – you're in the right building, but the book you're asking for isn't on any of the shelves.

This error tells you one thing very clearly: MySQL doesn't know about a database with that exact name.

## Why It Happens

The fundamental reason for this error is a mismatch between the database name your client or application is requesting and the database names that actually exist on the MySQL server. This mismatch can stem from several underlying issues, some of which are surprisingly common in development workflows and even creep into production setups.

One common scenario is when the application expects a database to be present, perhaps after a fresh deployment or during local setup, but the `CREATE DATABASE` command was never executed. Another frequent culprit is a simple typo in the database name within configuration files or command-line arguments. In my experience, even a subtle difference in casing can trigger this error, especially on Linux-based MySQL servers where database names are typically case-sensitive.

Furthermore, environment misconfiguration, such as pointing to the wrong MySQL server instance or using an outdated configuration, can lead your application to request a database that exists on a *different* server but not on the one it's currently connected to.

## Common Causes

Here's a breakdown of the most common reasons you might encounter `MySQL ERROR 1049`:

1.  **Typo in the Database Name:** This is arguably the most frequent cause. A simple spelling mistake in your application's configuration file, environment variable, or command-line argument for the database name (`my_app_db` vs. `myapp_db`, for instance) will lead to this error.
2.  **Case Sensitivity Mismatch:** MySQL database names can be case-sensitive, depending on the operating system and the `lower_case_table_names` server variable. On Linux, database names are typically case-sensitive by default (`lower_case_table_names = 0`). If your database was created as `MyDatabase` but your application tries to connect to `mydatabase`, you'll get this error. Windows and macOS often default to case-insensitivity (`lower_case_table_names = 1` or `2`), which can hide this issue during local development, only for it to surface when deploying to a Linux-based production server.
3.  **Database Not Created:** You might have connected to a fresh MySQL server instance where the required database simply hasn't been created yet. This often happens in new development setups, CI/CD environments, or newly provisioned cloud database instances where the schema migration or initial database creation script wasn't run.
4.  **Connecting to the Wrong MySQL Server:** Your application might be configured to connect to `db-server-dev.example.com` but you've accidentally deployed it with configuration pointing to `db-server-prod.example.com`, or perhaps an old local MySQL instance. The database 'X' might exist on one server but not the other.
5.  **Application Configuration Error:** The environment variable (`DATABASE_URL`, `DB_NAME`), configuration file (e.g., `config/database.yml` in Rails, `settings.py` in Django), or ORM settings specifying the database name might be incorrect or missing for the current environment.
6.  **Database Accidentally Dropped:** Less common in production, but in shared development or staging environments, I've seen databases get dropped by another developer, an automated cleanup script, or during a botched data refresh operation.

## Step-by-Step Fix

Addressing `MySQL ERROR 1049` involves a systematic approach to verify your database name, server, and configuration.

### 1. Verify the Exact Database Name

The first and easiest step is to confirm the actual name of the database your application is trying to connect to, and compare it against the databases that truly exist on your MySQL server.

*   **Check your application's configuration:** Locate where your application specifies the database name. This could be in an environment variable (`DB_NAME`, `DATABASE_URL`), a configuration file (`.env`, `config.php`, `application.properties`, `settings.py`), or directly in code. Note down the *exact* string used for the database name.
*   **Connect to MySQL and list existing databases:**
    Open a MySQL client (e.g., `mysql` command-line client, MySQL Workbench, DBeaver) and connect to the *same* MySQL server instance that your application is trying to reach. Once connected, run the following command:

    ```sql
    SHOW DATABASES;
    ```

    This will list all databases accessible by your current user. Carefully compare the name you found in your application's configuration with the list returned by `SHOW DATABASES;`. Look for typos, extra spaces, or differences in casing.

    If your application tries to connect to `myapp_db` but `SHOW DATABASES;` lists `Myapp_DB`, you've found a likely culprit.

### 2. Address Case Sensitivity

If `SHOW DATABASES;` shows a database with a similar name but different casing, this is a critical step. MySQL's default behavior for database and table name case sensitivity varies by operating system:

*   **Linux:** Default `lower_case_table_names = 0` (case-sensitive).
*   **Windows/macOS:** Default `lower_case_table_names = 1` or `2` (case-insensitive for tables, sometimes also databases depending on the specific setting).

You can check the current setting on your MySQL server:

```sql
SHOW VARIABLES LIKE 'lower_case_table_names';
```

If `lower_case_table_names` is `0`, then `my_database` and `My_Database` are treated as entirely separate databases. To fix this:
*   **Option A (Recommended):** Adjust your application's configuration to use the *exact* casing of the existing database name.
*   **Option B:** If the database doesn't contain critical data and you prefer a different casing, drop and recreate it with the desired case. Be cautious with this in production.
*   **Option C (Advanced, not usually recommended):** Modify the `lower_case_table_names` setting in your `my.cnf` or `my.ini` configuration file. This requires a MySQL server restart and affects *all* databases and tables. It's usually better to match the application to the server's existing configuration.

### 3. Create the Database if it Doesn't Exist

If `SHOW DATABASES;` did not list your required database at all, then it simply doesn't exist. You'll need to create it.

1.  **Connect to MySQL** (as a user with `CREATE` privileges, typically `root` for initial setup).
2.  **Execute the `CREATE DATABASE` command:**

    ```sql
    CREATE DATABASE your_database_name;
    ```
    Replace `your_database_name` with the exact name your application expects (paying attention to casing).

3.  **Grant Permissions (if necessary):** If the user your application connects with doesn't have permissions to access this new database, you might later encounter `ERROR 1045: Access denied`. It's good practice to grant specific permissions:

    ```sql
    GRANT ALL PRIVILEGES ON your_database_name.* TO 'your_user'@'localhost';
    FLUSH PRIVILEGES;
    ```
    Adjust `your_user` and `localhost` as appropriate for your setup.

### 4. Confirm You're Connecting to the Correct MySQL Server

It's a classic "Are you sure you're looking at the right server?" problem. This is especially relevant when working with multiple environments (dev, staging, prod) or local setups with several MySQL instances (e.g., Docker, Homebrew, official installer).

*   **Check connection details:** Verify the hostname, IP address, and port number in your application's configuration.
*   **Test connectivity independently:** Try connecting to the specified host and port using the `mysql` client directly:

    ```bash
    mysql -h <hostname_or_ip> -P <port> -u <username> -p
    ```
    If this connects successfully, then run `SHOW DATABASES;` on *that specific server* to see what databases are available there. This helps confirm you're indeed connected to the intended server and ruling out an accidental connection to a different instance.

### 5. Review Application-Specific Configuration

Sometimes the database name is derived or overridden by specific framework settings.

*   **Environment Variables:** Double-check your `.env` file or environment variable declarations, especially in containerized environments (Docker Compose, Kubernetes).
*   **ORM/Framework Settings:** If using an ORM like Sequelize, SQLAlchemy, or ActiveRecord, verify its specific database configuration. For instance, in a Python Django project, you'd check `DATABASES` in `settings.py`. For Node.js applications, check the database connection options you pass to your client library.

    ```bash
    # Example .env file content
    DB_CONNECTION=mysql
    DB_HOST=127.0.0.1
    DB_PORT=3306
    DB_DATABASE=my_app_database # <--- Verify this name
    DB_USERNAME=my_user
    DB_PASSWORD=my_password
    ```

### 6. Consider Accidental Deletion (Shared Environments)

In rare cases, particularly on shared test or staging servers, a database might have been accidentally dropped by another user or an automated script. If everything else checks out, and you're certain the database *was* there, check server logs or consult with colleagues. Restoring from a backup or re-running database creation scripts would be the fix here. I've seen this happen in internal test environments where cleanup scripts were too aggressive.

## Code Examples

Here are some concise, copy-paste ready code examples to help troubleshoot and fix the error.

### Listing Databases on the Server

To verify what databases exist on your connected MySQL server:

```sql
SHOW DATABASES;
```

### Creating a Database

If the database is missing, create it using a user with sufficient privileges (e.g., `root`):

```sql
CREATE DATABASE my_new_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Granting User Permissions to a New Database

After creating a database, ensure your application's user has access:

```sql
GRANT ALL PRIVILEGES ON my_new_app_db.* TO 'app_user'@'localhost' IDENTIFIED BY 'your_password';
FLUSH PRIVILEGES;
```
*Note: `IDENTIFIED BY` is deprecated in newer MySQL versions; use `ALTER USER` for setting/changing passwords.*

```sql
-- For MySQL 8.0+
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON my_new_app_db.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

### Example Application Configuration (Python/Django)

Incorrect database name in `settings.py`:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'my_app_dbb',  # Typo here, should be 'my_app_db'
        'USER': 'app_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```
This will result in `MySQL ERROR 1049: Unknown database 'my_app_dbb'`. The fix is to correct `NAME` to `'my_app_db'`.

### Testing Connection from Shell with Specific Database

To test if a database exists from the command line:

```bash
# Correct connection attempt
mysql -h localhost -P 3306 -u root -p my_app_db

# Incorrect connection attempt (will yield ERROR 1049)
mysql -h localhost -P 3306 -u root -p non_existent_db
```
The last command would produce the error.

## Environment-Specific Notes

The context in which you encounter `MySQL ERROR 1049` often influences the specific troubleshooting steps.

### Local Development

This is where I find myself fixing `ERROR 1049` most often.
*   **Forgotten `CREATE DATABASE`:** It's easy to clone a project, install dependencies, but forget the `CREATE DATABASE` step or running initial migrations for a fresh local database.
*   **Multiple MySQL Instances:** Developers often have multiple MySQL installations (e.g., a Homebrew installation on macOS, a Docker container, or an `apt` package on Linux). Ensure your application is pointing to the correct instance and port. Sometimes, `localhost` might resolve to a different MySQL server than expected.
*   **Case Sensitivity:** Testing on a macOS or Windows machine (where `lower_case_table_names` often defaults to `1` or `2`) might not expose case sensitivity issues that will later appear on a Linux-based staging or production server. Always verify the casing of your database names.

### Docker and Docker Compose

When working with Docker, this error often points to issues with service initialization or environment variable configuration within your `docker-compose.yml` or Dockerfile.
*   **`MYSQL_DATABASE` Environment Variable:** For official MySQL Docker images, the `MYSQL_DATABASE` environment variable is crucial. If set, Docker will automatically create this database when the container starts for the first time. If it's missing, misspelled, or your application uses a different name, you'll hit `ERROR 1049`.
    ```yaml
    # docker-compose.yml example
    services:
      db:
        image: mysql:8.0
        environment:
          MYSQL_ROOT_PASSWORD: root_password
          MYSQL_DATABASE: my_docker_app_db # This must match your app's config
        volumes:
          - db_data:/var/lib/mysql
    ```
*   **Service Startup Order:** Ensure your application container doesn't try to connect to the database *before* the MySQL container has fully initialized and created the database. `depends_on` in `docker-compose.yml` helps with startup order but doesn't guarantee the database is ready. Health checks or retry logic in your application are more robust.

### Cloud Environments (AWS RDS, Google Cloud SQL, Azure Database for MySQL)

Cloud database services abstract away much of the infrastructure, but they still require explicit database creation.
*   **Initial Database Creation:** When provisioning an instance (e.g., AWS RDS), there's often an option to specify an "Initial Database Name". If you leave this blank, or if your application expects a *different* database, you'll get `ERROR 1049`. You then need to connect to the cloud instance (via a jump box, SSH tunnel, or direct connection if security groups allow) and manually create the database using `CREATE DATABASE`.
*   **Instance vs. Database:** Remember that creating an RDS *instance* doesn't automatically mean your specific application database exists within it. It's just a server. I've seen this in production when a new RDS instance was provisioned, but the "initial database" field was left blank, and the schema migration wasn't run immediately, leading to application downtime.
*   **Connectivity vs. Database Existence:** Ensure your security groups, network ACLs, and firewalls allow connection to the cloud database instance *first*. If you can't connect at all, you'd get a different error (like a connection refused). `ERROR 1049` implies you successfully connected to the instance but the database is missing.

## Frequently Asked Questions

**Q: Is `MySQL ERROR 1049` related to `Access denied for user...` (ERROR 1045)?**
**A:** No, they are distinct errors. `ERROR 1049` means the database you're asking for *does not exist* on the server you connected to. `ERROR 1045` means the database *does exist*, but the user attempting to connect either provided incorrect credentials or does not have sufficient privileges to access that database. You can think of 1049 as a "Not Found" error for the database, and 1045 as an "Unauthorized" error.

**Q: What if I'm absolutely sure the database exists?**
**A:** If you're certain the database exists, double-check these two things meticulously:
1.  **Exact Name:** Verify the *exact* spelling and casing of the database name in your application's configuration against what `SHOW DATABASES;` returns. Case sensitivity (especially on Linux) is a common trap.
2.  **Correct Server:** Confirm you are connecting to the *intended* MySQL server instance. It's common to accidentally point to a development server when expecting production, or a different local instance. Use `mysql -h <host> -P <port> -u <user> -p` to verify the connection and `SHOW DATABASES;` on that specific server.

**Q: Can `lower_case_table_names` cause this error?**
**A:** Absolutely. If your MySQL server is configured with `lower_case_table_names = 0` (typically on Linux, meaning database names are case-sensitive) and you created a database named `MyApplicationDB`, but your application tries to connect to `myapplicationdb`, you will get `ERROR 1049` because the server sees them as two distinct, non-matching names.

**Q: How can I prevent `ERROR 1049` in CI/CD pipelines?**
**A:** In CI/CD, ensure your database setup script (e.g., `CREATE DATABASE` commands or ORM migrations) runs *before* your application attempts to connect. Use consistent environment variables for database names across all environments. For Dockerized CI, ensure `MYSQL_DATABASE` is correctly set and that there's proper coordination between your DB service and application service startup. Implementing health checks for your database service can also prevent your application from trying to connect prematurely.

## Related Errors

*   [mysql-1045](/errors/mysql-1045.html)
*   [postgresql-connection-refused](/errors/postgresql-connection-refused.html)