# pika.exceptions.ConnectionClosedByBroker: (320, 'CONNECTION_FORCED')
> Encountering pika.exceptions.ConnectionClosedByBroker: (320, 'CONNECTION_FORCED') indicates your RabbitMQ broker forcefully closed the connection, often due to an authentication or policy issue; this guide explains how to diagnose and fix it.

## What This Error Means

This Pika exception signals that your Python application's connection attempt or an existing connection to a RabbitMQ broker was explicitly rejected or terminated by the broker itself. The `(320, 'CONNECTION_FORCED')` part is critical:
*   `320`: This is the AMQP reply code for `CONNECTION_FORCED`. It's a high-level error indicating the broker has decided to close the connection. It's not a network timeout or a client-side error.
*   `CONNECTION_FORCED`: This human-readable message confirms the broker initiated the closure. It implies that from RabbitMQ's perspective, something about your client's behaviour, configuration, or environment is unacceptable, leading it to sever the connection.

In my experience, this is one of those errors that points you squarely to the broker's side for investigation, rather than just the client. It means the connection was established enough for RabbitMQ to understand *why* it needed to close it.

## Why It Happens

The broker forcefully closes a connection when it detects a violation of its security rules, operational policies, or resource limits. It's a protective measure. Unlike a network drop where the connection might just hang or time out, `CONNECTION_FORCED` is an active decision made by RabbitMQ. This usually happens during the connection handshake or shortly after, once the client has presented its credentials and the broker has had a chance to evaluate them, or if a pre-established policy is violated during an active session.

## Common Causes

Based on countless hours debugging production systems, I've narrowed down the most frequent reasons for a `(320, 'CONNECTION_FORCED')` error:

1.  **Authentication Failure (Incorrect Credentials):** This is by far the most common cause. The username and/or password provided by your Pika client do not match any valid user configured in RabbitMQ, or the credentials are correct but the user lacks permissions for the target virtual host.
    *   *Example:* Typos in the username or password in your application's configuration.
    *   *Example:* Using default credentials (e.g., `guest:guest`) from a non-localhost connection, which RabbitMQ usually forbids for security reasons.

2.  **Authorization Failure (Permissions):** Even if you authenticate successfully, the user might not have the necessary permissions (configure, write, read) on the specific virtual host (`vhost`), queues, or exchanges your application is trying to access or create.
    *   *Example:* Your application tries to declare a queue in `vhost A` but the authenticated user only has permissions for `vhost B`.
    *   *Example:* The user has read permissions but tries to publish a message.

3.  **Virtual Host (VHost) Not Found or Incorrect:** The virtual host specified in your connection string does not exist on the RabbitMQ broker, or your user does not have access to it.
    *   *Example:* Connecting to `/my_app_vhost` when the vhost is actually named `my-app-vhost`. VHost names are case-sensitive.

4.  **Broker-Side Policy Violations:** RabbitMQ administrators can set policies that impact connections.
    *   *Maximum Connections:* A policy might limit the number of connections a single user can open, or the total connections to a vhost, or even to the entire broker. If your application exceeds this, new connection attempts will be forced closed.
    *   *Idle Timeout:* Less common for `CONNECTION_FORCED` during initial connection, but if an active connection remains idle for too long and an `idle_timeout` policy is in place, the broker might close it.
    *   *Resource Limits:* If the broker is severely overloaded (e.g., low disk space, high memory usage, too many open file descriptors), it might start rejecting new connections or even force existing ones to close to stabilize itself. This isn't the primary reason for `CONNECTION_FORCED` but can manifest similarly.

5.  **Broker Restart or Maintenance:** While usually resulting in a more generic connection error, sometimes during a graceful shutdown or restart, RabbitMQ might force close connections as part of its termination process. This is generally less specific to `(320, 'CONNECTION_FORCED')` but worth considering if the problem is intermittent or follows a known maintenance window.

## Step-by-Step Fix

Here's my go-to troubleshooting process when I hit this error. It usually helps me pinpoint the issue quickly.

1.  **Verify RabbitMQ User Credentials and VHost:**
    *   **Action:** Double-check the username, password, and virtual host in your Pika connection string or configuration. Ensure there are no typos, leading/trailing spaces, or incorrect casing.
    *   **Tool:** `rabbitmqctl` (on the broker server) or RabbitMQ Management UI.
    *   **How:**
        ```bash
        # List users
        sudo rabbitmqctl list_users

        # Check user details (replace 'myuser' with your actual username)
        # This will show which vhosts the user has access to.
        sudo rabbitmqctl list_user_permissions myuser

        # List vhosts
        sudo rabbitmqctl list_vhosts
        ```
    *   **Common Pitfall:** Using `guest` user from a remote machine. By default, the `guest` user can only connect from `localhost`. Create a dedicated user for your application.

