# BlockingIOError: [Errno 11] Resource temporarily unavailable
> Encountering BlockingIOError [Errno 11] means a non-blocking I/O operation would block, indicating a resource is temporarily unavailable; this guide explains how to fix it.

As a Systems Engineer working with Python, I frequently encounter I/O-related issues, especially in high-concurrency or distributed systems. The `BlockingIOError: [Errno 11] Resource temporarily unavailable` is a classic example that often surfaces in network applications or when dealing with file descriptors in a non-blocking manner. Understanding this error is crucial for building robust and performant services.

## What This Error Means

At its core, `BlockingIOError` with `[Errno 11] Resource temporarily unavailable` signals that a requested I/O operation (like `socket.recv()`, `socket.send()`, or `os.read()`) on a non-blocking file descriptor could not be completed immediately without pausing the execution flow. In a non-blocking context, such an operation is designed to return immediately, either with data/status or an error. When the resource isn't ready – for instance, no data has arrived on a socket, or the send buffer is full – the OS reports `EAGAIN` or `EWOULDBLOCK`, which Python translates into `BlockingIOError`.

This error does *not* mean the resource is permanently unavailable or that something is fundamentally broken. It simply implies a temporary state where the operation *would block* if it were a blocking call, and since it's non-blocking, the system tells you to try again later. It's a signal to your application that it should either wait (using mechanisms like `select`, `poll`, or `epoll`) or perform other tasks before reattempting the I/O.

## Why It Happens

The reason this error surfaces is fundamental to how non-blocking I/O operates. When you configure a socket or file descriptor for non-blocking operations (e.g., `socket.setblocking(False)`), you're telling the operating system: "Don't make my program wait for this I/O to complete. If it can't be done instantly, tell me, and I'll deal with it."

The OS then responds with `EAGAIN` (or `EWOULDBLOCK`, which is often the same value) when:
1.  **Reading:** There is no data currently available in the receive buffer of the socket or pipe. If the operation were blocking, it would pause until data arrived.
2.  **Writing:** The send buffer of the socket or pipe is full, and the operating system cannot accept more data immediately. A blocking write would wait for space to become available.
3.  **Connecting:** An asynchronous connection attempt is still in progress and hasn't completed yet.

This mechanism is essential for event-driven architectures and servers that handle many concurrent connections without using a separate thread or process for each. Instead of blocking on one connection, the server can check all connections for readiness and process only those that are ready.

## Common Causes

In my experience, `BlockingIOError: [Errno 11]` typically stems from a few common scenarios:

*   **Incorrect Non-Blocking Logic:** The most frequent cause is attempting a non-blocking I/O operation without properly integrating it into an event loop or a readiness-checking mechanism (like `select.select` or `selectors` module). You perform a non-blocking `recv()` and expect data, but no data has arrived yet, leading to the error.
*   **Network Congestion or Slow Peer:** When sending data, if the network is saturated or the receiving end is slow to consume data, your socket's send buffer can fill up. Subsequent `socket.send()` calls will then raise `BlockingIOError`. Similarly, if the peer isn't sending data, your `socket.recv()` will encounter this error.
*   **Rapid Writes to a Full Buffer:** I've seen this in production when an application generates data faster than it can be sent over the network or written to a pipe. Without proper flow control or a mechanism to wait for buffer space, `send()` or `write()` calls will consistently fail with `BlockingIOError`.
*   **Asynchronous Connection Attempts:** When performing `socket.connect()` on a non-blocking socket, the connection isn't usually established instantly. The operation will raise `BlockingIOError` (or `OSError` with `EINPROGRESS`) as it waits for the TCP handshake to complete. You then need to `select` for write readiness to know when the connection is established or failed.
*   **Misconfigured File Descriptors:** While less common for standard sockets, if other file descriptors (like pipes or TTYs) are set to non-blocking mode and aren't ready, similar errors can occur.

## Step-by-Step Fix

Addressing `BlockingIOError` isn't about "fixing" a broken component, but rather refining your I/O handling logic to correctly manage non-blocking operations.

### Step 1: Confirm Non-Blocking Mode is Intentional

First, verify that your code intends to use non-blocking I/O. If you didn't explicitly call `socket.setblocking(False)`, you might have inherited a non-blocking state from a library or parent process. If you *intended* for the operation to block, then the fix is simply to remove the non-blocking flag or ensure `socket.setblocking(True)` is called.

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Default is blocking (True). If you need it to block, ensure this:
s.setblocking(True)
# Or if you don't explicitly set it, it will usually be blocking by default.
try:
    s.connect(('localhost', 12345)) # This would block
except BlockingIOError as e:
    print(f"Error connecting: {e}")
    # This scenario shouldn't happen with a blocking socket unless connect itself fails.
```

### Step 2: Implement Proper Readiness Checking

If non-blocking I/O is indeed intentional (which it usually is when you see this error), you must use a multiplexing mechanism to determine when a file descriptor is ready for I/O *before* attempting the operation. Python's `selectors` module is the modern, cross-platform way to do this.

```python
import socket
import selectors

