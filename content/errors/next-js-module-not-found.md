# Next.js Module not found: Can't resolve 'X'
> Encountering "Module not found: Can't resolve 'X'" means Next.js cannot locate an imported dependency; this guide explains how to fix it with practical steps.

## What This Error Means

When Next.js throws a "Module not found: Can't resolve 'X'" error, it indicates that the Webpack compiler, which Next.js uses internally, failed to locate a module or file that you're attempting to import. The 'X' in the error message will be the specific path or package name that could not be resolved. This can happen during `npm run dev` (development server), `npm run build` (production build), or `npm run start` (production server runtime if the module is dynamically imported server-side).

Essentially, your code is asking for something that isn't where Next.js expects it to be, or perhaps doesn't exist at all within the project's accessible paths. It's a critical error because the application cannot compile or run without all its required modules.

## Why It Happens

Module resolution is a core part of how JavaScript applications work, especially in environments like Node.js and client-side bundlers like Webpack. When you write `import SomeModule from 'path/to/SomeModule'` or `import SomePackage from 'some-package'`, the module resolver follows a set of rules to find that module.

For local files, it looks at relative paths (`./`, `../`) or absolute paths defined by configuration (like `baseUrl` or `paths` in `tsconfig.json`/`jsconfig.json`). For installed packages, it typically checks the `node_modules` directory, searching for the package name and then its entry point (defined in the package's `package.json`).

This error occurs when one of these resolution attempts fails. In my experience, it's often a simple oversight, but it can sometimes point to more complex configuration issues, especially in larger projects or monorepos.

## Common Causes

Based on my experience as a Platform Engineer, these are the most frequent reasons I've encountered for the "Module not found" error in Next.js applications:

1.  **Typos in Import Paths or Package Names:** The most straightforward cause. A misspelled filename, directory name, or package name will prevent the resolver from finding the target.
2.  **Missing or Uninstalled Node Module:** If you `import 'some-package'` but `some-package` isn't listed in your `package.json` dependencies or hasn't been installed (e.g., `npm install` or `yarn install` wasn't run), Next.js won't find it in `node_modules`.
3.  **Incorrect Relative Paths:** Misjudging the current file's location relative to the imported file (e.g., `../` vs `./` vs `../../`). This is particularly common when refactoring files.
4.  **Absolute Path Configuration Issues:** If you're using absolute imports (e.g., `import Button from '@/components/Button'`), the aliases defined in `tsconfig.json` (for TypeScript) or `jsconfig.json` (for JavaScript) might be incorrect, missing, or not correctly understood by Next.js.
5.  **Case Sensitivity Mismatches:** File systems on macOS and Windows are often case-insensitive by default, while Linux (common in CI/CD, Docker, and production servers) is case-sensitive. `components/Button.tsx` and `Components/Button.tsx` are different files on Linux. If your local dev environment tolerates `import Button from './components/button'`, but the actual file is `Button.tsx`, it will break in a Linux build environment. This is a classic "works on my machine" scenario.
6.  **Caching Issues:** Sometimes, stale caches (`.next/`, `node_modules/`) can confuse the module resolver, especially after adding new dependencies or refactoring.
7.  **Monorepo / Workspace Complications:** In a monorepo, packages might be symlinked. If the root `node_modules` isn't correctly structured or `next.config.js` isn't configured with `transpilePackages` for local packages, Next.js might fail to resolve or transpile modules.
8.  **Client-side Import of Node.js-only Modules:** Next.js uses Webpack to bundle client-side code. If you try to `import 'fs'` (Node.js File System module) directly into a component rendered on the client, Webpack will fail because 'fs' is not available in the browser environment.
9.  **Next.js Specific `transpilePackages` or `serverComponentsExternalPackages` Misconfiguration:** For packages that need to be transpiled (e.g., ESM-only packages in a CJS context or internal monorepo packages), `transpilePackages` in `next.config.js` is crucial. Similarly, `serverComponentsExternalPackages` helps manage server components.

## Step-by-Step Fix

Here’s my go-to troubleshooting process when I encounter a "Module not found" error:

1.  **Verify the Import Path and Module Name (Critical First Step):**
    *   **Double-check spelling:** Is 'X' in the error message exactly what you intended to import?
    *   **Relative vs. Absolute:** If it's a relative path (e.g., `./components/Button`), manually trace the path from the importing file to the target file. Ensure all slashes and directory names are correct. If it's an absolute path (e.g., `@/components/Button`), verify the alias configuration (see step 4).
    *   **Case Sensitivity:** Ensure the casing of the import path exactly matches the actual file/folder names on disk. This is especially important if you're developing on macOS/Windows and deploying to Linux.

2.  **Check `package.json` and `node_modules`:**
    *   If 'X' is a third-party package name (e.g., `lodash`, `react-query`), confirm it's listed under `dependencies` or `devDependencies` in your `package.json`.
    *   If it is, try re-installing your dependencies:
        ```bash
        # For npm
        rm -rf node_modules
        npm install

        # For yarn
        rm -rf node_modules
        yarn install

        # For pnpm (if applicable)
        pnpm recursive install # or pnpm install -r
        ```
    *   After installation, verify that the package's folder exists in `node_modules/X`.

3.  **Clear Next.js and Node Caches:**
    *   Stale build artifacts or module caches can sometimes cause these issues.
    *   Stop your development server (`Ctrl+C`).
    *   Remove the Next.js build cache and `node_modules`:
        ```bash
        rm -rf .next
        rm -rf node_modules
        ```
    *   Reinstall dependencies and restart the development server:
        ```bash
        npm install # or yarn install / pnpm install
        npm run dev
        ```

4.  **Review `tsconfig.json` / `jsconfig.json` for Path Aliases:**
    *   If you're using absolute imports (e.g., `import MyComponent from '@/components/MyComponent'`), ensure your `baseUrl` and `paths` are correctly configured.
    *   For TypeScript, open `tsconfig.json`. For JavaScript, open `jsconfig.json`.
    *   Look for the `compilerOptions` section:
        ```json
        {
          "compilerOptions": {
            "baseUrl": ".", // This usually means root of your project
            "paths": {
              "@/*": ["./*"], // This maps "@/" to your project root
              "@components/*": ["components/*"] // Example for specific alias
            }
          }
        }
        ```
    *   Adjust `baseUrl` and `paths` to correctly point to your desired directories. I've often seen `baseUrl` pointing to `src` while imports were trying to resolve from root, causing confusion.

5.  **Examine `next.config.js`:**
    *   If you're dealing with a monorepo, an external UI library, or packages that need specific Webpack treatment, `transpilePackages` might be necessary.
    *   ```javascript
        /** @type {import('next').NextConfig} */
        const nextConfig = {
          reactStrictMode: true,
          transpilePackages: ['some-ui-library', 'my-local-package'], // Add packages here
          // ... other configs
        };

        module.exports = nextConfig;
        ```
    *   If you're importing a Node.js-only module in a Server Component, you might need to externalize it or mark it for specific handling using `serverComponentsExternalPackages`.

6.  **Identify Node.js Built-in Module Imports:**
    *   If 'X' is a Node.js built-in module like `fs`, `path`, `crypto`, `http`, and the error occurs in a client-side component, it means you're trying to use server-only functionality in the browser.
    *   **Solution:**
        *   Move the logic that uses these modules to an API route, a server component, or a server-side utility function.
        *   If the module has a browser-compatible polyfill, consider using that (though this is less common with Next.js's server-side rendering).
        *   Use dynamic imports (`await import('...')`) with `ssr: false` to ensure it's only loaded client-side *if* a polyfill exists or if the browser environment supports it.

7.  **Restart Your Development Server:** After making any changes, always restart your development server (`npm run dev`) to ensure Webpack recompiles with the new configurations.

## Code Examples

Here are some concise, copy-paste ready examples for common scenarios:

**1. Correct Relative Import:**
Suppose you have `pages/index.tsx` and `components/Button.tsx`.
`pages/index.tsx`:
```typescript
import Button from '../components/Button'; // Correct relative path from pages/ to components/

export default function HomePage() {
  return <Button>Click me</Button>;
}
```

**2. Absolute Import with `tsconfig.json`:**
To enable imports like `import Button from '@/components/Button';`
`tsconfig.json`:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"] // Maps @/ to the project root
    },
    // ... other compiler options
  },
  // ...
}
```
`pages/index.tsx`:
```typescript
import Button from '@/components/Button'; // Assuming components/Button.tsx exists at project root/components/Button.tsx