2.  **Check User Permissions for the Target VHost:**
    *   **Action:** Confirm that the user your application is connecting with has appropriate `configure`, `write`, and `read` permissions for the specific virtual host it needs to interact with.
    *   **Tool:** `rabbitmqctl` or RabbitMQ Management UI.
    *   **How:** If your user `myuser` needs to access `my_vhost`, ensure it has permissions set for it.
        ```bash
        # Example: Setting full permissions for 'myuser' on 'my_vhost'
        # Only do this if you know it's safe for your environment!
        sudo rabbitmqctl set_permissions -p my_vhost myuser ".*" ".*" ".*"
        ```
    *   **Important:** Granular permissions are best practice in production. `".*"` gives full access to all resources.

3.  **Examine RabbitMQ Broker Logs:**
    *   **Action:** This is crucial. The broker's logs will often contain the precise reason for forcing the connection close. Look for entries related to authentication failures, authorization failures, or policy violations around the time your application tried to connect.
    *   **Location:**
        *   **Linux (package install):** `/var/log/rabbitmq/rabbit@<hostname>.log` and `rabbit@<hostname>_sasl.log`
        *   **Docker:** `docker logs <rabbitmq_container_name>`
        *   **Cloud (AWS AMQ):** CloudWatch logs for your broker instance.
    *   **Keywords to search for:** `authentication failed`, `access refused`, `connection limit`, `closed connection`, `denied access`, `vhost`.

4.  **Inspect Broker Policies (if applicable):**
    *   **Action:** If permissions are correct, investigate any configured RabbitMQ policies that might restrict connections.
    *   **Tool:** RabbitMQ Management UI (Admin -> Policies) or `rabbitmqctl`.
    *   **How:**
        ```bash
        # List all policies
        sudo rabbitmqctl list_policies -p /

        # Example: Looking for max connections per user
        # Note: This is an operator-level config, not always visible via list_policies directly
        ```
    *   **Common Policy:** `max-connections` or `max-channels` per user or vhost.

5.  **Verify Network Connectivity (Less likely for 320, but good sanity check):**
    *   **Action:** While `CONNECTION_FORCED` implies initial connection success for the broker to send the error, ensure basic network reachability.
    *   **Tool:** `ping`, `telnet`, `nc` (netcat).
    *   **How:** From your client machine, try to connect to the RabbitMQ port (default 5672).
        ```bash
        telnet <rabbitmq_host> 5672
        ```
        If it connects, you'll see a blank screen or a successful connection message. If it hangs or refuses, you have a firewall or network routing issue *before* the broker can even process your connection. This would typically manifest as a different Pika error (e.g., connection refused, timeout), but it's a good step to rule out broader network problems.

## Code Examples

Here are some concise Pika examples demonstrating robust connection handling, which is crucial when dealing with potential `ConnectionClosedByBroker` errors.

### Basic Pika Connection with Explicit Credentials and Error Handling

This example shows how to connect and gracefully catch the `ConnectionClosedByBroker` exception.

```python
import pika
from pika.exceptions import ConnectionClosedByBroker, AMQPConnectionError
import time

RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_VHOST = '/'
RABBITMQ_USER = 'myuser'
RABBITMQ_PASS = 'mypassword' # Replace with a strong password!

def connect_to_rabbitmq():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=60 # A good practice to keep connections alive
    )

    try:
        print(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}{RABBITMQ_VHOST} as user {RABBITMQ_USER}...")
        connection = pika.BlockingConnection(parameters)
        print("Successfully connected to RabbitMQ.")
        return connection
    except ConnectionClosedByBroker as e:
        print(f"ERROR: Connection to RabbitMQ was forced closed by broker: {e}")
        # Here, inspect e.reply_code and e.reply_text for more details if available
        if e.reply_code == 320:
            print("This usually indicates an authentication/authorization failure or policy violation.")
            print("Please check credentials, user permissions for the vhost, and broker logs.")
        return None
    except AMQPConnectionError as e:
        print(f"ERROR: Failed to connect to RabbitMQ due to general AMQP error: {e}")
        print("This could be due to network issues, broker not running, or incorrect host/port.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during connection: {e}")
        return None

if __name__ == "__main__":
    connection = None
    while connection is None:
        connection = connect_to_rabbitmq()
        if connection is None:
            print("Retrying connection in 5 seconds...")
            time.sleep(5)
        else:
            try:
                # Example: Do something with the connection, like opening a channel
                channel = connection.channel()
                channel.queue_declare(queue='hello')
                print("Channel opened and queue declared successfully. Connection is stable.")
                # Keep the connection alive for a bit to demonstrate stability
                time.sleep(30)
            except ConnectionClosedByBroker as e:
                print(f"ERROR: Connection was forced closed during operation: {e}")
                connection = None # Force a retry
            except Exception as e:
                print(f"An error occurred during channel operation: {e}")
                connection = None # Force a retry
            finally:
                if connection and connection.is_open:
                    print("Closing connection.")
                    connection.close()
                elif connection is None:
                    print("Connection was already closed or never established, skipping close.")

```

