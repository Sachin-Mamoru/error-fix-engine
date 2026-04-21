# TypeScript TS2307: Cannot find module 'X' or its corresponding type declarations
> Encountering TS2307 means TypeScript cannot find a module or its type declarations; this guide explains how to fix it.

## What This Error Means

When TypeScript throws the `TS2307: Cannot find module 'X' or its corresponding type declarations` error, it's telling you that during compilation, it couldn't locate a specific module you're trying to import, nor could it find the necessary type information for that module. This isn't just a runtime warning; it's a compilation stopper, meaning your TypeScript code won't successfully transform into runnable JavaScript until this issue is resolved.

At its core, TypeScript needs to understand the shape of all data and functions it interacts with. When you `import SomeModule from 'X'`, TypeScript looks for two things:
1.  **The module itself:** Typically, this means a `.ts`, `.tsx`, `.js`, or `.jsx` file within your project or a JavaScript package in your `node_modules` directory.
2.  **Its type declarations:** These are usually found in `.d.ts` files, either alongside the module's source or, more commonly for third-party JavaScript libraries, in a separate `@types/X` package.

If either of these components is missing or inaccessible from TypeScript's perspective, compilation fails. In my experience, this error usually surfaces during `npm run build` or when your IDE's language server is actively checking your code.

## Why It Happens

This error fundamentally occurs because TypeScript's compiler cannot resolve the path to the module you're importing, or it can resolve the module but has no type information to validate how you're using it. It's like asking someone to find a book without providing the correct library location or a book that exists but is written in a language they don't understand.

The "why" behind this error can range from straightforward installation oversights to subtle configuration issues within your `tsconfig.json` or project structure. It means TypeScript's module resolution strategy, which dictates how it finds files, has failed for the module named 'X'. It's critical to understand that even if your JavaScript runtime (Node.js, browser) might find the module later, TypeScript's static analysis requires this information *at compile time*.

## Common Causes

Based on years of working with TypeScript projects, I've distilled the common triggers for TS2307 into a few key areas:

1.  **Module Not Installed:** The most frequent culprit. The package 'X' simply hasn't been installed into your `node_modules` directory. This happens if you forget `npm install X` or if `npm install` wasn't run after cloning a repository.
2.  **Missing Type Declarations (`@types`):** Many older or JavaScript-first libraries don't ship with their own TypeScript declaration files (`.d.ts`). For these, you need to install a separate `@types/X` package from the DefinitelyTyped repository (e.g., `npm install @types/lodash --save-dev`). If you use a JavaScript library without its types, TypeScript won't know what `lodash.get()` returns or what arguments it expects.
3.  **Incorrect Import Path:**
    *   **Relative Paths:** Misspellings, incorrect directory traversal (`../` vs `./`), or forgetting the file extension (though `moduleResolution` often handles this for `.ts` files).
    *   **Absolute Paths/Path Aliases:** If you're using `baseUrl` or `paths` in your `tsconfig.json` to create aliases (e.g., `import { MyComponent } from '@components/MyComponent'`), these settings might be misconfigured or not correctly mapping to the physical file location.
4.  **`tsconfig.json` Misconfiguration:**
    *   **`moduleResolution`:** If set incorrectly (e.g., `node` vs. `bundler`), TypeScript might not use the expected algorithm to find modules in `node_modules`.
    *   **`baseUrl` and `paths`:** As mentioned above, incorrect mappings prevent TypeScript from resolving custom module paths.
    *   **`include` / `exclude`:** Your `tsconfig.json` might be accidentally excluding the directory where your module resides or where the type declarations are located.
    *   **`allowSyntheticDefaultImports` / `esModuleInterop`:** Sometimes, issues with how common JS modules are imported as ES modules can manifest similarly, though usually with different error codes.
5.  **Case Sensitivity:** On case-sensitive file systems (Linux, macOS by default), `import { MyService } from './myService'` will fail if the file is actually named `MyService.ts`. Windows is usually case-insensitive, which can hide these issues until deployment.
6.  **Monorepo Challenges:** In monorepos, hoisted `node_modules` or complex `tsconfig.json` setups across packages can sometimes lead to situations where a package is installed at the root but not correctly linked or resolved by a specific sub-package's TypeScript configuration.
7.  **Outdated `node_modules` / Cache Issues:** Sometimes, phantom errors occur due to corrupted `node_modules` or a stale `npm`/`yarn` cache. I've seen this in production when a `package-lock.json` gets out of sync or during CI builds.

## Step-by-Step Fix

Let's walk through the diagnostic and resolution process for TS2307.

1.  **Verify Module Installation:**
    First, confirm that the module 'X' is actually installed in your `node_modules` directory.
    ```bash
    # For npm
    npm ls X

    # For yarn
    yarn why X
    ```
    If `npm ls X` or `yarn why X` returns "empty" or "no dependencies", the module is not installed. If it shows the module, note its version.

