# Node.js Error: EADDRINUSE port already in use
> Encountering `EADDRINUSE` means your Node.js application is trying to bind to a network port that's already in use; this guide explains how to fix it.

## What This Error Means

The `EADDRINUSE` error, short for "Error: Address In Use," is a fundamental networking error. In Node.js, it means your application tried to start a server and listen on a network port that's already occupied by another process. Think of network ports as unique mailboxes. Only one process can listen for traffic on a specific port at any given time. When your Node.js app attempts to use an occupied port, the operating system throws this error to prevent conflicts.

## Why It Happens

This error arises because the operating system enforces a strict rule: only one process can bind to a specific IP address and port combination simultaneously. This prevents ambiguity and ensures that incoming network traffic always reaches the intended application. Node.js applications use a method (e.g., `server.listen()`) to request a port. If another application has already successfully bound to that port, your Node.js application's request will be denied with `EADDRINUSE`. This is standard operating system behavior, not a Node.js-specific bug.

## Common Causes

In my experience as an API & Integration Engineer, `EADDRINUSE` is a common error during local development. It's usually straightforward to fix once you understand the typical reasons:

1.  **Ghost Process / Unclean Shutdown:** This is the most frequent cause. A previous instance of your Node.js application or another service crashed, wasn't gracefully shut down, or was simply left running. When you try to start a new instance, the old one still holds the port.
2.  **Multiple Application Instances:** You might have inadvertently launched your Node.js application twice. This happens when you run `npm start` (or `node server.js`) in multiple terminals or if an IDE's run configuration starts an additional instance.
3.  **Conflicting Services:** Another application or service is legitimately using that port. Examples include:
    *   **Web servers:** Apache, Nginx (often ports 80, 443).
    *   **Development servers:** React (3000), Angular (4200), Flask (5000).
    *   **Databases:** PostgreSQL (5432), MongoDB (27017).
    *   **Other Node.js apps:** Another project of yours or a colleague's on the same machine.
4.  **Misconfigured Development Tools:** Hot-reloading features or build tools can sometimes leave processes lingering, especially after an error or forced restart. I've seen this in production when a deployment script failed midway, leaving an old application instance active alongside a new, failed attempt.
5.  **Using a Well-Known Port Without Privileges:** Ports below 1024 are "well-known" and often require root or administrator privileges. While a "Permission Denied" error is more common, `EADDRINUSE` can occur if another high-privileged process already occupies such a port.

## Step-by-Step Fix

Here's a practical, step-by-step approach to resolving `EADDRINUSE`. The goal is to identify which process is using the port and then decide whether to terminate it or change your application's port.

### 1. Identify the Culprit Process

Find out which process is currently listening on the port your Node.js application wants to use. Replace `YOUR_PORT` with the actual port (e.g., 3000, 8080).

#### On macOS/Linux:

Use `lsof -i tcp:YOUR_PORT`. The output will show the process ID (PID).

```bash
lsof -i tcp:3000
```

Example output:
```
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
node    12345 amara   20u  IPv4 0x...      0t0  TCP *:3000 (LISTEN)
```
Here, `PID 12345` is the process you're targeting.

#### On Windows (Command Prompt/PowerShell):

**Command Prompt:**
```cmd
netstat -aon | findstr :YOUR_PORT
```
Example for port `3000`:
```cmd
netstat -aon | findstr :3000
```
Example output, the last column is the PID:
```
  TCP    0.0.0.0:3000           0.0.0.0:0              LISTENING       12345
```

**PowerShell:**
```powershell
Get-NetTCPConnection -LocalPort YOUR_PORT | Select-Object OwningProcess, State
```
Example for port `3000`:
```powershell
Get-NetTCPConnection -LocalPort 3000 | Select-Object OwningProcess, State
```
Example output:
```
OwningProcess State
------------- -----
        12345 Listen
```

### 2. Terminate the Culprit Process

Once you have the PID, you can terminate the process. **Use caution:** ensure you are killing the correct process. If it's a critical system service, changing your application's port might be safer.

#### On macOS/Linux:

Use `kill -9 YOUR_PID` to forcefully terminate the process.

```bash
kill -9 12345
```

#### On Windows:

**Command Prompt:**
```cmd
taskkill /PID YOUR_PID /F
```
The `/F` flag forces termination.
```cmd
taskkill /PID 12345 /F
```

**Task Manager:**
Alternatively, open Task Manager (Ctrl+Shift+Esc), go to the "Details" tab, sort by "PID", find the process, right-click, and select "End task".

### 3. Verify the Port is Free

After termination, rerun the identification command (`lsof`, `netstat`, `Get-NetTCPConnection`). If it returns no results for your port, the port is free. You can now restart your Node.js application.

### 4. Change Your Application's Port (Alternative)

If the conflicting process is a legitimate service you cannot or should not terminate, configure your Node.js application to use a different port. Common alternatives for development are `3001`, `8000`, `8081`, `4000`, `5000`.

Most Node.js applications read the port from an environment variable (often `PORT`).

```javascript
const port = process.env.PORT || 3000; // Use PORT env variable, or default to 3000
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
```
To run your app on a different port:

#### On macOS/Linux:
```bash
PORT=3001 npm start
```

#### On Windows (Command Prompt):
```cmd
set PORT=3001 && npm start
```