## Environment-Specific Notes

How you troubleshoot `CONNECTION_FORCED` can vary slightly depending on your environment.

### Local Development

*   **Ease of Access:** You usually have full root/sudo access to the RabbitMQ server. This makes checking logs (`/var/log/rabbitmq/`) and using `rabbitmqctl` directly very straightforward.
*   **Common Traps:**
    *   Forgetting to start RabbitMQ. (Results in `AMQPConnectionError`, not 320, but worth mentioning).
    *   Using the `guest` user from a non-localhost connection (e.g., if your app is in a container, but RabbitMQ is on the host, it's not `localhost` from the app's perspective).
    *   Simple typos in `.env` files for credentials.

### Docker / Containerized Environments

*   **Log Access:** Use `docker logs <container_name_or_id>` for the RabbitMQ container to access logs.
*   **`rabbitmqctl` Access:** You'll need to run `rabbitmqctl` commands *inside* the RabbitMQ container:
    ```bash
    docker exec -it <rabbitmq_container_name_or_id> rabbitmqctl list_users
    ```
*   **Networking:**
    *   Ensure your application container can reach the RabbitMQ container. If they are in the same Docker network, use the service name (e.g., `rabbitmq` instead of `localhost` or an IP).
    *   Check port mappings if you're trying to connect from outside the Docker network.
*   **Configuration:** Credentials and vhosts are typically passed via environment variables to the RabbitMQ container and to your Pika application container. Double-check these.

### Cloud (Managed RabbitMQ Services like AWS AMQ)

*   **Reduced Control:** You won't have direct SSH access to the underlying OS or `rabbitmqctl` on the broker itself.
*   **Log Access:** Broker logs are usually integrated with the cloud provider's logging service (e.g., AWS CloudWatch for AMQ). This is your primary source of truth for broker-side errors.
*   **Security Groups/Firewalls:** Crucial for connectivity. Ensure the security group for your AMQ broker allows inbound connections on port 5672 from the security group/IP addresses of your application servers.
*   **IAM Roles/Credentials:** Authentication might involve IAM roles or secrets management services, not just plain username/password. Verify these integrations. I've seen misconfigured IAM policies lead to `CONNECTION_FORCED` when the broker rejects the connection.
*   **Managed Policies:** Be aware of any default or custom policies enforced by the managed service (e.g., maximum connections per broker). These can sometimes be hidden behind service-specific configurations.

## Frequently Asked Questions

**Q: Is `(320, 'CONNECTION_FORCED')` a Pika error or a RabbitMQ error?**
**A:** It's fundamentally a RabbitMQ error. The broker initiated the closure and sent the AMQP reply code 320. Pika is simply reporting the broker's action to your application.

**Q: Can a firewall cause this specific error?**
**A:** Not directly. If a firewall completely blocks the connection, Pika would typically raise a `ConnectionRefusedError` or a timeout (`AMQPConnectionError`). `CONNECTION_FORCED` means the initial TCP handshake *succeeded* and the broker *received* enough information to decide to actively close the connection. However, an *improperly configured* firewall that only allows specific ports or protocols *after* an initial connection could theoretically lead to weird issues, but it's not the primary cause for this specific error code.

**Q: How do I check RabbitMQ logs effectively?**
**A:** First, know where your logs are stored (local filesystem, Docker logs, cloud logging service). Then, use tools like `grep`, `awk`, `less`, `tail -f` to filter and follow the logs. Look for timestamps matching your application's connection attempts, and keywords like `authentication`, `permission`, `access refused`, `denied`, `forced close`.

**Q: What if the connection works sometimes and fails others?**
**A:** This often points to resource contention, transient network issues, or a race condition related to policy limits.
*   **Resource Limits:** The broker might be running low on memory/disk, or hitting max connections at peak times. Check RabbitMQ health metrics.
*   **Load Balancers/Clusters:** If connecting to a clustered RabbitMQ behind a load balancer, one node might be misconfigured, unhealthy, or have different policies.
*   **Application Logic:** Is your application opening too many connections, or not closing them properly?

**Q: What's the difference between `(320, 'CONNECTION_FORCED')` and other connection errors?**
**A:**
*   `ConnectionRefusedError` (or `AMQPConnectionError` wrapping it): Broker is not running, or firewall is blocking the initial connection. The broker didn't even get to process your request.
*   `Timeout` (`AMQPConnectionError`): Network latency, broker overloaded and slow to respond, or the connection hung before a proper handshake.
*   `(320, 'CONNECTION_FORCED')`: The broker *explicitly* told your client to go away after evaluating your connection attempt. It's an active rejection.

## Related Errors