export default function HomePage() {
  return <Button>Click me</Button>;
}
```

**3. `next.config.js` for Transpiling Local Packages (Monorepo):**
If `my-local-package` is a package within your monorepo that Next.js needs to transpile.
`next.config.js`:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['my-local-package'],
};

module.exports = nextConfig;
```

**4. Handling Node.js Built-in Modules on the Server:**
If you need to read a file, do it in a server component or API route.
`app/page.tsx` (Server Component):
```typescript
import { promises as fs } from 'fs'; // This import will only run on the server

export default async function HomePage() {
  let content = '';
  try {
    content = await fs.readFile(process.cwd() + '/public/data.txt', 'utf8');
  } catch (error) {
    console.error('Failed to read file:', error);
  }

  return (
    <div>
      <h1>File Content:</h1>
      <pre>{content}</pre>
    </div>
  );
}
```

## Environment-Specific Notes

The "Module not found" error can manifest differently or be caused by unique factors depending on your deployment environment.

*   **Local Development:** This is where you'll typically first encounter the error due to typos, new package installations, or minor path changes. The key here is quick iteration: restarting the dev server, clearing caches (`.next`, `node_modules`), and double-checking file paths and `tsconfig.json`. Case sensitivity is less of an issue here unless you've configured your local system to be case-sensitive.

