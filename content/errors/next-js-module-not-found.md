# Next.js Module not found: Can't resolve 'X'
> Encountering "Module not found: Can't resolve 'X'" in Next.js indicates a problem with locating an imported dependency during build or runtime; this guide explains how to diagnose and fix it.

## What This Error Means

When you encounter the "Module not found: Can't resolve 'X'" error in a Next.js application, it signifies that the underlying JavaScript bundler (Webpack or Turbopack) is unable to locate a file or package that your code is attempting to import. The 'X' in the error message is a placeholder for the actual module name or path that the bundler failed to resolve.

This error typically manifests in two primary contexts:
1.  **During Build (`next build`):** The most common scenario. The bundler scans your project, creates the optimized production bundles, and fails because it cannot find a necessary dependency. This prevents your application from being built and deployed.
2.  **During Development (`next dev`):** While less frequent for fundamental path issues (as the dev server often offers more dynamic resolution), it can still occur, particularly if the file system watcher misses changes or there are deep-seated configuration problems. If your development server can't find a module, it usually means your application won't compile and render correctly in the browser.

Essentially, your code has an `import` or `require` statement for 'X', but when the bundler looks for 'X' in all the places it's configured to search (like `node_modules`, specified paths, or relative paths), it comes up empty-handed. This issue must be resolved for your Next.js application to function.

## Why It Happens

At its core, the "Module not found" error stems from a mismatch between where your code expects a module to be and where the bundler actually looks for it. Next.js, leveraging tools like Webpack or Turbopack, follows a specific resolution strategy to find modules. This strategy involves checking relative paths, `node_modules` directories, and any custom aliases or path mappings defined in your project's configuration (e.g., `tsconfig.json` for TypeScript).

When this error appears, it tells me that one of these search avenues has failed. It's not usually a mysterious bug in Next.js itself, but rather a configuration oversight or a mistake in how a dependency is referenced or installed within your project.

I've seen this error pop up in a variety of situations, from simple typos to complex monorepo configurations. The key is to systematically investigate the import path and the environment to pinpoint the exact reason why the module 'X' remains elusive.

## Common Causes

Based on my experience as a Senior Platform Engineer, here are the most common culprits behind the "Module not found: Can't resolve 'X'" error in Next.js applications:

1.  **Missing `node_modules` Dependency:**
    *   **The package isn't installed:** You `import` a package (e.g., `react-icons`) but forgot to run `npm install react-icons` or `yarn add react-icons`.
    *   **Dependency removed:** The package was installed but later removed from `package.json` or accidentally uninstalled.
    *   **Incorrect `package.json` entry:** The package is listed in `devDependencies` but is actually needed at runtime, especially in a production build where `devDependencies` might not be installed.
    *   **Corrupted `node_modules`:** Sometimes, the `node_modules` directory can get into a bad state.

2.  **Incorrect Import Path:**
    *   **Typos:** The most basic but often overlooked cause. A simple misspelling in the module name or path (e.g., `components/buttoon` instead of `components/Button`).
    *   **Case Sensitivity:** File systems on macOS and Linux are case-sensitive, while Windows is generally not. If you develop on Windows and deploy to a Linux-based CI/CD environment or server, `import MyComponent from './mycomponent';` will fail if the actual file is `MyComponent.tsx`.
    *   **Relative Path Issues:** Incorrect `.` or `..` usage when navigating directories. For example, `import Component from '../../utils/helper';` when it should be `../utils/helper`.
    *   **Missing File Extension:** While Next.js often resolves `.js`, `.jsx`, `.ts`, `.tsx`, sometimes an explicit extension is needed, especially for non-standard file types or specific configurations.

3.  **Missing File or Module:**
    *   The file you're trying to import simply doesn't exist at the specified path. This could be due to deletion, misplacement, or incorrect creation.

4.  **TypeScript `tsconfig.json` Misconfiguration:**
    *   **`baseUrl` and `paths`:** If you're using path aliases (e.g., `@/components/Button`), these rely on `tsconfig.json`'s `baseUrl` and `paths` configuration. If these are incorrect or not picked up by the bundler, the aliases won't resolve.
    *   **`include` / `exclude`:** Files might be unintentionally excluded from the TypeScript compilation process, leading to resolution failures.

