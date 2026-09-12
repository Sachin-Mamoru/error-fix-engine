# TypeScript TS2307: Cannot find module 'X' or its corresponding type declarations
> Encountering TypeScript TS2307 means your project can't locate a module or its type definitions; this guide explains how to fix it by verifying installations and configuration.

## What This Error Means

This error indicates that the TypeScript compiler (`tsc`) cannot find the JavaScript module you are trying to `import`, or it cannot find the associated type declaration file (`.d.ts`) for that module. TypeScript needs these type declarations to perform static analysis and ensure type safety. Without them, it cannot understand the shape or interface of the imported module, leading to a compilation failure. It's essentially TypeScript telling you, "I don't know what `X` is, or what types it exposes, so I can't guarantee your code is safe to compile."

## Why It Happens

This error typically arises when there's a disconnect between your project's `node_modules` directory, your `tsconfig.json` configuration, and the actual packages you're trying to use. TypeScript's compiler relies on these pieces to resolve modules. If any piece is missing, misconfigured, or out of sync, `TS2307` is the result. In my experience, it's almost always a pathing issue, a missing dependency, or a missing type declaration package.

## Common Causes

Let's break down the typical culprits I've encountered when this error surfaces:

1.  **Module Not Installed:** The most straightforward reason. You're attempting to `import` a package that hasn't been added to your `package.json` dependencies and subsequently installed via `npm install` or `yarn install`. TypeScript can't find something that isn't there.
2.  **Missing Type Declarations (`@types` Package):** Even if the JavaScript module is installed, TypeScript needs its type definitions. Many popular libraries ship with their types directly, but others (especially older ones or those not primarily focused on TypeScript) require a separate `@types/package-name` package from the DefinitelyTyped project. If this `devDependencies` package is missing, TypeScript cannot type-check the module.
3.  **Incorrect Module Name or Path:** A simple typo in the `import` statement or an incorrect relative or absolute path to a local module. This often happens with refactoring or copy-pasting code.
4.  **`tsconfig.json` Misconfiguration:**
    *   **`baseUrl` and `paths`:** If you're using path aliases (e.g., `import { logger } from '@utils/logger';`), your `tsconfig.json` needs to correctly map these aliases to physical file system paths. If these mappings are incorrect or incomplete, TypeScript won't find the aliased module.
    *   **`moduleResolution`:** Incorrectly set. For most Node.js projects, this should be `node`. If it's `classic` or an unsupported value, TypeScript might not use the standard Node.js module resolution algorithm to find your packages.
    *   **`typeRoots`:** If you're managing custom type declarations or placing `@types` packages in non-standard locations, `typeRoots` needs to explicitly point to these directories. By default, TypeScript usually looks in `node_modules/@types`, but custom setups can override this.
    *   **`include` / `exclude`:** The TypeScript compiler might not be looking in the correct directories for your source files or installed types if these configuration options are too restrictive.
5.  **Corrupted `node_modules` or `package-lock.json`:** Sometimes, local dependency caches can get out of sync, or the `node_modules` directory can become corrupted. This often happens after merging branches, switching Node.js versions, or dealing with complex dependency trees.
6.  **Case Sensitivity Issues:** While development environments on Windows or macOS might be case-insensitive, Linux-based CI/CD pipelines, Docker containers, or production servers are strictly case-sensitive. If an import path or module name has incorrect casing (e.g., `import { MyUtil } from './myUtil';` instead of `./MyUtil`), it might work locally but fail in a case-sensitive environment.
7.  **Transpiled Output vs. Source:** If you're importing a module that's part of your project but hasn't been compiled yet (or its output is in a different directory than expected), TypeScript might not find it. This is less common for external `node_modules` but can happen with monorepos or complex build setups where internal packages depend on each other's compiled output.

## Step-by-Step Fix

Let's walk through the troubleshooting steps I typically follow when encountering this error.

1.  **Verify Module Installation:**
    *   **Check `package.json`:** Open your `package.json` file and confirm that the module `X` (or the package that provides `X`) is listed under `dependencies` or `devDependencies`.
    *   **Check `node_modules`:** Manually verify that the module's directory actually exists within your project's `node_modules` directory.
    *   **Reinstall:** If the module isn't found, install it.
        ```bash
        npm install <module-name> # For production dependencies
        # or
        npm install --save-dev <module-name> # For development dependencies
        # If using Yarn:
        yarn add <module-name>
        # or
        yarn add --dev <module-name>
        ```
    *   **Example:** If the error is `Cannot find module 'lodash'`, you'd run `npm install lodash`.