*   **Docker Containers:** When building or running Next.js in a Docker container, I've seen this error primarily because:
    *   **Incorrect `COPY` instructions in Dockerfile:** `node_modules` might not be copied correctly, or the build context might be wrong. Ensure your `COPY . .` happens *after* `npm install` and that your `.dockerignore` isn't inadvertently excluding essential files or directories.
    *   **Different OS:** The Docker image likely runs Linux. This makes case sensitivity a significant factor if your local development was on macOS or Windows. Always match case precisely.
    *   **Build-time vs. Runtime:** Some modules might resolve fine during `npm run build` in a builder stage but then fail at runtime if the runtime image doesn't have the necessary dependencies or environment variables.

*   **Cloud Platforms (Vercel, AWS Amplify, Netlify):** These platforms often abstract away much of the build environment, but they run on Linux-based systems.
    *   **Case Sensitivity:** This is the most common culprit when "it works on my machine" but fails in CI/CD.
    *   **Build Command Issues:** Ensure your build command (`next build`) runs successfully and that all dependencies are installed. Sometimes platforms use `yarn` by default, but your project might expect `npm`. Configure the correct package manager if necessary.
    *   **Monorepo Configuration:** For Vercel, ensuring your project root and included files are correctly configured in `vercel.json` or the Vercel UI is crucial, especially for monorepos where Next.js apps might be nested. Similarly for AWS Amplify, ensuring correct build settings and artifact paths is key.
    *   **Environment Variables:** If a module's resolution depends on an environment variable (e.g., for conditional imports or pathing), ensure that variable is correctly set in the cloud build environment.

## Frequently Asked Questions

**Q: Why does my project build locally but fail with "Module not found" in CI/CD?**
**A:** This is almost always a case sensitivity issue or a difference in the build environment. Locally, your file system might be case-insensitive, but CI/CD environments (typically Linux) are case-sensitive. Double-check all file and directory names in your import paths for exact case matches. Also, ensure all `node_modules` are correctly installed in the CI/CD pipeline, and clear any potential caches.

**Q: What if 'X' is a CSS, SCSS, or image file?**
**A:** If it's a styling or asset file, the "Module not found" error usually indicates a wrong path or a missing Webpack loader configuration.
*   **Path:** Verify the import path is correct, just like for JavaScript/TypeScript files.
*   **Loader:** Ensure you have the necessary Next.js configuration or Webpack loaders (e.g., `sass` for SCSS, `css` for CSS, Next.js handles images by default but `next/image` requires specific setup). For example, `npm install sass` is needed for SCSS.

**Q: How do `baseUrl` and `paths` work together in `tsconfig.json` / `jsconfig.json`?**
**A:** `baseUrl` defines the base directory from which all non-relative module imports are resolved. `paths` allows you to create aliases that map specific module names or patterns to a set of locations, relative to the `baseUrl`. For example, `baseUrl: "./"` and `paths: { "@/*": ["src/*"] }` would mean `import Some from '@/util/Some'` would look for `src/util/Some` from the project root.

**Q: Can this error be related to `next.config.js`?**
**A:** Absolutely. As mentioned, `transpilePackages` is crucial for monorepos or specific packages. Additionally, custom Webpack configurations within `next.config.js` (`webpack` function) can inadvertently break module resolution if not handled carefully. For instance, modifying default resolution rules can lead to conflicts.

**Q: I'm getting "Module not found: Can't resolve 'fs'" (or similar Node.js modules) in a client-side component. How do I fix this?**
**A:** This means you're trying to import a Node.js built-in module, like the file system (`fs`), directly into code that Next.js intends to run in the browser. These modules are not available in browser environments. You must move any logic using these modules to server-side code (e.g., API routes, server components, or `getServerSideProps`/`getStaticProps`).

## Related Errors
*   [typescript-ts2307](/errors/typescript-ts2307.html)