# MongoDB MongoServerError: Authentication failed
> Encountering MongoDB MongoServerError: Authentication failed means your application cannot connect to MongoDB due to incorrect credentials or insufficient user permissions; this guide explains how to fix it.

## What This Error Means

When your application throws a `MongoDB MongoServerError: Authentication failed`, it's a clear signal from your MongoDB instance that it has explicitly denied access. This isn't a network connectivity problem (like a timeout or connection refused), nor is it typically an issue with the MongoDB server itself being down. Instead, it means the server received your connection attempt, understood it, but rejected it because the credentials provided (username, password) were incorrect, or the user specified does not have the necessary permissions to access the target database.

In my experience, this error points directly to a security misconfiguration rather than an operational one. MongoDB is telling you, "I know who you are trying to be, but you don't have the key." It's a critical error because it prevents any further interaction between your client application and the database until resolved.

## Why It Happens

Authentication in MongoDB is a multi-layered process designed to ensure that only authorized users can interact with your data. The `MongoServerError: Authentication failed` error occurs when any part of this process goes awry. Fundamentally, it's a mismatch between what your client application is providing and what the MongoDB server expects or allows.

Commonly, this happens because:
*   The username or password supplied by your client doesn't match what's stored on the MongoDB server. This could be due to a typo, an outdated password, or simply pointing to the wrong user.
*   The user attempting to connect either does not exist in the database where authentication is being attempted, or it lacks the required roles and privileges to perform the operations your application intends to execute on the specified database.
*   The `authSource` parameter in your connection string is incorrect, meaning MongoDB is looking for the user on a different database than where it was actually defined.
*   The authentication mechanism (e.g., SCRAM-SHA-256) specified by the client doesn't match what the server is configured to use, or what the user was created with.

I've seen this in production when a developer refreshes a credentials file but forgets to restart the service, or when moving between development and production environments where credentials significantly differ.

## Common Causes

Let's break down the most frequent culprits behind this persistent error:

1.  **Incorrect Username or Password:** This is, by far, the most common reason. A simple typo, using an outdated password after a rotation, or confusing credentials between different environments (dev, staging, prod) can all lead to this. Always double-check.
2.  **User Does Not Exist:** The user specified in your connection string might not have been created on the MongoDB server at all, or it might have been deleted.
3.  **Incorrect `authSource`:** MongoDB users are created in the context of a specific database (e.g., `admin`, `myAppDb`). The `authSource` parameter in your connection string tells MongoDB *which* database to look for the user's credentials. If your user `myUser` was created on `myAppDb` but your connection string doesn't specify `authSource=myAppDb` (defaulting to `admin`), authentication will fail because MongoDB is looking for `myUser` in the wrong place.
4.  **Insufficient User Permissions (Roles):** Even if the username and password are correct and the user exists, they might not have the necessary roles to access the specific database or perform the operations your application requires. For instance, a user with `read` access on `myAppDb` will fail if your application tries to write data to that database.
5.  **Authentication Mechanism Mismatch:** MongoDB supports several authentication mechanisms (e.g., SCRAM-SHA-1, SCRAM-SHA-256, X.509). If your client application attempts to authenticate using a mechanism that the server doesn't support or that the user wasn't configured for, it will fail. Modern MongoDB versions default to SCRAM-SHA-256, but older clients or specific configurations might require `authMechanism` to be explicitly set.
6.  **Environment Variable Issues:** If you're loading your MongoDB credentials from environment variables (a common and recommended practice), there might be an issue with how these variables are being loaded or accessed by your application. This could be anything from a malformed variable name to a process not having access to the correct environment.
7.  **Firewall or Security Group Misconfigurations (Edge Case):** While usually leading to connection timeouts or refusals, I have, on rare occasions, encountered scenarios where a very restrictive firewall or security group might interfere with specific authentication packets, leading to an authentication failure rather than a complete connection block. This is less common but worth a quick check if all other credential-related issues have been ruled out.

## Step-by-Step Fix

Let's systematically troubleshoot and resolve `MongoDB MongoServerError: Authentication failed`.

### 1. Verify Credentials and Connection String

This is the very first thing to check.
*   **Double-check Username and Password:** Ensure the exact username and password are being used. Pay attention to case sensitivity, special characters, and leading/trailing spaces.
*   **Review the Connection String:** Look for typos. A typical connection string looks like this:
    ```
    mongodb://<username>:<password>@<host>:<port>/<database>?authSource=<authSourceDb>&ssl=true
    ```
    Confirm that `<username>`, `<password>`, and `<host>` are correct.