2.  **Install Missing Type Declarations:**
    *   If the module itself is installed (i.e., step 1 passed) but the error persists, it's highly likely you need the `@types` package for it. Search for `npm install @types/<module-name>`.
    *   Type declaration packages are almost always `devDependencies`.
    *   **Example:** For `lodash`, you'd run `npm install --save-dev @types/lodash`.
    *   **Note:** Sometimes the type declaration package name differs slightly from the module name (e.g., `react-router-dom` needs `@types/react-router-dom`). A quick search on npmjs.com or DefinitelyTyped's repository usually clarifies this.

3.  **Check Import Path and Module Name:**
    *   **Typo?** Double-check the spelling of the module in your `import` statement in the problematic TypeScript file.
    *   **Relative Path Correct?** For local files (e.g., `import { MyService } from '../services/my-service';`), ensure the path is accurate relative to the importing file. Remember that `./` means "current directory" and `../` means "parent directory".
    *   **Absolute Path / Alias Correct?** If you're using path aliases (e.g., `import { logger } from '@utils/logger';`), confirm that the alias is correctly defined in `tsconfig.json` (see step 4). Pay attention to case sensitivity here.

4.  **Review `tsconfig.json` Configuration:**
    *   **`baseUrl` and `paths`:** If you are using path aliases, confirm they are correctly mapped within `compilerOptions`. The `baseUrl` typically defines the root for module resolution.
        ```json
        // tsconfig.json example for path aliases
        {
          "compilerOptions": {
            "baseUrl": "./src", // Crucial: all module paths are relative to this base
            "paths": {
              "@utils/*": ["utils/*"], // Now resolves to ./src/utils/*
              "@config": ["config/index.ts"] // Resolves to ./src/config/index.ts
            },
            // ... other options
          }
        }
        ```
        In this example, `import { foo } from '@utils/bar';` would resolve to `src/utils/bar.ts`.
    *   **`moduleResolution`:** For most modern Node.js projects, this should be `node`.
        ```json
        {
          "compilerOptions": {
            "moduleResolution": "node",
            // ...
          }
        }
        ```
    *   **`typeRoots`:** If you have custom type declarations or are using a non-standard structure for `@types` packages, ensure `typeRoots` points to them. Generally, `typeRoots: ["./node_modules/@types"]` is implicitly handled, but explicit declaration might be needed in complex setups or when using global types.
    *   **`include` / `exclude`:** Ensure your TypeScript source files and any directories containing custom type definitions are covered by the `include` array and not inadvertently excluded by `exclude`.

5.  **Clean and Reinstall Dependencies:**
    *   Sometimes, the `node_modules` directory or the lock file (`package-lock.json`, `yarn.lock`) can get into a strange state. A fresh install often resolves these issues.
        ```bash
        rm -rf node_modules
        rm -f package-lock.json # For npm users
        rm -f yarn.lock        # For yarn users

        npm install # or yarn install
        ```
    *   After performing this, try compiling your TypeScript project again.

6.  **Restart TypeScript Language Server (IDE):**
    *   If you're using an IDE like VS Code, the TypeScript language server might not have picked up recent changes (like newly installed `@types` packages). Restarting VS Code or using the "TypeScript: Restart TS Server" command (usually accessible via Ctrl+Shift+P or Cmd+Shift+P) can resolve this by forcing the language server to re-index your project. I've seen this many times where the command line build passes but the IDE still shows the error.

## Code Examples

Here are some common scenarios and their corresponding fixes.

**Scenario 1: Missing Module Installation**

Error: `TS2307: Cannot find module 'axios' or its corresponding type declarations.`
Your code:
```typescript
import axios from 'axios';

async function fetchData() {
  const response = await axios.get('https://api.example.com/data');
  console.log(response.data);
}
```
Fix: Install the `axios` package.
```bash
npm install axios
# or
yarn add axios
```

**Scenario 2: Missing Type Declarations for an Installed Module**

Error: `TS2307: Cannot find module 'express' or its corresponding type declarations.`
Your code:
```typescript
import express from 'express';
const app = express();
app.get('/', (req, res) => res.send('Hello'));
app.listen(3000, () => console.log('Listening on port 3000'));
```
Fix: Install the `@types/express` type declaration package.
```bash
npm install --save-dev @types/express
# or
yarn add --dev @types/express
```

