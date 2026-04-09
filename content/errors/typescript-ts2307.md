# TypeScript TS2307: Cannot find module 'X' or its corresponding type declarations
> Encountering TS2307 means TypeScript cannot find a specified module or its corresponding type declarations, leading to compilation failure; this guide provides a practical, step-by-step approach to resolve it.

## What This Error Means

The `TS2307` error, "Cannot find module 'X' or its corresponding type declarations," is a common compilation error in TypeScript projects. At its core, it signifies that the TypeScript compiler is unable to locate the JavaScript module you're trying to import (e.g., `import { X } from 'X';`) or, crucially, its associated type definition file (`.d.ts`).

TypeScript relies on these type declarations to understand the structure, methods, and properties available within a module. Without them, it cannot perform static type checking, which is one of TypeScript's primary benefits. When you see this error, it's not a runtime issue; your code hasn't even executed yet. Instead, the TypeScript compiler is failing to build your project because it lacks the necessary information about an imported dependency. This can block your entire development workflow, from local builds to CI/CD pipelines.

## Why It Happens

This error primarily occurs because TypeScript's module resolution system cannot map an `import` statement to a physical file on disk and, subsequently, locate its type definitions. TypeScript's compiler follows specific rules, often mirroring Node.js's `require()` resolution algorithm (especially with `moduleResolution: "node"` in `tsconfig.json`), to find modules.

The "why" behind `TS2307` is almost always a tooling or configuration issue rather than a logical bug in your application code. It means that somewhere along the chain, either the module itself isn't where TypeScript expects it to be, or the accompanying `.d.ts` file that describes the module's types is absent or inaccessible. In my experience, this usually points to an installation problem, an incorrect import path, or a misconfigured `tsconfig.json`.

## Common Causes

Identifying the root cause is the first step to a quick resolution. Here are the most common scenarios that trigger `TS2307`:

1.  **Module Not Installed:** The most straightforward cause. You've added an `import` statement for a package but haven't actually installed it via your package manager (`npm` or `yarn`). TypeScript won't find it in `node_modules`.
    *   **Example:** `import { someFunction } from 'some-library';` but `some-library` isn't in `package.json` or `node_modules`.

2.  **Missing Type Definitions (`@types` Package):** Many older or plain JavaScript libraries don't ship with their own TypeScript declaration files (`.d.ts`). For TypeScript to understand these libraries, you need to install community-maintained type definitions from the DefinitelyTyped project, typically available as `@types/<package-name>`.
    *   **Example:** `import express from 'express';` but `@types/express` hasn't been installed.

3.  **Incorrect Import Path:**
    *   **Typo:** A simple misspelling in the module name or path.
    *   **Relative Path Error:** Incorrectly navigating the file system with `./` or `../`. For instance, importing `./utils/MyUtil` when the file is actually `./utils/myUtil.ts` (especially problematic on case-sensitive file systems like Linux).
    *   **Absolute Path Misconfiguration:** If you're using absolute imports (e.g., `import { Foo } from '@components/Foo'`), but `tsconfig.json`'s `baseUrl` or `paths` are not correctly configured to resolve these aliases.
    *   **Missing Extension/Index File:** Depending on your `moduleResolution` and environment, you might need to specify file extensions or ensure `index.ts` files exist where expected.

4.  **`tsconfig.json` Misconfiguration:**
    *   **`baseUrl`:** If not set correctly, absolute imports will fail.
    *   **`paths`:** Used for module aliases, crucial for monorepos or custom import paths. An incorrect mapping here will prevent resolution.
    *   **`moduleResolution`:** While `"node"` is common, if your project uses modern bundlers or specific module formats, `"bundler"` or `"node16"` might be required.
    *   **`typeRoots` / `types`:** These options can explicitly tell TypeScript where to look for type definitions or which types to include/exclude. If overly restrictive or incorrect, they can hide legitimate type packages.
    *   **`include` / `exclude`:** If your `tsconfig.json` doesn't include the relevant source files or accidentally excludes `node_modules`, modules within those paths won't be processed.

5.  **Module Not Properly Exported:** Less common, but sometimes the module you're trying to import doesn't actually export the member you're looking for, or its `package.json` has an incorrect `main` or `exports` field.

6.  **Stale `node_modules` or Build Cache:** Occasionally, after installing new packages or type definitions, the build tools or IDEs don't refresh their cache, leading to persistent errors.

## Step-by-Step Fix

Let's walk through the most effective troubleshooting steps for `TS2307`. I always start from the simplest fixes and work my way up to more complex configuration changes.

