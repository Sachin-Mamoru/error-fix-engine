# MySQL ERROR 1049: Unknown database 'X'
> Encountering MySQL ERROR 1049: Unknown database 'X' means the specified database doesn't exist; this guide explains how to identify and resolve this common connection error.

## What This Error Means

MySQL ERROR 1049, "Unknown database 'X'", is a clear and direct message indicating that the MySQL server you are connected to cannot find a database with the name 'X' that your client or application is trying to access. It's not a server crash, nor is it typically a permission problem (though that can follow if you fix this and try to access a database you aren't authorized for). Essentially, you're asking the MySQL server for something it doesn't have on its list of available databases.

This error can manifest in various scenarios:
*   During an attempt to connect your application to the database.
*   When executing a `USE database_name;` command in the MySQL client.
*   When running a script that explicitly references a database.

The 'X' in the error message will be replaced by the specific database name that MySQL couldn't find. It's crucial to pay close attention to this name, as subtle differences often cause the issue.

## Why It Happens

The fundamental reason for `ERROR 1049` is a mismatch. The database name provided by the client (your application, a SQL script, or manual command) does not correspond to an actual, existing database on the MySQL server instance it's trying to connect to. This isn't about credentials or privileges yet; it's a pre-authentication check that fails because the target resource (the database) simply isn't there.

In my experience, this error points to a configuration or deployment oversight rather than an issue with the MySQL server itself. The server is working as intended; it's simply reporting that the requested database isn't available.

## Common Causes

Identifying the root cause of `ERROR 1049` often comes down to a few typical culprits:

1.  **Typo or Spelling Error:** This is by far the most frequent cause. A simple mistake like `mydatabas` instead of `mydatabase`, or `staging_db` instead of `production_db` can trigger this error. I've spent too much time debugging this only to find a single missing letter.
2.  **Case Sensitivity Mismatch:** MySQL database names are case-sensitive on Unix-like operating systems (Linux, macOS) by default, but case-insensitive on Windows. If your database is named `MyDatabase` on a Linux server, but your application tries to connect to `mydatabase`, you will get `ERROR 1049`. This is a common pitfall when moving projects between different OS environments.
3.  **Database Not Created:** In new setups, CI/CD pipelines, or fresh local development environments, it's easy to forget the step of actually creating the database. The application configuration points to a database name, but the `CREATE DATABASE` command was never executed.
4.  **Connecting to the Wrong MySQL Server/Instance:** Your application might be configured to connect to `localhost`, but your intended database lives on a remote server, or vice-versa. Alternatively, if you have multiple MySQL instances running (e.g., one from Docker, one natively installed), your application might be connecting to the wrong one. I've seen this in production when an environment variable pointed to a defunct database server.
5.  **Database Dropped Unexpectedly:** While less common, a database could have been accidentally dropped by a script, a manual command, or an automated cleanup process.
6.  **Incorrect `USE` Statement:** If you're manually working in the MySQL client or running a script, an incorrect `USE database_name;` statement will produce this error for subsequent queries if the specified database doesn't exist.

## Step-by-Step Fix

Here’s a methodical approach to troubleshoot and resolve `MySQL ERROR 1049`:

### Step 1: Verify the Database Name

Start by confirming the exact database name your application or client is attempting to use.

*   **Application Configuration:** Check your application's database configuration file (e.g., `config.php`, `database.yml`, `.env` file, `application.properties`). Locate the database name parameter.
*   **SQL Scripts/Commands:** If running a SQL script or a direct `mysql` command, inspect the `USE` statement or the database parameter in the connection string.
*   **Remember the Case:** Make a note of the exact spelling and capitalization.

### Step 2: List Existing Databases on the Server

Connect to your MySQL server *without* specifying the problematic database. You can usually do this by connecting to a default database like `mysql` or `information_schema`, or simply omitting the database name in the connection command if your user has global privileges.

```bash
mysql -u your_user -p
```

Once connected, run the following command to see all databases accessible by your user:

```sql
SHOW DATABASES;
```

**What to look for:**
*   Does your intended database name appear in the list?
*   If it appears, does the spelling and, critically, the **case** exactly match what you noted in Step 1?

If you see `MyDatabase` but your application uses `mydatabase` (and you're on a case-sensitive OS like Linux), this is very likely your problem.

### Step 3: Check Server Connectivity and Identity

Ensure you are connected to the intended MySQL server instance. This is especially relevant in environments with multiple databases or instances.

In your MySQL client, after connecting (potentially to a different database like `mysql` to avoid `1049`):

```sql
SELECT @@hostname, @@port;
```

This will show you the hostname and port of the MySQL server you are currently connected to. Compare this with the hostname/port configured in your application. Mismatched hostnames often mean you're talking to the wrong database server altogether.

### Step 4: Create the Database (If Missing)

If `SHOW DATABASES;` from Step 2 confirmed that your database is genuinely missing from the server, you need to create it.

```sql
CREATE DATABASE your_database_name;
```

Replace `your_database_name` with the exact, intended name (paying attention to case). Ensure the user you're logged in with has `CREATE` privileges. After creating, you can try to `USE` it or reconnect your application.

### Step 5: Update Application Configuration

Once you've identified the correct database name (either by finding an existing one or creating a new one), update your application's configuration to use the correct name.

For example, if your application configuration looks like this:

```php
// config.php example
$config['database'] = [
    'host' => 'localhost',
    'name' => 'non_existent_db', // This was causing the error
    'user' => 'your_user',
    'password' => 'your_password'
];
```

Change it to:

```php
// config.php example - Fix applied
$config['database'] = [
    'host' => 'localhost',
    'name' => 'your_correct_database_name', // Corrected name
    'user' => 'your_user',
    'password' => 'your_password'
];
```

After updating, restart your application to ensure it loads the new configuration.

### Step 6: Address Case Sensitivity (If Applicable)

If the database exists but with different casing (e.g., `MyDatabase` vs `mydatabase`), and you're on a case-sensitive file system (Linux/macOS):
*   **Option A (Recommended):** Update your application's configuration to exactly match the case of the database name as shown by `SHOW DATABASES;`.
*   **Option B (Advanced/Cautionary):** If you absolutely need case-insensitive database names on Linux, you can configure `lower_case_table_names=1` in your MySQL server's `my.cnf` or `my.ini` file. **WARNING:** This requires a server restart and can have implications for existing databases if they rely on case sensitivity for table names. It's generally better to just fix the application's configuration.

## Code Examples

Here are some concise, copy-paste ready code examples illustrating the error and its fix.

### Python Example with `mysql.connector`

**Incorrect (will produce ERROR 1049):**

```python
import mysql.connector

try:
    # 'non_existent_db' does not exist on the MySQL server
    cnx = mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysecretpassword",
        database="non_existent_db"
    )
    print("Connected successfully!")
except mysql.connector.Error as err:
    print(f"Error connecting to database: {err}")
finally:
    if 'cnx' in locals() and cnx.is_connected():
        cnx.close()
```

**Corrected (assuming 'my_application_db' exists):**

```python
import mysql.connector

try:
    # 'my_application_db' is a verified, existing database
    cnx = mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysecretpassword",
        database="my_application_db"
    )
    print("Connected successfully to my_application_db!")
    # Example query
    cursor = cnx.cursor()
    cursor.execute("SELECT VERSION();")
    result = cursor.fetchone()
    print(f"MySQL Version: {result[0]}")
    cursor.close()
except mysql.connector.Error as err:
    print(f"Error connecting to database: {err}")
finally:
    if 'cnx' in locals() and cnx.is_connected():
        cnx.close()
```

### SQL Commands to Create and Verify

```sql
-- Step 1: Connect to MySQL server (e.g., as root or a user with CREATE privileges)
-- mysql -u root -p

-- Step 2: Show existing databases to verify if yours is missing or misspelled
SHOW DATABASES;
-- Expected output might look like:
-- +--------------------+
-- | Database           |
-- +--------------------+
-- | information_schema |
-- | mysql              |
-- | performance_schema |
-- | sys                |
-- +--------------------+

-- Step 3: If 'my_application_db' is not listed, create it
CREATE DATABASE my_application_db;

-- Step 4: Verify creation
SHOW DATABASES;
-- Expected output now includes:
-- | my_application_db  |

-- Step 5: Now you can connect to and use the database
USE my_application_db;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO users (username) VALUES ('TakeshiMori');
SELECT * FROM users;
```

## Environment-Specific Notes

The context in which you encounter `ERROR 1049` can sometimes point to its cause more quickly.

### Local Development

*   **Fresh Clones:** Often occurs after cloning a new project and forgetting to run `db:create` or equivalent setup scripts.
*   **Multiple Instances:** I've run into this when switching between a database installed via Homebrew (macOS) and one spun up by MAMP/XAMPP, or even a Dockerized instance. Ensure your application's `localhost` or `127.0.0.1` refers to the MySQL instance you intend.
*   **Env File Issues:** Local `.env` files might be missing or incorrectly configured, pointing to a placeholder database name.

### Docker/Containerized Environments

*   **Service Initialization:** A common scenario is the database container starting, but the `initdb.d` scripts (which create initial databases and users) failing or not completing before the application container tries to connect. Check `docker logs` for your database container.
*   **Environment Variables:** Misconfigured `MYSQL_DATABASE` or similar environment variables in your `docker-compose.yml` or Kubernetes manifest. Double-check these values against what your application expects.
*   **Networking:** While less likely to be `1049` (often manifests as connection refused/timeout), incorrect service names in `docker-compose.yml` could lead to connecting to a non-existent host, which could indirectly cause this if a connection is established to an empty server.

### Cloud (AWS RDS, Azure Database, Google Cloud SQL)

*   **Instance State:** First, ensure the cloud database instance itself is running and healthy. A stopped or unhealthy instance will usually give a connection error rather than `1049`, but it's a good first check.
*   **Actual Database Name:** Unlike local setups where you might create your own, cloud providers sometimes provision a default database with a specific name (e.g., `admin`, `default_db`). Verify the exact database name from your cloud console. I've often seen subtle differences here.
*   **Region Mismatch:** Less common, but it's possible for an application to attempt connecting to a database instance in the wrong cloud region, especially if hardcoded IP addresses or old DNS entries are involved. This would then present as a non-existent database if that instance doesn't have it.

## Frequently Asked Questions

**Q: Is this a permissions error?**
**A:** No, `ERROR 1049` specifically means "Unknown database" – the database simply does not exist on the server. Permission errors are typically `ERROR 1044` (Access denied for user to database 'X') or `ERROR 1045` (Access denied for user 'Y'@'Z' using password: YES). While you might get a permissions error *after* resolving 1049, the 1049 error itself is not about privileges.

**Q: I see the database when I `SHOW DATABASES;` but still get the error. Why?**
**A:** This is almost certainly a case sensitivity issue. On Unix-like systems, database names are case-sensitive. If `SHOW DATABASES;` displays `MyApplicationDb` but your connection string uses `myappdb` or `myapplicationdb`, you will get `ERROR 1049`. Ensure the casing in your application configuration exactly matches what `SHOW DATABASES;` reports.

**Q: Can a database be "hidden" from `SHOW DATABASES;`?**
**A:** No, not practically for this error. `SHOW DATABASES;` lists all databases for which the connecting user has *any* privileges. If a database isn't listed, it means it genuinely doesn't exist on that server, or your user has no access at all, rendering it effectively non-existent from your perspective.

**Q: What if the database was just created? Do I need to restart anything?**
**A:** No, database creation in MySQL is an immediate operation. You should be able to connect and use it right away. However, your *application* might cache connections or schema information. In such cases, restarting your application might be necessary for it to pick up the newly created database, but the MySQL server itself does not need a restart.

## Related Errors