5.  **Next.js Custom Configuration (`next.config.js`) Issues:**
    *   **Custom Webpack setup:** If you've customized Next.js's Webpack configuration (e.g., adding resolvers, aliases, or loaders), an error in this setup can prevent modules from being found. For instance, I've seen issues when `next-transpile-modules` isn't correctly configured for packages outside the project root.
    *   **Unsupported file types:** If you're importing a non-standard file type (e.g., a specific SVG format or a custom data file) without a corresponding Webpack loader defined, the bundler won't know how to process it.

6.  **Monorepo Complexities:**
    *   In monorepos using tools like Yarn Workspaces or pnpm, packages might not be hoisted correctly, or the linking between workspaces might be broken. This can lead to internal package dependencies not being resolved.

7.  **Build Cache Corruption:**
    *   While less common, sometimes the `.next` build cache or npm/Yarn/pnpm caches can become corrupted, leading to stale resolution information.

## Step-by-Step Fix

When faced with "Module not found: Can't resolve 'X'", a systematic approach is crucial. Here’s the troubleshooting guide I typically follow:

1.  **Identify 'X' Precisely:**
    *   The first and most important step is to carefully read the error message and identify the exact module path or name that Next.js cannot resolve. This is your 'X'. It could be `react-query`, `./components/MyButton`, or `@/lib/api`. Knowing 'X' is half the battle.

2.  **Check for Missing `node_modules` Dependency:**
    *   **Is 'X' a third-party package?** If 'X' looks like a package name (e.g., `axios`, `lodash`, `date-fns`), it's likely a missing dependency.
    *   **Verify installation:**
        ```bash
        # Using npm
        npm ls <your-package-name>
        # Using yarn
        yarn why <your-package-name>
        # Using pnpm
        pnpm why <your-package-name>
        ```
        If the package is not found or shows an incorrect version, install it:
        ```bash
        # For a regular dependency
        npm install <your-package-name>
        # or
        yarn add <your-package-name>
        # or
        pnpm add <your-package-name>

        # For a dev dependency (if needed)
        npm install --save-dev <your-package-name>
        # or
        yarn add --dev <your-package-name>
        # or
        pnpm add --save-dev <your-package-name>
        ```
    *   **Reinstall all dependencies:** Sometimes, `node_modules` can become corrupted.
        ```bash
        rm -rf node_modules
        rm -f package-lock.json # Or yarn.lock / pnpm-lock.yaml
        npm install             # Or yarn / pnpm install
        ```

3.  **Verify Import Path and File Existence:**
    *   **Locate the import statement:** Find where 'X' is being imported in your code.
    *   **Check for typos:** Carefully compare the import path with the actual file/directory name. Look for simple spelling mistakes.
    *   **Case sensitivity:** Ensure the casing of the import path exactly matches the file system's casing. On Linux-based systems (most CI/CD, Docker, cloud environments), `mycomponent.tsx` is different from `MyComponent.tsx`.
    *   **Relative vs. Absolute:** If using a relative path (e.g., `./`, `../`), manually trace the path to ensure it leads to the correct file. If using an absolute path or alias (e.g., `@/components`), refer to step 4.
    *   **Does the file exist?** The simplest check: navigate to the expected file location in your terminal or file explorer. If it's not there, that's your problem.

4.  **Review `tsconfig.json` (for TypeScript Projects):**
    *   If you're using path aliases like `@/components` or `~lib`, these are configured in your `tsconfig.json` under `compilerOptions.baseUrl` and `compilerOptions.paths`.
    *   Ensure `baseUrl` is correctly set (often `.` for the project root).
    *   Verify that `paths` correctly maps your aliases to actual directories.
    *   Example:
        ```json
        // tsconfig.json
        {
          "compilerOptions": {
            "baseUrl": ".",
            "paths": {
              "@/components/*": ["components/*"],
              "@/lib/*": ["lib/*"]
            }
          }
        }
        ```
        If your `components` folder is directly in the project root, this setup maps `@/components/MyComponent` to `./components/MyComponent`. I've often seen `baseUrl` being wrong or `paths` not matching the actual file structure.

