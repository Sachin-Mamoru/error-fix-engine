# SSL certificate error: self-signed certificate in certificate chain
> Encountering "self-signed certificate in certificate chain" means your system doesn't trust the SSL certificate; this guide explains how to fix it.

As a Cloud & DevOps Engineer, I've run into the "self-signed certificate in certificate chain" error more times than I can count. It's a common snag, especially when dealing with internal services, development environments, or tightly controlled corporate networks. While the message itself points to a security measure doing its job, understanding its root causes and how to properly address it is key to unblocking your work without compromising security.

### What This Error Means

At its core, this error signifies a breakdown in the chain of trust for an SSL/TLS certificate. When your client (be it a web browser, `curl` command, Git client, or an application) attempts to establish an HTTPS connection, the server presents its SSL certificate. The client then tries to verify this certificate by tracing its lineage back to a Certificate Authority (CA) that it implicitly trusts.

The "self-signed certificate in certificate chain" message specifically means that during this verification process, the client encountered a certificate that was signed by itself, rather than by a recognized and trusted third-party CA. Furthermore, this self-signed certificate (or the CA that signed it) is *not* present in your client's list of trusted root certificates. Without a verifiable path to a trusted root, the client cannot confirm the identity of the server and, by default, assumes the connection is not secure, thus aborting it with this error.

It’s crucial to understand that not all self-signed certificates are inherently bad or malicious. Many legitimate internal systems use them. The issue arises when your client's system doesn't have prior knowledge or trust in that specific self-signed certificate.

### Why It Happens

This error primarily occurs because the client's system (whether it's an operating system's CA store, a specific application's trust store, or even a browser's built-in list) does not recognize or trust the issuer of the server's SSL certificate.

Here's the sequence of events that leads to this:
1.  **Server Presentation:** A server (e.g., a web server, API endpoint, Git repository) presents an SSL certificate during the TLS handshake.
2.  **Client Verification:** Your client application receives this certificate. It then looks at the "Issuer" field of the certificate to find out who signed it.
3.  **Chain Building:** If the issuer is an intermediate CA, the client expects the server to also provide the intermediate CA's certificate. This process continues, building a "chain" of certificates, until it reaches a root CA.
4.  **Trust Check:** The client then checks if this root CA (or any certificate in the chain) is present in its own local store of trusted root CAs.
5.  **Failure Point:** If the certificate presented by the server is self-signed, and that self-signed certificate is *not* in the client's trusted store, or if an intermediate certificate in the chain is self-signed and untrusted, the trust verification fails.