**Scenario 3: Incorrect Relative Path for a Local File**

Error: `TS2307: Cannot find module './utils/helpers' or its corresponding type declarations.`
File structure:
```
src/
  api/
    index.ts (where the error occurs)
  common/
    helpers.ts
```
Your code in `src/api/index.ts`:
```typescript
import { formatData } from './utils/helpers'; // Incorrect path
// The file 'helpers.ts' is in 'src/common', not 'src/api/utils'
```
Fix: Correct the import path to reflect the actual file location.
```typescript
import { formatData } from '../common/helpers'; // Corrected path
```

**Scenario 4: `baseUrl` and `paths` Misconfiguration for an Alias**

Error: `TS2307: Cannot find module '@config/app' or its corresponding type declarations.`
Your code:
```typescript
import { APP_NAME } from '@config/app';
console.log(APP_NAME);
```
`tsconfig.json`:
```json
{
  "compilerOptions": {
    "baseUrl": ".", // Assume project root is '.'
    "paths": {
      "@config/*": ["config/*"] // This maps to ./config/* relative to baseUrl
    },
    // ... other options
  },
  "include": ["src/**/*"]
}
```
And file structure:
```
my-project/
  src/
    config/
      app.ts
  tsconfig.json
```
The error here is that `@config/*` would resolve to `config/*` relative to `baseUrl: "."`, meaning `my-project/config/app.ts`. But the actual file is at `my-project/src/config/app.ts`.

Fix: Adjust `baseUrl` and `paths` to correctly reflect the structure.

Option A: Set `baseUrl` to `src`
```json
{
  "compilerOptions": {
    "baseUrl": "./src", // Now base is 'src'
    "paths": {
      "@config/*": ["config/*"] // Resolves to ./src/config/*
    },
    // ...
  }
}
```
Option B: Keep `baseUrl` at `.` but adjust `paths`
```json
{
  "compilerOptions": {
    "baseUrl": ".", // Base is project root
    "paths": {
      "@config/*": ["src/config/*"] // Explicitly point into 'src'
    },
    // ...
  }
}
```

## Environment-Specific Notes

The `TS2307` error can manifest differently or require specific considerations based on your development and deployment environment.

*   **Local Development:**
    *   **IDE Caching:** As mentioned, if you add new `@types` packages, your IDE's TypeScript language server might need a restart to pick up the changes. This is a common pitfall and can lead to confusion when the command line compiler works, but the IDE still flags an error.
    *   **Global Installs:** Avoid using global `npm install -g` for project dependencies. This can lead to version mismatches, makes your project less portable, and makes it harder for project-specific tools to find modules reliably. Always install dependencies locally to the project.
    *   **`node_modules` Visibility:** Ensure your project root (where `package.json` and `tsconfig.json` reside) is at a level where `node_modules` is directly accessible. Sometimes overly nested project structures can confuse module resolution.

*   **Docker Containers:**
    *   **Image Layers and `npm install`:** When building Docker images, `node_modules` is typically created as a separate layer. It's crucial that `npm install` (or `yarn install`) runs *inside* the container during the Docker build process, after `package.json` and `package-lock.json` are copied. Copying `node_modules` from your host machine directly can lead to issues due to OS differences (e.g., native module compilation, symlinks).
    *   **`.dockerignore`:** Double-check your `.dockerignore` file. If `node_modules` is listed, it won't be copied into the container. This is usually desired if you want `npm install` to run freshly. However, if you explicitly intended to copy an existing `node_modules` (which is rare and often problematic), ensure it's not ignored.
    *   **`WORKDIR`:** Verify that the `WORKDIR` instruction in your `Dockerfile` is correctly set to the directory where your `package.json` and `tsconfig.json` reside. An incorrect `WORKDIR` means `npm install` will run in the wrong place, and `tsc` won't find `node_modules` when it tries to compile.

    ```dockerfile
    # Example Dockerfile snippet for a TypeScript Node.js app
    FROM node:18-alpine as builder
    WORKDIR /app
    COPY package.json package-lock.json ./ # Copy only package files first
    RUN npm install --frozen-lockfile      # Install dependencies in a separate layer

    COPY . .                               # Copy the rest of your application code
    RUN npm run build                      # Run your TypeScript build command

    FROM node:18-alpine as runner
    WORKDIR /app
    COPY --from=builder /app/package.json ./
    COPY --from=builder /app/node_modules ./node_modules
    COPY --from=builder /app/dist ./dist  # Assuming 'dist' is your build output directory

    CMD ["node", "dist/index.js"]
    ```