2.  **Install the Missing Module:**
    If the module 'X' is not installed, install it.
    ```bash
    # Install as a regular dependency
    npm install X
    # or
    yarn add X

    # Install as a dev dependency (if only used during development/build)
    npm install X --save-dev
    # or
    yarn add X --dev
    ```

3.  **Install Missing Type Declarations:**
    If the module 'X' *is* installed but you're still getting the TS2307 error, it often means TypeScript can't find its type definitions. This is common for older JavaScript libraries.
    ```bash
    # Install types as a dev dependency
    npm install @types/X --save-dev
    # or
    yarn add @types/X --dev
    ```
    *Self-correction:* For scoped packages like `@angular/core`, the types package would typically be `@types/angular__core` (using double underscore). If 'X' is `lodash`, you'd install `@types/lodash`. If you're unsure, search on npmjs.com for `@types/X`.

4.  **Check Import Path Accuracy:**
    Scrutinize the `import` statement in your code.
    *   **Relative Paths:** Is `import { foo } from '../../components/foo'` correct? Double-check the directory structure.
    *   **Named vs. Default Imports:** Are you importing `import X from 'X'` (default) when it should be `import { X } from 'X'` (named), or vice-versa? Some libraries have different export styles.
    *   **Subpath Imports:** If you're importing a specific part of a library (e.g., `import { createLogger } from 'winston/lib/winston/create-logger'`), ensure the subpath is correct and exposed.

5.  **Review `tsconfig.json` Configuration:**
    Open your `tsconfig.json` file.
    *   **`baseUrl` and `paths`:** If you're using path aliases, verify they are correctly configured.
        ```json
        {
          "compilerOptions": {
            "baseUrl": ".", // This makes paths relative to the project root
            "paths": {
              "@components/*": ["src/components/*"],
              "@utils/*": ["src/utils/*"]
            },
            "moduleResolution": "node", // Generally safe default
            // ... other options
          }
        }
        ```
        Then, `import { MyButton } from '@components/MyButton'` should resolve to `src/components/MyButton.ts`.
    *   **`moduleResolution`:** Ensure it's set to `"node"` or `"bundler"` (for modern setups like Vite/Rollup). If you're using an older value, update it.
    *   **`include` and `exclude`:** Make sure your source files and any relevant `node_modules` aren't being inadvertently excluded.
    *   **`allowSyntheticDefaultImports` / `esModuleInterop`:** For packages that might have module interop issues, try setting these to `true` in `compilerOptions`.
        ```json
        {
          "compilerOptions": {
            "allowSyntheticDefaultImports": true,
            "esModuleInterop": true
            // ...
          }
        }
        ```

6.  **Rebuild/Restart:**
    After making changes, especially to `tsconfig.json` or installing new packages, stop and restart your TypeScript compiler, build process, or development server (e.g., `npm run dev`, `tsc --watch`). Your IDE might also need a restart to refresh its language server cache.

7.  **Clear `node_modules` and Cache:**
    As a last resort for stubborn issues, a clean slate often helps.
    ```bash
    # Delete node_modules and package-lock.json/yarn.lock
    rm -rf node_modules
    rm -f package-lock.json yarn.lock

    # Clear npm/yarn cache
    npm cache clean --force # For npm
    yarn cache clean        # For yarn

    # Reinstall everything
    npm install
    # or
    yarn install
    ```
    Then, try to build again. I've often seen this fix weird, inexplicable resolution failures.

8.  **Monorepo Specifics:**
    If you're in a monorepo, ensure the package is correctly declared in the `package.json` of the *sub-package* that's trying to import it. Also, check that your monorepo tool (Lerna, Nx, pnpm workspace) is properly hoisting or linking dependencies.

## Code Examples

Here are some concise, copy-paste ready examples for common fixes.

**1. Installing a missing module:**

```bash
# If your code has `import { someFunction } from 'some-library';`
# and 'some-library' is not installed:
npm install some-library
# or
yarn add some-library
```

**2. Installing missing type declarations:**

```bash
# If your code has `import moment from 'moment';`
# and you get TS2307, because 'moment' ships without its own types:
npm install @types/moment --save-dev
# or
yarn add @types/moment --dev
```

**3. Correct `tsconfig.json` for path aliases:**

```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": "./src", // Base URL for module resolution, relative to tsconfig.json
    "paths": {
      "@components/*": ["components/*"], // Maps @components/X to src/components/X
      "@services/*": ["services/*"]      // Maps @services/X to src/services/X
    },
    "moduleResolution": "node",
    "target": "es2020",
    "lib": ["es2020", "dom"],
    "jsx": "react",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*.ts", "src/**/*.tsx"],
  "exclude": ["node_modules"]
}
```
With the above `tsconfig.json`, you could write:
```typescript
// src/pages/HomePage.ts
import { Button } from '@components/Button'; // Resolves to src/components/Button.ts
import { UserService } from '@services/UserService'; // Resolves to src/services/UserService.ts

// ...
```

**4. Enabling ES Module Interop:**