5.  **Inspect `next.config.js` for Custom Webpack Configurations:**
    *   If you've customized Next.js's Webpack configuration, review it for any custom resolvers, aliases, or loaders that might be misconfigured or missing.
    *   For example, if you're importing SVGs as React components, you need a specific Webpack rule. If that rule is broken, you might see "Can't resolve 'my-icon.svg'".
    *   Check for packages like `next-transpile-modules` which are used for transpiling packages outside the `node_modules` directory, common in monorepos. An incorrect `transpilePackages` array can lead to this error.

6.  **Clear Next.js and Package Manager Caches:**
    *   Sometimes, stale build artifacts or package manager caches can interfere.
    *   **Delete `.next` folder:** This clears Next.js's build cache.
        ```bash
        rm -rf .next
        ```
    *   **Clean package manager cache (optional but can help):**
        ```bash
        npm cache clean --force # For npm
        # yarn cache clean       # For yarn (older versions)
        # pnpm store prune      # For pnpm
        ```
    *   After clearing, rerun `npm install` (or equivalent) and `next dev` or `next build`.

7.  **Consider Monorepo Specifics:**
    *   If in a monorepo, ensure `package.json` `workspaces` are correctly defined.
    *   Verify that internal packages are properly linked or installed in the root `node_modules`. Sometimes, running `npm install` or `yarn install` at the monorepo root is needed to resolve links.

## Code Examples

Here are some concise, copy-paste ready examples of common fixes:

**1. Installing a Missing Third-Party Package:**

If the error is: `Module not found: Can't resolve 'react-query'`

```bash
# Using npm
npm install @tanstack/react-query
# Using yarn
yarn add @tanstack/react-query
# Using pnpm
pnpm add @tanstack/react-query
```

**2. Correcting a Local Path Typo or Case Mismatch:**

If you have a file `./components/MyButton.tsx` and the error is: `Module not found: Can't resolve './components/mybutton'`

```javascript
// Incorrect import statement
import MyButton from './components/mybutton'; // 'mybutton' is lowercase

// Correct import statement (case-sensitive filename)
import MyButton from './components/MyButton';
```

**3. Configuring `tsconfig.json` for Path Aliases:**

If the error is: `Module not found: Can't resolve '@/lib/utils'` and you want to use absolute imports.

First, ensure your `tsconfig.json` (or `jsconfig.json` for JS projects) is configured:

```json
// tsconfig.json (at your project root)
{
  "compilerOptions": {
    "baseUrl": ".", // Important: this sets the base for your paths
    "paths": {
      "@/components/*": ["components/*"], // Maps @/components to the 'components' folder
      "@/lib/*": ["lib/*"],             // Maps @/lib to the 'lib' folder
      "@/styles/*": ["styles/*"]         // Example for styles
    },
    // ... other compiler options
  },
  // ... other tsconfig options
}
```

Then, use the alias in your code:

```javascript
// src/app/page.tsx or any other file
import { someUtilityFunction } from '@/lib/utils';
import MyHeader from '@/components/Header';
```

## Environment-Specific Notes

The "Module not found" error can behave slightly differently or have unique triggers depending on your environment.

### Local Development (`next dev`)

*   **File System Watchers:** While `next dev` is usually robust, sometimes the file system watcher can miss changes, especially for newly added files or changes in `tsconfig.json`. Restarting the dev server (`npm run dev` or `yarn dev`) often resolves this.
*   **Case Sensitivity:** If developing on Windows, the case-insensitivity of the file system can mask real case errors. The error might not appear until deployment to a Linux-based environment (e.g., CI/CD, Docker, Vercel). Always be explicit with casing.
*   **Hot Module Replacement (HMR):** With HMR, changes are injected without a full refresh. If the error appears after an HMR update but disappears after a full page refresh (or server restart), it might be an HMR-specific issue, though less common for module resolution.

### Build Environment (CI/CD, Vercel, Netlify, etc.)

*   **Fresh Installs:** Cloud build environments typically perform a clean `npm install` (or `yarn`/`pnpm`) from scratch. This means `node_modules` corruption is less likely, but *missing* `dependencies` (especially if they were accidentally in `devDependencies` locally) will be exposed.
*   **Strict `NODE_ENV`:** Build processes usually run with `NODE_ENV=production`. Ensure your `next.config.js` or any conditional logic doesn't inadvertently exclude necessary modules or paths based on this environment variable.
*   **Case Sensitivity:** This is the biggest culprit I've encountered in CI/CD. Developers on Windows create `components/Button.tsx` but import `components/button.tsx`. Their local `next dev` works, but the Linux-based build server fails. Running `git config core.ignorecase false` locally can help detect these issues before pushing to production.
*   **Build Caching:** While CI/CD often builds from scratch, some platforms offer build caching. If `node_modules` or `.next` are cached incorrectly, it can sometimes lead to stale resolution issues. Clearing the build cache on the platform might be necessary.