*   **Cloud (e.g., AWS Lambda, Google Cloud Functions):**
    *   **Deployment Package Size:** When deploying to serverless platforms, the `node_modules` directory is often part of your deployment package. Ensure all necessary dependencies, including `@types` packages (if your build runs on the serverless platform and needs them, though typically `@types` are dev dependencies), are included and correctly bundled.
    *   **Build Environment Consistency:** The build environment in cloud CI/CD pipelines (e.g., AWS CodeBuild, GitHub Actions, GitLab CI) might differ from your local machine. Ensure these environments have sufficient memory and disk space for `npm install` to complete successfully and consistently. I've seen `npm install` silently fail or get corrupted due to resource constraints, leading to this `TS2307` error only in deployment.
    *   **Lambda Layers:** If using AWS Lambda Layers for common dependencies, ensure the layer is correctly configured and accessible to your function. The path within the layer must match what the Node.js runtime expects (e.g., `/opt/nodejs/node_modules`). Your function's import statements need to resolve to these paths.

## Frequently Asked Questions

*   **Q: Why does my code work fine in VS Code but fail when I run `tsc` from the command line?**
    *   **A:** VS Code's TypeScript language server sometimes has a more lenient module resolution, or it might be using an older/cached version of your `node_modules` or `tsconfig.json`. When `tsc` runs from the command line, it's performing a fresh compilation based strictly on your current project files and configuration. Restarting VS Code's TS server or explicitly running `tsc --build` (or `npm run build`) after changes usually syncs them up.

*   **Q: I'm using Yarn workspaces or a monorepo. How does that affect this error?**
    *   **A:** In monorepos, module resolution can be more complex. Ensure that:
        1.  Your `package.json` files for each workspace correctly list their dependencies.
        2.  `yarn install` or `npm install` is run from the monorepo root to hoist/link dependencies correctly.
        3.  `tsconfig.json` files in sub-packages correctly extend a base `tsconfig.json` if applicable, and their `baseUrl` and `paths` are configured relative to their own context or the monorepo root. Sometimes `composite` projects and `references` in `tsconfig.json` are needed for inter-package dependencies.

*   **Q: Does the order of `npm install package` and `npm install --save-dev @types/package` matter?**
    *   **A:** Not strictly for the TypeScript compiler, as it will look for types regardless of when they were installed, as long as they are present in `node_modules/@types`. However, it's good practice to install the main package first, then its types. When installing a new package, I typically install both (the `package` and `@types/package`) together or consecutively before attempting to compile, just to ensure consistency.

*   **Q: My module `X` *does* have its own built-in types (e.g., `react`). Why am I still getting TS2307?**
    *   **A:** Even with built-in types, there might be an issue.
        1.  **TypeScript Version:** Your project's TypeScript version might be too old to understand the types provided by the module, especially if the module uses newer TypeScript features.
        2.  **`package.json` `types` field:** The module's `package.json` might not correctly point to its type declarations via the `types` or `typings` field, or there's an issue with the module's packaging.
        3.  **`moduleResolution`:** An incorrect `moduleResolution` setting in `tsconfig.json` can prevent TypeScript from finding built-in types. Ensure it's set to `node` for Node.js environments.
        4.  **Corrupted `node_modules`:** A clean reinstall (step 5) can sometimes resolve this if the package was partially installed or corrupted.

*   **Q: I've tried everything in the guide, but the error persists. What's next?**
    *   **A:**
        1.  **Simplify:** Create a minimal `tsconfig.json` and a single `.ts` file that only imports the problematic module. Does it still fail? This helps isolate whether the issue is with the module itself or your broader project configuration.
        2.  **Verbose Output:** Run `tsc --traceResolution` to get extremely detailed output on how TypeScript is attempting to resolve modules. This verbose logging can reveal exactly where it's looking, what paths it's trying, and why it's ultimately failing to find the module. It's often the Rosetta Stone for complex resolution issues.
        3.  **Search:** Use the exact error message along with the specific module name (`TS2307 cannot find module 'X'`) in a search engine. Someone else has likely encountered the same specific combination of module, environment, and `tsconfig.json` settings.

## Related Errors
*   *(none)*