1.  **Verify Module Installation:**
    *   **Check `package.json`:** Open your `package.json` file and confirm that the module `X` (or its main package name) is listed under `dependencies` or `devDependencies`.
    *   **Check `node_modules`:** Manually verify if the module's directory exists within your `node_modules` folder.
    *   **Reinstall Dependencies:** If the package is missing or `node_modules` seems corrupted, run your package manager's install command:
        ```bash
        # For npm
        npm install <package-name> # if it's completely new
        npm install               # to ensure all dependencies from package.json are installed

        # For yarn
        yarn add <package-name>    # if it's completely new
        yarn                      # to ensure all dependencies from package.json are installed
        ```

2.  **Install Type Definitions:**
    *   If `X` is a JavaScript library that doesn't include its own `.d.ts` files, you'll need to install the corresponding `@types` package. In my experience, this is the single most common fix for `TS2307`.
        ```bash
        # Example: for the 'lodash' library
        npm install --save-dev @types/lodash

        # For yarn
        yarn add --dev @types/lodash
        ```
    *   Remember to restart your TypeScript server or IDE after installing new `@types` packages for changes to take effect.

3.  **Check Import Paths:**
    *   **Exact Match:** Ensure the import path in your `.ts` file exactly matches the module name or the relative path to your local file. Pay close attention to case sensitivity.
    *   **Relative Paths:** Double-check relative paths like `./components/MyComponent` or `../services/api`. Make sure they resolve correctly from the current file's location.
    *   **Absolute Paths/Aliases:** If you're using aliases (e.g., `import { User } from '@models/User'`), confirm that these are correctly configured in your `tsconfig.json` under `compilerOptions.baseUrl` and `compilerOptions.paths`.

4.  **Review `tsconfig.json` Configuration:**
    *   **`compilerOptions.baseUrl`:** This path serves as the base for resolving non-relative module names. Ensure it points to the correct root of your source files (e.g., `"./src"`).
    *   **`compilerOptions.paths`:** Crucial for custom module mappings. For example:
        ```json
        {
          "compilerOptions": {
            "baseUrl": ".", // Or "./src"
            "paths": {
              "@utils/*": ["src/utils/*"],
              "@components/*": ["src/components/*"]
            }
          }
        }
        ```
    *   **`compilerOptions.moduleResolution`:** For Node.js projects, `"node"` is standard. Modern setups or specific bundlers might benefit from `"bundler"` or `"node16"`.
    *   **`compilerOptions.typeRoots` / `compilerOptions.types`:** If you've customized these, ensure they include `node_modules/@types` (the default location for `@types` packages) or any other directories where your custom `.d.ts` files reside.
    *   **`include` / `exclude`:** Ensure your TypeScript files and relevant declaration files are not accidentally excluded.
    *   **Run `tsc --showConfig`:** This command is invaluable for debugging your effective `tsconfig.json` settings, especially when dealing with inherited configurations or complex setups.

5.  **Clean and Rebuild:**
    *   Sometimes, stale caches or partially installed dependencies can cause phantom errors.
    *   Delete `node_modules` and `package-lock.json` (or `yarn.lock`).
    *   Clear your npm/yarn cache: `npm cache clean --force` or `yarn cache clean`.
    *   Reinstall all dependencies: `npm install` or `yarn`.
    *   Delete your `dist` or output directory.
    *   Recompile your project: `tsc` or your specific build command (e.g., `npm run build`).

6.  **Restart Your IDE/TypeScript Server:**
    *   Especially in VS Code, the TypeScript language server can sometimes get out of sync. A quick restart of the editor or the TS server (usually accessible via the command palette) can often resolve persistent `TS2307` errors after a fix has been applied.

## Code Examples

Here are some concise, copy-paste ready examples for common `TS2307` fixes.

**1. Installing Missing Type Definitions:**

If your code has:
```typescript
import { format } from 'date-fns';
// TS2307: Cannot find module 'date-fns' or its corresponding type declarations.
```
But `date-fns` is a JavaScript library without built-in types, you need to install its `@types` package:

```bash
# Install the library (if not already)
npm install date-fns
# Then install its types as a dev dependency
npm install --save-dev @types/date-fns
```

**2. Correcting `tsconfig.json` for Path Aliases:**

Given a project structure like:
```
my-project/
├── src/
│   ├── components/
│   │   └── Button.ts
│   └── utils/
│       └── helpers.ts
├── tsconfig.json
└── package.json
```
And you want to import `helpers.ts` as `@utils/helpers`:

Your `tsconfig.json` should look like this:
```json
{
  "compilerOptions": {
    "baseUrl": ".", // Base for module resolution, often the project root
    "paths": {
      "@utils/*": ["src/utils/*"],
      "@components/*": ["src/components/*"]
    },
    "moduleResolution": "node",
    "target": "es2017",
    "module": "commonjs",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules"]
}
```
Then, you can use the alias in your TypeScript files:
```typescript
// src/some-file.ts
import { capitalize } from '@utils/helpers';
import { Button } from '@components/Button';
```

**3. Dockerfile for a TypeScript Project (Ensuring Dependencies are Installed):**