### Docker Containers

*   **`COPY` and `WORKDIR`:** Ensure your `Dockerfile` correctly copies all necessary source files, `package.json`, and lock files into the container. The `WORKDIR` instruction must also be set correctly, as all subsequent commands (like `npm install`) will run relative to this directory.
    ```dockerfile
    # Example Dockerfile snippet
    WORKDIR /app
    COPY package.json yarn.lock ./
    RUN yarn install --frozen-lockfile
    COPY . . # Copy source code
    RUN yarn build
    ```
    If you forget to `COPY` your `lib` folder, for instance, any imports from `@/lib` will fail inside the container.
*   **Multi-Stage Builds:** In a multi-stage build, be careful not to accidentally exclude necessary files when moving from the build stage to the final runtime stage. Only copy what's absolutely needed, but ensure *all* resolved files from the build step are present.
*   **Node.js Version:** In rare cases, a specific Node.js version might have subtle differences in module resolution or how it interacts with Webpack. Ensure your Docker image uses a Node.js version compatible with your Next.js project.

## Frequently Asked Questions

**Q: The module 'X' exists in my project, and I double-checked the path. Why does it still fail?**
**A:** This usually points to a configuration issue or a cache problem.
1.  **TypeScript `tsconfig.json`:** If using path aliases (e.g., `@/components`), ensure `baseUrl` and `paths` are correctly set and that the alias points to the correct location relative to `baseUrl`.
2.  **Case Sensitivity:** Confirm the import path's casing perfectly matches the file system's casing, especially if you developed on a case-insensitive OS (Windows) and are building on a case-sensitive one (Linux).
3.  **Next.js Cache:** Delete the `.next` directory and `node_modules`, then reinstall dependencies and restart your dev server or rebuild.
4.  **`next.config.js`:** Check if any custom Webpack configuration is interfering with module resolution.

**Q: What if 'X' is a local file (e.g., `./utils/helper.js`), not a package from `node_modules`?**
**A:** Focus on step 3 (`Verify Import Path and File Existence`).
1.  **Exact Path:** Manually trace the `import` path relative to the importing file. Is `.` or `..` used correctly?
2.  **File Existence & Name:** Confirm the file `helper.js` truly exists in the `utils` directory at that exact path, and its name and extension are spelled correctly with the right casing.
3.  **`tsconfig.json` (`paths`):** If you're using an alias (e.g., `@/utils/helper`), ensure your `tsconfig.json` correctly maps `@/utils` to your `utils` directory.

**Q: Does `next.config.js` actually affect this type of error? I thought it was just for server-side configurations.**
**A:** Yes, absolutely. `next.config.js` allows you to customize the underlying Webpack configuration for both client and server bundles. Any modifications you make to Webpack's `resolve` object (e.g., adding `alias` entries, custom `modules`, or `extensions`), or specific `module.rules` for handling different file types (like SVGs or specific CSS preprocessors), can directly cause or fix "Module not found" errors. For instance, if you're using a library that requires specific transpilation (e.g., ES Modules in `node_modules`), you might need `next-transpile-modules` configured in `next.config.js`.

**Q: I'm using TypeScript, and everything works locally with `next dev`, but `next build` fails with this error. What's different?**
**A:** This is a classic symptom of case sensitivity or `tsconfig.json` issues on your build server.
1.  **Case Sensitivity:** Your local Windows machine might tolerate `import styles from './styles.module.css';` even if the file is `Styles.module.css`, but a Linux build server will not. This is the most common reason I've seen.
2.  **`tsconfig.json` differences:** Ensure the build environment is picking up the correct `tsconfig.json` and that all `paths` and `baseUrl` configurations are robust.
3.  **Environmental Variables:** Very occasionally, environment variables present in your local dev setup but absent during build could affect conditional imports or module loading.

## Related Errors