# Node.js Error: EADDRINUSE port already in use
> Encountering EADDRINUSE means your Node.js app can't bind to its desired port because another process is already using it; this guide explains how to fix it.

As an API & Integration Engineer, I've spent countless hours debugging Node.js applications, and the `EADDRINUSE` error is one that pops up regularly, especially during development or when managing multiple services. It's a common hurdle, but fortunately, it's usually straightforward to resolve once you understand its roots. This guide will walk you through what `EADDRINUSE` means, why it occurs, and provide a clear, actionable approach to get your Node.js application back online.

## What This Error Means

The `EADDRINUSE` error, which stands for "Error Address In Use," is a low-level operating system error. When your Node.js application attempts to start an HTTP server (or any server that listens for incoming connections), it tries to "bind" to a specific IP address and port number. This binding process registers your application as the listener for incoming network traffic on that particular endpoint.

The `EADDRINUSE` error means that the operating system has rejected this binding request because another process is *already* listening on that exact IP address and port combination. In simpler terms, the parking spot your app wants to occupy is already taken. This prevents your Node.js server from starting and usually results in an unhandled exception that crashes your application.

## Why It Happens

At its core, `EADDRINUSE` occurs because, on most operating systems, only one process can listen on a specific TCP/IP port at any given time for a particular IP address. This is a fundamental networking principle designed to ensure that incoming data packets know which application to deliver to.

When your Node.js application executes `server.listen(port, hostname, callback)`, it's essentially asking the OS: "Can I open a socket and listen for connections on `hostname:port`?" If the OS replies with `EADDRINUSE`, it means the request was denied because the `hostname:port` combination is currently reserved and actively used by another process. This could be another instance of your own application, a different application entirely, or even a system service.

## Common Causes

In my experience, the `EADDRINUSE` error typically stems from one of a few common scenarios:

1.  **Zombie Process / Unclean Shutdown:** This is perhaps the most frequent cause. A previous instance of your Node.js application, or another service, might have crashed or wasn't shut down cleanly. The process might no longer be actively executing code, but the operating system still holds its network socket open, preventing new applications from binding to the same port. I've seen this countless times in development environments where `Ctrl+C` doesn't always terminate processes gracefully, or a test run failed to clean up after itself.
2.  **Multiple Instances Running:** You might have inadvertently started your Node.js application more than once. This can happen if you open multiple terminal windows and run `node app.js` in each, or if a build script triggers multiple instances.
3.  **Another Application Using the Port:** A completely different application could be using the port your Node.js app expects. This might be a database (e.g., PostgreSQL defaults to 5432), another web server (Apache/Nginx on 80/443), a development tool, or even a system service.
4.  **Port Hardcoding Conflicts:** In development, it's common to hardcode ports like 3000, 8080, or 5000. If you're working on multiple projects concurrently, or if different team members use the same default port, conflicts can arise.
5.  **Hot Reloading / Watchers Gone Awry:** Some development setups use tools that restart the Node.js process upon file changes (e.g., `nodemon`). Occasionally, these tools might fail to terminate the old process before starting a new one, leading to a brief `EADDRINUSE` conflict until the old process is eventually garbage collected by the OS.

## Step-by-Step Fix

Here's a systematic approach to resolving the `EADDRINUSE` error:

### Step 1: Identify the Process Using the Port

The first step is to find out *which* process is hogging your port.

**On macOS/Linux:**
You'll use the `lsof` (list open files) command, specifically `lsof -i :PORT_NUMBER`.

Let's say your Node.js app is trying to listen on port 3000:

```bash
lsof -i :3000
```

You'll get output similar to this:

```
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
node      12345 amara   20u  IPv4 0x...      0t0  TCP *:3000 (LISTEN)
```

The crucial pieces of information here are the `PID` (Process ID) and the `COMMAND`. In this example, `PID 12345` is a `node` process.

**On Windows:**
You'll use `netstat` combined with `findstr` (or `grep` in PowerShell).

Again, for port 3000:

```cmd
netstat -ano | findstr :3000
```

You might see something like:

```
  TCP    0.0.0.0:3000           0.0.0.0:0              LISTENING       6789
```

The last column, `6789`, is the `PID` (Process ID). To find out what process that PID belongs to, use `tasklist`:

```cmd
tasklist /fi "PID eq 6789"
```

This will tell you the image name, e.g., `node.exe`.

### Step 2: Terminate the Culprit Process

Once you have the PID, you can terminate the process.

**On macOS/Linux:**

```bash
kill -9 12345 # Replace 12345 with your actual PID
```
The `kill -9` command sends a `SIGKILL` signal, which forcefully terminates the process. Be cautious; this doesn't allow the process to perform any cleanup. If it's your own app, this is generally safe. If it's a critical system service, identify it carefully before killing.

**On Windows:**

```cmd
taskkill /PID 6789 /F # Replace 6789 with your actual PID
```
The `/F` flag forcefully terminates the process.

After terminating, try restarting your Node.js application.

### Step 3: Change Your Application's Port

If you can't or don't want to kill the offending process (e.g., it's a legitimate service you need running), the next best solution is to change the port your Node.js application uses.

It's good practice to make the port configurable, typically through an environment variable.

```javascript
const port = process.env.PORT || 3000; // Use environment variable PORT, or default to 3000
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
```

Then, you can start your application with a different port:

**On macOS/Linux:**

```bash
PORT=3001 node app.js
```

**On Windows (cmd):**

```cmd
set PORT=3001 && node app.js
```

**On Windows (PowerShell):**

```powershell
$env:PORT=3001; node app.js
```

### Step 4: Implement Graceful Shutdown (Prevention)

To prevent zombie processes, ensure your Node.js application shuts down gracefully when it receives termination signals (like `SIGTERM` from process managers or `Ctrl+C`). This allows the server to close its connections and release the port cleanly.

```javascript
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

const server = app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});

process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => { // For Ctrl+C
  console.log('SIGINT signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});
```

### Step 5: Check Process Managers or Service Configurations

If you're using `pm2`, `forever`, `systemd`, or similar process managers, ensure they aren't configured to run multiple instances or that previous instances are properly stopped before new ones are started. I've encountered scenarios where a `systemd` service restart failed, leaving the old process alive, or `pm2` was accidentally configured to start multiple instances on the same port.

### Step 6: Reboot (Last Resort)

If all else fails, a system reboot will clear all actively used ports and restart services. This is a blunt instrument but effective when you're pressed for time or can't identify the rogue process.

## Code Examples

Here are concise, copy-paste ready code examples:

**1. Basic Node.js HTTP Server with Port Configuration:**

```javascript
// app.js
const http = require('http');

const port = process.env.PORT || 3000; // Prefer environment variable, default to 3000

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Hello World from Node.js!\n');
});

server.listen(port, () => {
  console.log(`Server running at http://localhost:${port}/`);
});

server.on('error', (e) => {
  if (e.code === 'EADDRINUSE') {
    console.error(`Port ${port} is already in use.`);
    console.error('Another server is probably running, or a previous instance crashed.');
    process.exit(1); // Exit with an error code
  } else {
    console.error('Server error:', e.message);
  }
});
```

**2. Express.js Server with Graceful Shutdown:**

```javascript
// server.js
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Hello from Express!');
});

const server = app.listen(port, () => {
  console.log(`Express server listening on port ${port}`);
});

// Handle server errors, specifically EADDRINUSE
server.on('error', (e) => {
  if (e.code === 'EADDRINUSE') {
    console.error(`ERROR: Port ${port} is already in use.`);
    console.error('Please check if another instance of this app or another service is running.');
    process.exit(1);
  } else {
    console.error('Server experienced an unexpected error:', e);
    process.exit(1);
  }
});

// Graceful shutdown handling
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully.');
  server.close(() => {
    console.log('HTTP server closed.');
    process.exit(0);
  });
});