HOST = 'localhost'
PORT = 12345

sel = selectors.DefaultSelector()

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)
            if recv_data:
                data.outb += recv_data # Echo received data
            else:
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()
        except BlockingIOError:
            # Expected when no data is available yet, just ignore and wait for next poll
            pass
        except Exception as e:
            print(f"Error during recv from {data.addr}: {e}")
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if data.outb:
            try:
                print(f"Echoing {len(data.outb)} bytes to {data.addr}")
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]
            except BlockingIOError:
                # Expected when send buffer is full, just ignore and wait for next poll
                pass
            except Exception as e:
                print(f"Error during send to {data.addr}: {e}")
                sel.unregister(sock)
                sock.close()

# Example server setup
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((HOST, PORT))
lsock.listen()
print(f"Listening on {(HOST, PORT)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

# Main event loop
try:
    while True:
        events = sel.select(timeout=None) # blocks until sockets are ready
        for key, mask in events:
            if key.data is None: # Listening socket
                accept_wrapper(key.fileobj)
            else: # Connected client socket
                service_connection(key, mask)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()
    lsock.close()
```

### Step 3: Gracefully Handle the Exception

Even with readiness checking, it's good practice to wrap non-blocking I/O calls in `try...except BlockingIOError`. This can happen if, for instance, a resource state changes between the `select` call and the actual `recv`/`send` call, or if you're polling less frequently. When caught, simply ignore it and wait for the next iteration of your event loop.

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setblocking(False)
s.connect_ex(('localhost', 12345)) # connect_ex returns errno, doesn't raise BlockingIOError on EINPROGRESS

# ... later in your event loop, after checking for write readiness ...
try:
    data = s.recv(1024)
    if data:
        # process data
        pass
except BlockingIOError:
    # No data available, try again later.
    pass
except Exception as e:
    # Handle other unexpected errors
    print(f"An unexpected error occurred: {e}")
```

### Step 4: Review Buffer Sizes and Flow Control

If you're primarily seeing this error on `send()` calls, it might indicate that your application is producing data faster than the network or the remote peer can consume it.
*   **TCP send/receive buffers:** The OS manages these, but understanding their role is key. If the send buffer is full, `send()` will block (or raise `BlockingIOError` if non-blocking).
*   **Application-level buffers:** Implement queues or buffers within your application to temporarily store data that couldn't be sent. Send data from this buffer only when the socket is write-ready.

### Step 5: Check System Resource Limits

In rare cases, an `Errno 11` could relate to system-wide resource limits, although `Errno 24: Too many open files` is more typical for file descriptor exhaustion. However, if your system is under extreme memory pressure, kernel buffers might not be allocated efficiently. This is more of a system administration concern, but worth noting. You can check limits using `ulimit -a` on Linux.

```bash
# Check current user limits
ulimit -a
```

## Code Examples

### Non-Blocking Client Connection (Simplified)

This example shows how a client might attempt a non-blocking connection and then check for readiness.

```python
import socket
import selectors
import time

sel = selectors.DefaultSelector()

def connect_to_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    err = sock.connect_ex((host, port)) # Returns errno, not BlockingIOError
    if err != 0 and err != 115: # 115 is EINPROGRESS (Resource temporarily unavailable)
        print(f"Error connecting: {err}")
        return None

    print(f"Initiated non-blocking connect to {host}:{port}")
    # Register for write events to know when connection completes
    sel.register(sock, selectors.EVENT_WRITE, data={'host': host, 'port': port, 'status': 'connecting'})
    return sock

def service_client_connection(key, mask):
    sock = key.fileobj
    data = key.data

    if data['status'] == 'connecting':
        if mask & selectors.EVENT_WRITE:
            # Connection complete (or failed)
            try:
                # Check for connection errors, e.g., using getsockopt
                error_code = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if error_code == 0:
                    print(f"Successfully connected to {data['host']}:{data['port']}")
                    data['status'] = 'connected'
                    # Now register for read events to receive data
                    sel.modify(sock, selectors.EVENT_READ, data=data)
                    # Send a message immediately
                    sock.sendall(b"Hello from non-blocking client!\n")
                else:
                    print(f"Connection failed to {data['host']}:{data['port']}: Errno {error_code}")
                    sel.unregister(sock)
                    sock.close()
            except BlockingIOError:
                # Should not happen after write readiness for connect
                pass
            except Exception as e:
                print(f"Error after connect: {e}")
                sel.unregister(sock)
                sock.close()

    elif data['status'] == 'connected':
        if mask & selectors.EVENT_READ:
            try:
                recv_data = sock.recv(1024)
                if recv_data:
                    print(f"Received: {recv_data.decode().strip()}")
                else:
                    print(f"Server closed connection.")
                    sel.unregister(sock)
                    sock.close()
            except BlockingIOError:
                pass # No data yet, wait for next cycle
            except Exception as e:
                print(f"Error receiving: {e}")
                sel.unregister(sock)
                sock.close()

# Example usage:
client_socket = connect_to_server('localhost', 12345) # Assuming a server is running

try:
    while True:
        events = sel.select(timeout=1) # 1-second timeout
        if not events and client_socket and client_socket._closed: # All sockets closed
            break
        for key, mask in events:
            service_client_connection(key, mask)
        time.sleep(0.1) # Small pause to prevent busy-waiting if select returns quickly
except KeyboardInterrupt:
    print("Client stopped.")
finally:
    sel.close()
    if client_socket and not client_socket._closed:
        client_socket.close()
```

## Environment-Specific Notes

The manifestation and troubleshooting of `BlockingIOError` can subtly change depending on your deployment environment.

*   **Cloud Environments (AWS EC2, Google Cloud, Azure VMs):**
    *   **Network Latency:** Higher network latency between instances or services can exacerbate situations where send buffers fill up, leading to more frequent `BlockingIOError` on `send()`.
    *   **Resource Limits:** Cloud instances have virtualized resources. While typically generous, ensure you're not hitting specific network bandwidth limits or connection limits imposed by your instance type or network configuration.
    *   **Security Groups/Firewalls:** A misconfigured firewall might silently drop packets, leading to timeouts or incomplete connections, which can indirectly contribute to I/O issues, though `BlockingIOError` is usually a local resource issue.

*   **Docker Containers:**
    *   **Container Networking:** Docker's default bridge networking adds a layer of abstraction. While usually performant, high-traffic scenarios or misconfigurations (e.g., incorrect port mappings, network driver issues) could stress network stacks and contribute to buffer pressure.
    *   **Resource Allocation:** Containers are often resource-constrained. If a container is starved of CPU or memory, it might not process I/O events quickly enough, leading to internal buffers filling up or data not being consumed from network buffers in time. Always check container resource limits (`--cpus`, `--memory`).
    *   **File Descriptor Limits:** Containers inherit host limits or have their own. Ensure `ulimit -n` inside the container is sufficient for your application, especially for servers handling many connections.

*   **Local Development:**
    *   **Loopback Device:** On `localhost` (loopback), network operations are extremely fast. This means send buffers rarely fill up unless your application actively writes at an incredibly high rate.
    *   **Rapid Iteration:** In development, you might be less rigorous with error handling. A `BlockingIOError` might surface more readily because you're testing edge cases or pushing limits without a finely tuned event loop.
    *   **Single-Machine Bottlenecks:** If running client and server on the same machine, contention for CPU or memory from other processes can be a factor.

Regardless of the environment, the core solution remains proper non-blocking I/O logic using `selectors`. However, diagnosing *why* buffers are filling up or why a remote resource is slow might require environment-specific monitoring and analysis. I've found that checking network stats (`netstat -s`, `ss -s`) and system load (`top`, `htop`) are invaluable first steps in any environment.

## Frequently Asked Questions

**Q: Is `BlockingIOError` always a problem?**
**A:** No, not at all. For non-blocking I/O, `BlockingIOError` (specifically `[Errno 11]`) is often the expected signal from the OS that an operation would block. It's only a problem if you're not prepared to handle it by re-trying the operation later (e.g., within an event loop).

**Q: How does `socket.timeout` relate to `BlockingIOError`?**
**A:** `socket.timeout` is raised when a blocking socket operation exceeds a set timeout duration. `BlockingIOError` occurs immediately on a non-blocking socket when the operation *cannot* complete without blocking. They are distinct concepts for different I/O modes. `socket.settimeout(x)` implies blocking I/O with a time limit, while `socket.setblocking(False)` implies non-blocking I/O.

**Q: Can `BlockingIOError` happen with files, not just sockets?**
**A:** Yes, while less common, `BlockingIOError` can occur when performing non-blocking I/O on other file descriptors like pipes (`os.pipe()`) or character devices, particularly if the `os.O_NONBLOCK` flag is set during their creation and the underlying resource isn't ready.

**Q: What if I'm using an asynchronous library like `asyncio`?**
**A:** Libraries like `asyncio` abstract away the explicit handling of `BlockingIOError`. They use event loops and underlying `selectors` (or similar OS-specific mechanisms) to manage I/O readiness internally. If you see `BlockingIOError` when using `asyncio`, it usually means you're performing a blocking call in an `async` function, or there's a misconfiguration where an underlying socket was inadvertently set to non-blocking and then accessed directly without `await` or proper `asyncio` I/O primitives.

**Q: Is it safe to just catch and ignore `BlockingIOError`?**
**A:** It's safe to catch and ignore `BlockingIOError` *if* you are properly using an event loop (like `selectors` or `asyncio`) to wait for readiness. Simply ignoring it in a tight loop without a waiting mechanism will result in busy-waiting, consuming excessive CPU, and still not resolving the underlying I/O state. You need to wait for the resource to become ready.

## Related Errors