### 2. Confirm `authSource` Parameter

The `authSource` parameter is critical. It tells MongoDB which database holds the user's credentials. If omitted, it defaults to `admin`.
*   **Determine User's Authentication Database:** You need to know which database the user was originally created on. For users created via Atlas or with `db.createUser()`, it's usually the database you were `use`'d into when running the command, or `admin`.
*   **Update Connection String:** Set `authSource` to the correct database.
    *   Example: If `myAppUser` was created on `myAppDb`:
        ```
        mongodb://myAppUser:myPassword@localhost:27017/myAppDb?authSource=myAppDb
        ```
    *   If `myAppUser` was created on `admin` but needs access to `myAppDb`:
        ```
        mongodb://myAppUser:myPassword@localhost:27017/myAppDb?authSource=admin
        ```

### 3. Verify User Existence and Roles on MongoDB

Connect to your MongoDB instance with a privileged user (e.g., an `admin` user) and inspect the user configuration.

1.  **Connect to MongoDB Shell:**
    ```bash
    mongosh -u adminUser -p adminPassword --authenticationDatabase admin
    ```
    Replace `adminUser` and `adminPassword` with your administrative credentials.

2.  **List Users and Roles:**
    To see all users and their associated roles across different databases, you can use:
    ```javascript
    use admin
    db.getUsers({ showPrivileges: true }) // Requires MongoDB 4.0+ for showPrivileges
    ```
    If you know the specific user, you can check their details:
    ```javascript
    use myAppDb // Or the database where the user is *expected* to be defined
    db.getUser('myAppUser')
    ```
    Look for:
    *   Does `myAppUser` exist?
    *   Is the user defined on the correct database (`myAppDb` in this example)?
    *   Does the `roles` array contain the necessary permissions (e.g., `readWrite` on `myAppDb`)?

### 4. Grant or Modify User Roles (If Necessary)

If the user exists but lacks the required permissions for the database or specific operations, you'll need to grant them.

1.  **Connect with a Privileged User:**
    ```bash
    mongosh -u adminUser -p adminPassword --authenticationDatabase admin
    ```

2.  **Grant Roles:**
    To grant `readWrite` access on `myAppDb` to `myAppUser`:
    ```javascript
    use admin // User roles are often managed from the admin database
    db.grantRolesToUser(
        "myAppUser",
        [
            { role: "readWrite", db: "myAppDb" }
        ]
    )
    ```
    Other common roles include `read`, `dbAdmin`, `clusterMonitor`. Refer to MongoDB documentation for a complete list.

### 5. Check Authentication Mechanism

While often handled automatically by modern drivers, an explicit `authMechanism` can sometimes be necessary, especially with older setups or specific security policies.

*   **Specify in Connection String:**
    ```
    mongodb://myAppUser:myPassword@localhost:27017/myAppDb?authSource=myAppDb&authMechanism=SCRAM-SHA-256
    ```
    `SCRAM-SHA-256` is the default and recommended mechanism for MongoDB 4.0+. `SCRAM-SHA-1` is an older alternative.

### 6. Environment Variable Inspection

If your application uses environment variables for credentials, ensure they are correctly set and read.
*   **Check Variable Names:** Confirm variable names match what your application expects (e.g., `MONGO_USER`, `MONGO_PASS`).
*   **Verify Values:** Print or echo the environment variables in the context of your application's execution to ensure they hold the correct, complete values. For example, in a Linux shell:
    ```bash
    echo $MONGO_USER
    echo $MONGO_PASS
    ```
    I've personally spent hours debugging this only to find a missing `_` in an env var name.

### 7. Restart Application and MongoDB (If Applicable)

After making any changes to user roles, passwords, or environment variables, always restart your client application to ensure it picks up the new configuration. If you've modified MongoDB server-side settings, a MongoDB restart might be necessary as well, though less common for just user/role changes.

## Code Examples

Here are concise, copy-paste ready examples of how to set up connections, ensuring `authSource` is correctly included.

### Python Example