process.on('SIGINT', () => { // Ctrl+C
  console.log('SIGINT received, shutting down gracefully.');
  server.close(() => {
    console.log('HTTP server closed.');
    process.exit(0);
  });
});
```

## Environment-Specific Notes

The `EADDRINUSE` error manifests differently and requires slightly varied approaches depending on your deployment environment.

*   **Local Development:** This is where you'll most frequently encounter it. As discussed, `lsof` (macOS/Linux) or `netstat` (Windows) are your best friends. Often, a quick `kill -9 PID` or changing the port for your current development session is all it takes. I keep a cheat sheet of these commands handy.
*   **Docker:** In a Dockerized environment, `EADDRINUSE` usually means one of two things:
    1.  **Container Port Conflict:** Another container on the *same Docker host* is trying to map its internal port to the *same host port* that your new container wants to use. For example, if two containers try to map `80:3000`. Use `docker ps` to see what ports existing containers are exposing.
    2.  **Host Port Conflict:** A process *on the Docker host machine itself* is already using the port you're trying to map to. In this case, use `lsof` or `netstat` on the *host machine* to identify the conflict.
    Ensure your Dockerfiles and `docker-compose.yml` files correctly manage port exposure and mapping. Always listen on `0.0.0.0` inside the container, and map container ports (e.g., `3000`) to appropriate host ports.
*   **Cloud (Heroku, Kubernetes, AWS EC2, etc.):**
    *   **Heroku:** Heroku explicitly provides a `PORT` environment variable that your application *must* listen on. If your Node.js app hardcodes a port (e.g., `app.listen(3000)`), it will fail with `EADDRINUSE` because Heroku has already allocated a dynamic port for your dyno and expects your app to use `process.env.PORT`. This is a common pitfall I've debugged for teams migrating to Heroku.
    *   **Kubernetes:** `EADDRINUSE` errors in Kubernetes are rarer at the service level (as services typically abstract ports). When they do occur, it's usually inside a pod trying to bind to a `hostPort` that's already in use on the specific node where the pod is scheduled. It can also indicate a misconfiguration where multiple containers within the *same pod* attempt to bind to the same internal port, which is generally bad practice. Always ensure your containers listen on their designated internal ports and let Kubernetes handle service discovery and routing.
    *   **AWS EC2 / Virtual Machines:** This mirrors the "local development" scenario but on a remote server. You'll SSH into the instance and use `lsof` or `netstat` to find the rogue process. Ensure your deployment scripts or process managers cleanly stop previous instances before starting new ones. I've seen situations where an `npm start` command was run manually on an EC2 instance, leaving a process running even after subsequent automated deployments.

## Frequently Asked Questions

**Q: Can multiple Node.js applications listen on the same port?**
**A:** No, not on the same IP address and port combination. The operating system allows only one process to "own" a specific network socket at a time. If you need multiple services to appear on the same public port (e.g., 80 or 443), you'll typically use a reverse proxy (like Nginx or Caddy) to route requests to different internal ports where your Node.js apps are actually listening.

**Q: How can I prevent `EADDRINUSE` errors in CI/CD pipelines?**
**A:** Ensure your CI/CD setup includes robust cleanup steps. For integration tests, use tools that allocate dynamic ports, or configure distinct ports for different services. During deployment, implement graceful shutdowns for old application instances before new ones are started. If using container orchestration, verify your configuration doesn't lead to port conflicts.

**Q: Is it always safe to kill the process identified by `lsof` or `netstat`?**
**A:** Generally, yes, if you know it's your own application or a development tool. However, always verify the `COMMAND` and `USER` fields. Killing system-critical processes (e.g., a database, SSH server, or system service) can cause stability issues or data loss. If in doubt, try changing your application's port first.

**Q: My application is supposed to restart automatically, but it gets `EADDRINUSE`. What's wrong?**
**A:** This often indicates an issue with your process manager or auto-restart mechanism. It might be failing to fully terminate the old process before attempting to start a new one. Review the logs of your process manager (e.g., `pm2 logs`, `journalctl -u your-service`) to see if the old process is receiving and acting on termination signals (`SIGTERM`, `SIGINT`) properly, or if there's a timeout causing it to be forcibly killed too late.

## Related Errors