#### On Windows (PowerShell):
```powershell
$env:PORT=3001; npm start
```

### 5. Implement Graceful Shutdown (Prevention)

To prevent `EADDRINUSE` from ghost processes, ensure your Node.js application shuts down gracefully. Listen for termination signals (`SIGINT`, `SIGTERM`) and close the server connection before exiting.

```javascript
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

const server = app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});

const shutdown = (signal) => {
  console.log(`${signal} received: closing HTTP server`);
  server.close(() => {
    console.log('HTTP server closed.');
    process.exit(0);
  });
};

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
```

## Code Examples

Here are concise, copy-paste ready examples.

### Basic Node.js HTTP Server with EADDRINUSE Error Handling

```javascript
// server.js
const http = require('http');

const hostname = '127.0.0.1';
const port = 3000; // This port might be in use

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Hello World\n');
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`ERROR: Port ${port} is already in use.`);
    console.error('Please try another port or terminate the conflicting process.');
    process.exit(1); // Exit with an error code
  } else {
    console.error(`Server encountered an unexpected error: ${err.message}`);
    process.exit(1);
  }
});
```

### Express.js Server Using Environment Variable for Port

```javascript
// app.js
const express = require('express');
const app = express();

const port = process.env.PORT || 8080; // Default to 8080 if PORT env variable is not set

app.get('/', (req, res) => {
  res.send('Hello from Express!');
});

app.listen(port, () => {
  console.log(`Express server listening on port ${port}`);
});
```
To run this using port `4000`:
`PORT=4000 node app.js` (Linux/macOS)
`set PORT=4000 && node app.js` (Windows cmd)
`$env:PORT=4000; node app.js` (Windows PowerShell)

## Environment-Specific Notes

While troubleshooting steps are similar, their application varies by environment.

*   **Local Development:** `EADDRINUSE` is most common here. `lsof` and `netstat` are essential. Solutions usually involve killing a runaway process or simply changing your app's port. A quick `killall node` (on macOS/Linux, use with caution) or restarting your machine can often clear lingering Node.js processes.

*   **Docker:** In Docker, `EADDRINUSE` usually means one of two things:
    1.  **Container Port Conflict:** Less common; your app within the container tries to bind to a port already in use *inside that container's network namespace*. This suggests multiple services within one container using the same port (an anti-pattern).
    2.  **Host Port Conflict:** More common; when mapping host port to container port (`-p host_port:container_port`), `host_port` is already in use *on your host machine* (by another Docker container or a non-Docker app). To troubleshoot, check `lsof` or `netstat` on your host for `host_port`. If another container uses it, `docker ps` to identify, then `docker stop <container_id>` or `docker rm <container_id>` to free the port. I've seen this in production when a CI/CD pipeline failed to clean up a test container, causing conflicts on the build agent.

*   **Cloud (AWS EC2, Google Cloud, Azure VMs):** For Node.js on a VM, troubleshooting is like local development. SSH into the VM and use `lsof` or `netstat`. `EADDRINUSE` typically indicates a failed deployment leaving an old instance, multiple instances launched on the same VM, or another VM service using the port. Ensure robust deployment scripts with graceful shutdowns and process managers (`pm2`, `systemd`).

*   **Cloud PaaS (Heroku, Vercel, Render, AWS Lambda, Google Cloud Functions):** You generally won't encounter `EADDRINUSE` at the OS level directly. These platforms abstract port management. If an `EADDRINUSE`-like error occurs, it usually means your application code is hardcoding a port that the PaaS platform doesn't allow or that conflicts with its internal proxies. Most PaaS platforms inject the required `PORT` via an environment variable (`process.env.PORT`) that your application *must* use.

## Frequently Asked Questions

**Q: Can two different applications use the same port?**
**A:** No, not on the same IP address. Only one process can bind to a specific port at a time. Attempting to bind a second process will result in `EADDRINUSE`.

**Q: How do I find out which process is using a port on Windows?**
**A:** Use `netstat -aon | findstr :YOUR_PORT` in Command Prompt or `Get-NetTCPConnection -LocalPort YOUR_PORT | Select-Object OwningProcess, State` in PowerShell to find the process ID (PID).

**Q: Why does `kill -9` sometimes not work, or the process restarts?**
**A:** If a process immediately restarts after `kill -9`, it's likely managed by a process manager (like PM2, `systemd`, `forever`, etc.) that detects its termination and relaunches it. In such cases, you need to stop the *manager* process or the service itself, not just the child.

**Q: Is it safe to `kill -9` any process I find?**
**A:** `kill -9` is a forceful termination; it prevents the process from cleaning up or saving state. While generally safe for your own development server, exercise caution with system processes or critical applications, as misuse can lead to data loss or instability. Always identify the process carefully.

**Q: What are common default ports I should avoid for my Node.js app?**
**A:** Avoid well-known system ports (0-1023) like 22 (SSH), 80 (HTTP), 443 (HTTPS), 3306 (MySQL), 5432 (PostgreSQL), 27017 (MongoDB). Other common development ports that frequently cause conflicts include 3000, 4200, 5000, 8000, 8080. If you pick one of these, be prepared for potential conflicts.

## Related Errors
- [linux-address-in-use](/errors/linux-address-in-use.html)
- [docker-port-already-allocated](/errors/docker-port-already-allocated.html)