```json
// tsconfig.json
{
  "compilerOptions": {
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true
    // ... other options
  }
}
```

## Environment-Specific Notes

The troubleshooting steps remain largely consistent, but how you apply them can differ slightly across environments.

### Local Development

*   **IDE Integration:** Your IDE (VS Code, WebStorm) typically runs its own TypeScript language server. This server often caches information. If you install new packages or change `tsconfig.json`, you might need to restart your IDE or use a "Restart TS Server" command within it to clear its cache and pick up the changes.
*   **File System:** Be mindful of case sensitivity if you develop on Windows and deploy to Linux. Windows' file system is usually case-insensitive, while Linux's is not. This can lead to modules being found locally but failing on a CI/CD server.
*   **`node_modules`:** Ensure the `node_modules` folder is where your `package.json` and `tsconfig.json` expects it to be. Accidental deletion or moving it can cause issues.

### Docker Containers

*   **Build Context:** When building Docker images, the `COPY . .` command copies your entire build context. Ensure that your `node_modules` are *not* copied from your host (unless you explicitly mean to, which is rarely recommended for production images). Instead, run `npm install` *inside* the Docker container during the build process.
*   **`WORKDIR`:** Verify your `WORKDIR` inside the Dockerfile is correctly set, as relative paths and `node_modules` resolution depend on it.
*   **Layer Caching:** Docker layers can cache `node_modules`. If you modify `package.json` or `package-lock.json`, ensure your Dockerfile invalidates the cache layer for `npm install` by placing it after the `COPY package*.json` step.
    ```dockerfile
    # Dockerfile example
    FROM node:lts-alpine
    WORKDIR /app
    COPY package*.json ./
    RUN npm install # This layer will be re-run if package.json changes
    COPY . .
    RUN npm run build
    CMD ["node", "dist/index.js"]
    ```
    If `npm install` fails inside Docker, check the container logs meticulously.

### Cloud Environments (CI/CD, Serverless)

*   **Clean Installs:** CI/CD pipelines typically perform clean `npm install` or `yarn install` operations. This is good as it prevents local environment inconsistencies, but it means you must ensure all dependencies (including `@types` packages) are correctly listed in `package.json`.
*   **Caching Strategies:** Most CI/CD platforms offer dependency caching. While this speeds up builds, a corrupted cache can sometimes be a source of `TS2307`. If an error is persistent, try disabling the cache for a build to see if it resolves the issue.
*   **Build Environment:** The Node.js version and npm/yarn version used in your CI/CD pipeline might differ from your local setup. Ensure they are compatible and consistent.
*   **Serverless Functions:** When deploying serverless functions (AWS Lambda, Azure Functions, Google Cloud Functions), your `node_modules` folder is usually zipped and uploaded. This means any `devDependencies` (including `@types`) that are critical for the *build process* must be installed *before* packaging, but often are not included in the final deployment package. Make sure your build script correctly handles this separation. I've often seen `TS2307` errors appear during serverless deployments simply because the build environment didn't have `@types` installed, even though the final runtime didn't need them.

## Frequently Asked Questions

**Q: Why do I need `@types` packages if TypeScript is installed?**
**A:** TypeScript itself provides the language features and compiler. However, many JavaScript libraries were written before TypeScript became popular and don't include type definitions. `@types` packages, primarily from the DefinitelyTyped project, provide these external type declarations, allowing TypeScript to understand and validate the usage of these JavaScript libraries.

**Q: How do I find the correct `@types` package for a library?**
**A:** The standard convention is `npm install @types/library-name`. For scoped packages like `@angular/core`, it's `npm install @types/angular__core`. If unsure, search on npmjs.com for `@types/your-library-name`. If no `@types` package exists, you might need to create a simple declaration file (`.d.ts`) yourself, often with `declare module 'X';` as a fallback.

**Q: What if the module *is* installed (I see it in `node_modules`) but I still get the error?**
**A:** This points to a module resolution issue. Double-check your import path, review your `tsconfig.json` (`baseUrl`, `paths`, `moduleResolution`), ensure you have the corresponding `@types` package, or try clearing `node_modules` and reinstalling. Case sensitivity on Linux/macOS is also a common culprit here.

**Q: Does this error mean my code won't run at all?**
**A:** It means your TypeScript code won't *compile* into JavaScript. If you manage to compile it (e.g., using `tsc --noEmit false` or ignoring the error), and the underlying JavaScript module is present at runtime, the JavaScript code might run. However, the purpose of TypeScript is to catch these errors at compile time, so bypassing it defeats the purpose and introduces potential runtime issues.

**Q: What exactly do `baseUrl` and `paths` in `tsconfig.json` do?**
**A:** `baseUrl` defines the base directory from which non-relative module imports are resolved. `paths` allows you to create alias mappings for specific import paths, letting you use shorter or more descriptive names (e.g., `@components`) instead of long relative paths like `../../../src/components`. They are powerful for organizing large projects and preventing "dot-dot-slash hell."

## Related Errors