A common `TS2307` trigger in Docker is forgetting to install dependencies.

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package.json ./
COPY package-lock.json ./

# Install production dependencies (or all if building dev image)
RUN npm ci --omit=dev

# Copy the rest of the application code
COPY . .

# Build the TypeScript project
RUN npm run build # This command should internally call 'tsc'

# Start the application
CMD ["node", "dist/index.js"]
```

## Environment-Specific Notes

The context in which you encounter `TS2307` can influence your troubleshooting approach.

*   **Local Development:**
    *   Your IDE (e.g., VS Code) usually has a built-in TypeScript language server that actively flags these errors. Ensure it's running correctly and restart it if errors persist after a fix.
    *   Using `tsc --watch` during development can give you immediate feedback when you make changes, helping you spot resolution issues quickly.
    *   Be mindful of global npm packages versus local project dependencies. `TS2307` typically relates to local `node_modules`.

*   **Cloud (CI/CD Pipelines):**
    *   This is a frequent place to see `TS2307`, often when local development works fine. The primary culprits are usually:
        *   **`node_modules` not committed:** Your build pipeline *must* run `npm install` (or `npm ci` for lockfile integrity) before attempting to compile TypeScript.
        *   **Stale `package-lock.json` / `yarn.lock`:** If these files are not updated after adding new dependencies (including `@types` packages), the CI environment might install an older, incomplete set of packages. Always ensure your lock files are committed and up-to-date. I've seen this in production when someone forgot to update `package.json` after adding a new dependency.
        *   **Case Sensitivity:** CI/CD environments (often Linux-based) are case-sensitive regarding file paths, unlike macOS or Windows default settings. An `import { MyComponent } from './myComponent'` could work locally but fail in CI if the file is actually `MyComponent.ts`.
        *   **Caching Issues:** Ensure your CI environment's npm/yarn cache is properly managed; sometimes a full cache clear might be needed in the pipeline configuration.

*   **Docker:**
    *   When building Docker images for TypeScript applications, the entire build process happens within the container.
    *   **Dependency Installation Order:** Copy `package.json` and `package-lock.json` first, run `npm install`, *then* copy the rest of your source code. This leverages Docker's layer caching effectively.
    *   **Production vs. Development Dependencies:** If you're building a production image, use `npm ci --omit=dev` or `yarn install --production` to only install necessary runtime dependencies, but ensure any `@types` packages needed *for the build step* are either installed during the build (`npm ci` without `--omit=dev`) or your build artifacts (`.js` files) are copied into the final image.

## Frequently Asked Questions

**Q: Why does my project compile fine locally but fail on CI/CD with TS2307?**
**A:** This is a classic scenario. The most common reasons are: 1) `node_modules` is not committed, and the CI environment's `npm install` differs from your local setup (e.g., stale `package-lock.json`, `npm ci` not used). 2) Case sensitivity issues: your local OS might be case-insensitive, while the CI (likely Linux) is not, causing path mismatches. 3) Missing environment variables or configuration differences specific to the CI server.

**Q: I installed `@types/X`, but the error persists. What next?**
**A:** First, try restarting your IDE (VS Code, WebStorm) to ensure its TypeScript language server picks up the new types. If that doesn't work, delete `node_modules`, `package-lock.json` (or `yarn.lock`), run `npm install` (or `yarn`), and then rebuild your project. Also, double-check your `tsconfig.json` for any `typeRoots` or `types` options that might be overriding or restricting where TypeScript looks for declaration files.

**Q: My module 'X' exists, but TypeScript still can't find it. It's a local file.**
**A:** This usually points to an incorrect import path. Verify the *exact* relative or absolute path, including the file's case and extension (though TypeScript often infers `.ts`, `.tsx`, `.d.ts`). Ensure the file itself is included by your `tsconfig.json`'s `include` patterns and not excluded by `exclude`. If it's a plain `.js` file, you might need to create a simple `index.d.ts` file next to it or in your `@types` directory to provide its type definitions.

**Q: What's the difference between `moduleResolution: "node"` and `"bundler"`?**
**A:** `moduleResolution: "node"` simulates Node.js's module resolution algorithm. It's robust for Node.js projects. `moduleResolution: "bundler"` is a newer strategy designed to align more closely with how modern JavaScript bundlers (Webpack, Rollup, Vite, esbuild) resolve modules. It's particularly useful for projects targeting browsers or using modern `package.json` `exports` field features. If you're experiencing resolution issues with newer packages, trying `"bundler"` might help.

**Q: Can I ignore this error?**
**A:** No, `TS2307` is a critical compilation error. It means TypeScript fundamentally cannot understand the types of a module you're trying to use, which defeats the purpose of TypeScript and will prevent your project from compiling. You must resolve this error for your application to build successfully.

## Related Errors

*   [npm-missing-package](/errors/npm-missing-package.html)