The 'why' is ultimately about security. Operating systems and applications maintain a curated list of well-known and trusted CAs (like DigiCert, Let's Encrypt, GlobalSign, etc.). These CAs undergo rigorous audits and security practices. If a certificate isn't signed by one of these trusted entities, the client cannot guarantee that it's connecting to the legitimate server and not an imposter attempting a Man-in-the-Middle (MITM) attack.

### Common Causes

Based on my experience in various environments, here are the most common scenarios that lead to the "self-signed certificate in certificate chain" error:

*   **Development and Testing Environments:** This is perhaps the most frequent culprit. For local development servers, internal APIs, or non-production test environments, developers often generate self-signed certificates to enable HTTPS without the cost or complexity of obtaining publicly trusted certificates. My first thought when I see this error is often "Is this a dev server?"
*   **Internal Corporate Services:** Many organizations run internal applications, Git repositories (like GitLab or GitHub Enterprise instances), or artifact repositories (like Artifactory or Nexus) that are not exposed to the public internet. These services often use certificates issued by the company's internal Certificate Authority (PKI) or even directly self-signed certificates. If your client machine isn't configured to trust the corporate CA, you'll hit this error.
*   **SSL Interception Proxies (Man-in-the-Middle by Design):** In enterprise networks, it's common for security appliances (like firewalls or proxies) to perform "SSL inspection." This involves decrypting HTTPS traffic, inspecting it for threats, and then re-encrypting it before sending it to the destination. During re-encryption, the proxy presents its own certificate, often issued by an internal CA that isn't trusted by default by client machines. I've seen this in production when engineers connect to external services via the corporate network.
*   **Misconfigured Servers or Incomplete Certificate Chains:** Sometimes, the server itself is misconfigured. While it might have a valid certificate issued by a trusted CA, it might fail to send the entire certificate chain (i.e., missing intermediate CA certificates) during the TLS handshake. When the client receives only the server's end-entity certificate and can't build the chain back to a trusted root, it can sometimes present as a self-signed error.
*   **Outdated Client CA Bundles:** Less common now with modern operating systems and browsers, but possible with older systems or specialized tools. If the client's trusted CA bundle is outdated, it might not recognize newer root CAs, leading to validation failures.
*   **Containerized Applications:** When working with Docker or Kubernetes, a container might not inherit the host's trusted CA store. If an application inside a container tries to connect to a service using a self-signed or internal corporate certificate, the container itself needs to be explicitly configured to trust that certificate.

### Step-by-Step Fix

Addressing this error typically involves one of two main approaches: either configuring the server with a trusted certificate or configuring the client to trust the existing certificate.

1.  **Identify the Untrusted Certificate:**
    The first step is always to understand *which* certificate is causing the problem and who issued it.
    ```bash
    openssl s_client -showcerts -connect your.server.com:443 </dev/null
    ```
    Look for the `s: /CN=your.server.com` (subject) and `i: /CN=Self-Signed-CA` (issuer) lines. This will show you the certificate chain and reveal if it's self-signed or issued by an unfamiliar entity.

2.  **Option A: Replace the Server Certificate with a Trusted One (Recommended for Public-Facing Services)**
    If `your.server.com` is publicly accessible, this is the most secure and universally accepted solution.
    *   **Commercial CA:** Purchase an SSL certificate from a commercial Certificate Authority (e.g., DigiCert, Sectigo).
    *   **Let's Encrypt:** For free, automated certificates, use Let's Encrypt with a tool like `certbot`. This is an excellent option for most public-facing web services.
    *   **Internal PKI:** If it's an internal service within an organization, use your company's own Public Key Infrastructure to issue a certificate. Ensure client machines are configured to trust the corporate root CA.

3.  **Option B: Configure Your Client to Trust the Self-Signed Certificate (For Internal/Dev Environments - Use with Caution)**
    This approach tells your client to explicitly trust the self-signed certificate. It's suitable for controlled environments where you understand and accept the risks.

    *   **System-Wide Trust (Operating System):**
        *   **Linux (Debian/Ubuntu-based):**
            First, obtain the public key of the self-signed CA certificate (e.g., `ca-cert.crt`). You can often extract this from the `openssl s_client` output or get it from the server administrator.
            ```bash
            sudo cp ca-cert.crt /usr/local/share/ca-certificates/
            sudo update-ca-certificates
            # Verify it's added
            grep "ca-cert.crt" /etc/ca-certificates.conf
            ```
            For RedHat/CentOS: `sudo cp ca-cert.crt /etc/pki/ca-trust/source/anchors/ && sudo update-ca-trust extract`
        *   **Windows:**
            Open `certmgr.msc`, navigate to "Trusted Root Certification Authorities" -> "Certificates," then right-click -> "All Tasks" -> "Import..." and follow the wizard to import your `ca-cert.crt` file.
        *   **macOS:**
            Open "Keychain Access," select the "System" keychain, drag and drop your `ca-cert.crt` file into the window. Double-click the imported certificate and change its trust settings to "Always Trust."

    *   **Application-Specific Trust:**
        Sometimes, you only need to tell a specific application to trust a certificate, without modifying the entire system's trust store.

        *   **`curl`:**
            ```bash
            curl --cacert /path/to/ca-cert.crt https://your.server.com/api
            ```
            Alternatively, for quick debugging (NOT recommended for production or scripts):
            ```bash
            curl -k https://your.server.com/api # -k or --insecure ignores SSL verification
            ```
        *   **Git:**
            To trust a specific CA for Git operations:
            ```bash
            git config --global http.sslCAInfo /path/to/ca-cert.crt
            ```
            To disable SSL verification globally (use only in *very* controlled dev environments):
            ```bash
            git config --global http.sslVerify false
            ```
        *   **Python `requests` library:**
            ```python
            import requests
            response = requests.get('https://your.server.com/api', verify='/path/to/ca-cert.crt')
            # To disable (DANGEROUS!):
            # response = requests.get('https://your.server.com/api', verify=False)
            ```
        *   **Node.js (for `https.request` or similar):**
            ```javascript
            const https = require('https');
            const fs = require('fs');

            const options = {
              hostname: 'your.server.com',
              port: 443,
              path: '/',
              method: 'GET',
              ca: fs.readFileSync('/path/to/ca-cert.pem') // Provide CA certificate
            };

            const req = https.request(options, (res) => {
              // ...
            });
            req.end();
            ```
            For `NODE_TLS_REJECT_UNAUTHORIZED=0` (DANGEROUS!):
            `NODE_TLS_REJECT_UNAUTHORIZED=0 node your_script.js`

### Code Examples

Here are some concise, copy-paste-ready code snippets to handle this error in various contexts.

**1. Inspecting a Server's Certificate Chain**
```bash
openssl s_client -showcerts -connect your.server.com:443 </dev/null
```

**2. Adding a CA Certificate to Debian/Ubuntu System-Wide**
```bash
# Assuming ca-cert.crt is the public key of your self-signed CA
sudo cp ca-cert.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

**3. Using `curl` with a Specific CA Certificate**
```bash
curl --cacert /path/to/my_trusted_ca.crt https://my-internal-api.com/data
```

**4. Temporarily Ignoring SSL Verification with `curl` (Development ONLY!)**
```bash
curl -k https://my-dev-server.com/test
```

**5. Configuring Git to Trust a Specific CA Certificate**
```bash
git config --global http.sslCAInfo /path/to/my_trusted_ca.crt
```

**6. Python `requests` with a Specific CA Certificate**
```python
import requests

try:
    response = requests.get('https://my-internal-service.com/status', verify='/path/to/my_trusted_ca.pem')
    print(f"Status: {response.status_code}")
except requests.exceptions.SSLError as e:
    print(f"SSL Error: {e}")
```

**7. Python `requests` ignoring SSL verification (Development ONLY!)**
```python
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # Suppress warnings

try:
    response = requests.get('https://my-dev-server.com/data', verify=False)
    print(f"Status: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
```

### Environment-Specific Notes

The context in which you encounter this error often dictates the best approach to fix it.

*   **Cloud (AWS, Azure, GCP):**
    *   **Load Balancers:** If you're using an Application Load Balancer (ALB) on AWS, Azure Application Gateway, or Google Cloud Load Balancing, ensure the SSL certificate configured on the load balancer itself is valid and trusted. If the LB terminates SSL, that's the certificate clients see. If the LB passes through SSL, the backend service's certificate is what matters. In my experience, forgetting to update certificates on ALBs is a common cause for production outages.
    *   **Kubernetes (EKS, AKS, GKE):** Inside a Kubernetes cluster, pods might need to trust internal services or image registries. If a pod uses `curl` or `wget` or any HTTP client, it will use the CA bundle available *inside* the container. You'll need to create a `ConfigMap` for your CA certificate and mount it into your pods, then configure your applications or the container's OS to trust it. For ingress, `cert-manager` is an excellent tool to automate certificate lifecycle with Let's Encrypt or your internal CA.
    *   **CI/CD Pipelines:** Jenkins, GitLab CI, GitHub Actions runners often execute commands that interact with internal services (e.g., private artifact repositories, internal Git servers). If these services use self-signed certificates, the CI/CD agent's environment needs to be configured to trust them, usually by adding the CA certificate to the system's trusted store within the runner's execution context.

*   **Docker/Containers:**
    *   **Building Images:** If your `Dockerfile` includes commands like `RUN apt-get update && apt-get install ...` or `RUN curl ...` that connect to HTTPS endpoints with self-signed certs, the build process will fail. You need to include the CA certificate in the Docker image during the build process.
        ```dockerfile
        FROM debian:stable
        COPY ca-cert.crt /usr/local/share/ca-certificates/ca-cert.crt
        RUN update-ca-certificates
        # Now subsequent curl/wget commands inside the Dockerfile will trust it
        ```
    *   **Running Containers:** If a running container needs to access internal services with self-signed certs, the same logic applies. Ensure the container has the necessary CA certificates installed or mounted.
    *   **Docker Daemon/Registry:** If you are running a private Docker registry with a self-signed certificate, the Docker daemon itself needs to be configured to trust it. You can do this by adding the CA certificate to `/etc/docker/certs.d/your.registry.com:port/ca.crt` on the Docker host, or by adding the registry to the "insecure-registries" list in `/etc/docker/daemon.json` (less secure).

*   **Local Development:**
    *   **Browser Warnings:** When accessing a local dev server with a self-signed certificate, your browser will show a severe warning (e.g., `NET::ERR_CERT_AUTHORITY_INVALID`). You can usually proceed by clicking "Advanced" and "Proceed to..." but this is not a permanent fix.
    *   **Tools like `mkcert`:** For local development, `mkcert` is a fantastic tool that generates locally-trusted SSL certificates. It installs a local CA into your system's trust store, then uses that CA to sign certificates for your `localhost` domains, making your browser happy without security compromises. It's what I personally use for most of my local dev setups.

### Frequently Asked Questions

**Q: Is it safe to ignore SSL certificate errors by using flags like `-k` or `verify=False`?**
**A:** Generally, no. Ignoring SSL certificate errors disables a fundamental security mechanism. It leaves you vulnerable to Man-in-the-Middle attacks where an attacker could intercept and read/modify your encrypted traffic. Only use these options in tightly controlled development or testing environments where you fully understand the implications and risks, and *never* in production.

**Q: How do I get a trusted certificate for my server?**
**A:** For public-facing services, the most common and recommended way is to use Let's Encrypt, which provides free, automated, and publicly trusted certificates. For commercial certificates with extended validation or warranty, you can purchase them from commercial Certificate Authorities like DigiCert, Sectigo, or GlobalSign. For internal corporate services, use your organization's internal PKI.

**Q: My browser shows the error, but `curl` works fine. Why?**
**A:** This often happens because your browser and `curl` might be using different CA trust stores. Browsers typically use the operating system's trust store (or their own built-in one), while `curl` might be configured to use a different bundle (e.g., `/etc/ssl/certs/ca-certificates.crt` on Linux) or might even have a default configuration that's less strict or has been explicitly told to trust your certificate via `--cacert` or `http.sslCAInfo`.

**Q: What's the difference between a "self-signed" certificate and an "untrusted" certificate?**
**A:** A "self-signed" certificate is one where the certificate's issuer is the same as its subject (it signed itself). An "untrusted" certificate is any certificate that a client cannot validate back to a known and trusted root Certificate Authority. All self-signed certificates are untrusted *by default* unless their public key has been explicitly added to the client's trust store. Conversely, a certificate issued by a well-known CA can also become untrusted if the client's CA bundle is outdated and doesn't contain that CA's root, or if the full certificate chain is not provided by the server.

**Q: How do I manage certificates in a large enterprise environment?**
**A:** Large enterprises typically employ an internal Public Key Infrastructure (PKI) to issue and manage certificates for internal services. Client machines are usually configured via Group Policy (Windows) or MDM solutions (macOS, Linux) to automatically trust the enterprise's root CA. Tools like `cert-manager` in Kubernetes or centralized certificate management platforms also help automate lifecycle management, ensuring certificates are renewed before expiry and trusted across the infrastructure.

### Related Errors

*   [git-permission-denied-publickey](/errors/git-permission-denied-publickey.html)