```python
import pymongo
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

# --- Configuration ---
MONGO_URI = "mongodb://myAppUser:mySecretPassword@localhost:27017/myAppDb?authSource=myAppDb&ssl=false"
# For MongoDB Atlas or remote server, ssl=true is usually required and highly recommended.
# Example Atlas URI: mongodb+srv://myAppUser:mySecretPassword@cluster0.abcde.mongodb.net/myAppDb?retryWrites=true&w=majority

try:
    # Attempt to connect
    client = pymongo.MongoClient(MONGO_URI)

    # The ismaster command is cheap and does not require auth.
    # The actual authentication happens when you try to access a database or collection.
    client.admin.command('ismaster') # Check server status - basic connectivity

    # Try to access a collection, which forces authentication
    db = client.myAppDb
    collection = db.myCollection
    
    # Perform a simple operation to confirm full access
    # This operation will fail if auth is not successful or user lacks privileges
    doc_count = collection.count_documents({})
    print(f"Successfully connected to MongoDB and accessed myCollection. Documents: {doc_count}")

except ServerSelectionTimeoutError as err:
    print(f"Server selection timeout: {err}")
    print("Check network connectivity and MongoDB server status.")
except OperationFailure as err:
    if "Authentication failed" in str(err):
        print(f"MongoDB Authentication Failed: {err}")
        print("Please check username, password, authSource, and user roles.")
    else:
        print(f"MongoDB Operation Failure: {err}")
except Exception as err:
    print(f"An unexpected error occurred: {err}")
finally:
    if 'client' in locals() and client:
        client.close()
```

### Node.js Example

```javascript
const { MongoClient } = require('mongodb');

// --- Configuration ---
const uri = "mongodb://myAppUser:mySecretPassword@localhost:27017/myAppDb?authSource=myAppDb&ssl=false";
// For MongoDB Atlas or remote server, ssl=true is usually required and highly recommended.
// Example Atlas URI: mongodb+srv://myAppUser:mySecretPassword@cluster0.abcde.mongodb.net/myAppDb?retryWrites=true&w=majority

async function connectToMongoDB() {
  const client = new MongoClient(uri, { 
    useNewUrlParser: true, 
    useUnifiedTopology: true 
  });

  try {
    await client.connect();
    console.log("Successfully connected to MongoDB!");

    const db = client.db("myAppDb"); // Specify the database to work with
    const collection = db.collection("myCollection");

    // Perform a simple operation to confirm full access
    const docCount = await collection.countDocuments({});
    console.log(`Accessed myCollection. Documents: ${docCount}`);

  } catch (error) {
    if (error.name === 'MongoServerError' && error.message.includes('Authentication failed')) {
      console.error("MongoDB Authentication Failed:", error.message);
      console.error("Please check username, password, authSource, and user roles.");
    } else {
      console.error("An error occurred:", error);
    }
  } finally {
    await client.close();
    console.log("Connection closed.");
  }
}

connectToMongoDB();
```

## Environment-Specific Notes

The troubleshooting steps remain largely consistent, but the way you interact with MongoDB's configuration and network settings can vary significantly depending on your environment.

### MongoDB Atlas (Cloud)

MongoDB Atlas is a fully managed cloud database service, which simplifies many operational aspects but introduces its own set of authentication considerations.
*   **Network Access:** This is paramount. Ensure your application's IP address (or range) is whitelisted under "Network Access" in your Atlas project. If the IP isn't allowed, you'll often see connection timeouts, but in some edge cases, it might manifest as an auth error if the handshake fails at a specific point.
*   **Database Access:** All user management is handled under "Database Access". This is where you create users, assign them roles (e.g., `readWriteAnyDatabase`, `Atlas Admin`), and set passwords. Always ensure the user exists and has the necessary roles for the database your application is trying to access.
*   **Connection String:** Atlas provides ready-to-use connection strings for various drivers. Always use these, as they'll include the correct `authSource` (typically `admin`) and other parameters like `retryWrites` and `w=majority`. The `mongodb+srv` protocol also handles DNS SRV records for you.
*   **Cloud Provider Firewalls:** Even with Atlas, if your application runs on AWS EC2, GCP Compute Engine, or Azure VM, ensure its own instance-level security groups or network security groups permit outbound connections to MongoDB Atlas's port (default 27017, or 27015-27017 if using `mongodb+srv`).

### Docker

When running MongoDB in Docker containers, authentication issues can sometimes be linked to how environment variables are passed and how containers communicate.
*   **`docker-compose.yml`:** If using `docker-compose`, ensure your `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD`, or application-specific credentials are correctly defined in the `environment` section of your MongoDB service.
    ```yaml
    services:
      mongodb:
        image: mongo:latest
        environment:
          MONGO_INITDB_ROOT_USERNAME: myadmin
          MONGO_INITDB_ROOT_PASSWORD: mysecretpassword
        ports:
          - "27017:27017"
        # ... other configurations like volumes
    ```
*   **Network Configuration:** Ensure your application container can reach the MongoDB container. If they are in the same `docker-compose` network, you can use the service name (e.g., `mongodb`) as the hostname in your connection string.
*   **Data Persistence:** If you're not using Docker volumes to persist your MongoDB data, every time the container restarts, you might lose any custom users you've created, reverting to the initial setup defined by `MONGO_INITDB` variables. This is a common pitfall I've encountered.

### Local Development

For local development environments, issues are often simpler but can still be frustrating.
*   **`mongod` with `--auth`:** If you've started `mongod` without the `--auth` flag, authentication will be disabled, and any credentials will be ignored. If you then try to connect with credentials, it might throw an auth error (or simply connect without needing them, depending on the driver and version). Ensure you explicitly enable authentication if you intend to use it.
    ```bash
    mongod --port 27017 --dbpath /data/db --auth
    ```
*   **Local Firewall:** Your operating system's firewall (e.g., Windows Firewall, `ufw` on Linux, macOS firewall) might be blocking connections to `localhost:27017`. Temporarily disable it for testing, or add an explicit rule to allow access.
*   **Running `mongosh`:** When using the `mongosh` client locally, remember to specify authentication details:
    ```bash
    mongosh "mongodb://myAppUser:mySecretPassword@localhost:27017/myAppDb?authSource=myAppDb"
    ```
    This helps confirm if the credentials work *at all* outside your application.

## Frequently Asked Questions

**Q: My user works when I connect with `mongosh`, but my application still gets "Authentication failed". Why?**
**A:** This is a classic indicator that the `authSource` parameter in your application's connection string is incorrect or missing. When you connect with `mongosh`, you might be implicitly connecting to the `admin` database first or explicitly specifying the authentication database. Ensure your application's connection string includes `?authSource=<yourAuthDb>`. Also, check environment variable loading within your application.

**Q: I just regenerated my password for the user in MongoDB Atlas. Why is my application still failing to authenticate?**
**A:** After regenerating a password, you *must* update your application's configuration with the new password. Common reasons for continued failure include: the application wasn't restarted and is still using cached old credentials; the updated password has a typo; or there's an issue with how the new password is being loaded (e.g., environment variable not refreshed).

**Q: What's the difference between `authSource` and `authMechanism`?**
**A:** `authSource` specifies the database where the user's authentication credentials (username and password) are *defined*. MongoDB looks in this specific database to verify the user. `authMechanism`, on the other hand, defines the *protocol* or method used to perform the authentication challenge-response (e.g., SCRAM-SHA-256 is a common mechanism). Both are crucial for successful authentication but serve different purposes.

**Q: Can a firewall cause `Authentication failed` errors instead of a connection timeout?**
**A:** While less common, it's theoretically possible. Typically, a firewall blocking the port would lead to a connection timeout or refusal error. However, if a firewall selectively drops certain packets during the authentication handshake process (e.g., specific protocol messages), it *could* manifest as an authentication failure. Always check basic connectivity first, but focus on credentials and user permissions as the primary suspects.

**Q: I have a user `myUser` with `readWrite` access to `myAppDb`, but I'm trying to connect to a different database `anotherDb` (e.g., `mongodb://myUser:pass@host/anotherDb?authSource=myAppDb`). Will this work?**
**A:** Yes, this configuration should generally work. You authenticate `myUser` against `myAppDb` (where `myUser` is defined) and then your client driver will establish a session. Once authenticated, the connection will have the privileges granted to `myUser`. If `myUser` only has `readWrite` on `myAppDb`, it won't be able to access `anotherDb` for read/write operations (unless it also has permissions on `anotherDb` or a broader role like `readWriteAnyDatabase`). The initial authentication will succeed if `authSource` is correct, but subsequent operations might fail with permission errors if the user doesn't have roles on the target database.

## Related Errors
- [mongodb-connection-string](/errors/mongodb-connection-string.html)
- [mysql-1045](/errors/mysql-1045.html)