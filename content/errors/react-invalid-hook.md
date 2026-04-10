# React Error: Invalid hook call – Hooks can only be called inside a function component
> Encountering an 'Invalid hook call' means you're using React Hooks outside of a function component; this guide explains how to identify and fix these common missteps.

## What This Error Means

This error is React's strict way of telling you that you've violated one of its fundamental "Rules of Hooks." React Hooks like `useState`, `useEffect`, `useContext`, or any custom hook you create (which internally uses other hooks) are special functions designed to add state and lifecycle features to functional components. The core rule is simple: Hooks can *only* be called inside a React function component or from within another custom hook.

When React throws "Invalid hook call," it means its internal mechanisms, which rely on a consistent order and context for hook calls, have detected a violation. It can't properly associate the state or effect you're trying to declare with a specific functional component instance. This isn't just a suggestion; it's a critical constraint for React to manage your component's state and lifecycle correctly and predictably.

## Why It Happens

React relies on a predictable sequence of hook calls during a component's render cycle. When you call a hook, React internally keeps track of which component is currently rendering and associates the hook's state or effect with that component instance.

If a hook is called outside a functional component (e.g., in a class component, a regular JavaScript function, or even conditionally), React loses this crucial context. It doesn't know which component's state it should manage or which component's lifecycle it should tie an effect to. This leads to an internal error within React's core, prompting the "Invalid hook call" message. It's a safety mechanism to prevent unpredictable behavior and hard-to-debug state inconsistencies.

## Common Causes

In my experience, this error almost always boils down to one of these scenarios:

1.  **Hook Called in a Class Component:** This is arguably the most common and straightforward cause. Class components use their own state management (`this.state`) and lifecycle methods (`componentDidMount`, etc.). They simply cannot use React Hooks. If you're attempting to call `useState` or `useEffect` within a `class MyComponent extends React.Component` definition, React will immediately flag it.
2.  **Hook Called in a Regular JavaScript Function:** You might have a utility function, a helper, or a callback that is *not* a React function component and does *not* start with `use` (making it a custom hook). If you try to call `useState` or any other hook inside such a function, React won't have the necessary context. The only non-component functions that can call hooks are custom hooks, and they must be named accordingly (e.g., `useMyCustomHook`).
3.  **Multiple React Instances:** This is a more subtle and frustrating cause. It happens when your application ends up with more than one copy of the `react` package in its `node_modules` directory, or when a library you're using also bundles its own version of React. Each copy of `react` has its own internal state, and if a component from one instance tries to call a hook from another instance, React detects a mismatch and throws the "Invalid hook call" error. This is particularly common in monorepos or with certain build tools.
4.  **Incorrect Module Resolution:** Related to the multiple instances problem, misconfigured `webpack` or `rollup` aliases, or even incorrect `tsconfig.json` paths, can lead to your application resolving `react` from a different location than where your hooks are expected to resolve it, effectively creating the same "multiple React instances" issue.
5.  **Using an Outdated React Version:** While less common for *this specific error* (as the error implies hooks are *available* but misused), if you were on a very old React version (pre-16.8), hooks wouldn't exist. However, if hooks are present and throwing this error, it's usually one of the above.

## Step-by-Step Fix

When tackling this error, a systematic approach is key. Don't just guess; follow these steps:

1.  **Locate the Error Source:** The error message in your console will usually point to the exact file and line number where the invalid hook call occurred. This is your starting point. If the error points to React's internal files, that often suggests a "multiple React instances" issue, but always trace back to your code.

2.  **Check for Hook Usage in Class Components:**
    *   Examine the file identified. Is the component defined using `class MyComponent extends React.Component`?
    *   If so, any `useState`, `useEffect`, or custom hook call within its `render()` method, constructor, or any other class method is incorrect.
    *   **Fix:** You have two main options:
        *   **Refactor to a Function Component:** This is often the cleanest solution. Convert your class component into a functional component, allowing you to use hooks directly.
        *   **Use Class Component Lifecycle/State:** If refactoring is not feasible, replace the hook logic with class-based alternatives (e.g., `this.state` and `setState` for `useState`, `componentDidMount`, `componentDidUpdate`, `componentWillUnmount` for `useEffect`).

    ```javascript
    // Problem: Hook in a class component
    class UserProfile extends React.Component {
        // const [username, setUsername] = useState(''); // ERROR: Invalid hook call here

        render() {
            return <div>Profile Page</div>;
        }
    }
    ```

3.  **Identify Hooks in Regular JavaScript Functions:**
    *   If your component is already a function component, check if any hooks are being called inside helper functions that are *not* themselves custom hooks.
    *   A function like `function formatData(data) { const [config, setConfig] = useState({}); ... }` will cause this error if `formatData` isn't a custom hook (i.e., doesn't start with `use`).
    *   **Fix:**
        *   If the helper function *should* manage state or effects, rename it to follow the custom hook convention (e.g., `useFormatData`) and ensure it's called only from a function component or another custom hook.
        *   If it's purely a utility, pass any necessary state or props to it as arguments, rather than attempting to call hooks inside it.

    ```javascript
    // Problem: Hook in a regular JS function
    function generateReportData() {
        // const [data, setData] = useState([]); // ERROR: Invalid hook call here
        // This function should probably receive data as an argument or be a custom hook
        return [];
    }
    ```

4.  **Diagnose Multiple React Instances:**
    *   If the above steps don't resolve the issue, especially if the error points to `react-dom` or React's core files, suspect duplicate React instances.
    *   Use your package manager to inspect your dependency tree.
        *   For npm: `npm ls react`
        *   For Yarn: `yarn why react`
    *   Look for multiple versions of `react` or `react-dom` in the output.
    *   **Fix:**
        *   **Force a single version:** In your `package.json`, use `resolutions` (Yarn) or `overrides` (npm 8+) to explicitly tell your package manager to use only one version of `react` and `react-dom`.
        ```json
        // package.json example
        {
          "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            // other dependencies
          },
          "resolutions": {
            "react": "18.2.0",
            "react-dom": "18.2.0"
          },
          "overrides": {
            "react": "18.2.0",
            "react-dom": "18.2.0"
          }
        }
        ```
        *   **Clear `node_modules` and reinstall:** After modifying `package.json` (or even if you haven't), always delete `node_modules` and your lock file (`package-lock.json` or `yarn.lock`), then run `npm install` or `yarn install` again.
        ```bash
        rm -rf node_modules
        rm package-lock.json # or yarn.lock
        npm install           # or yarn install
        ```
        *   **Configure Webpack/Rollup aliases:** If you're building a library or a complex monorepo, explicitly alias `react` and `react-dom` to a single path in your build configuration.
        ```javascript
        // webpack.config.js snippet
        module.exports = {
          resolve: {
            alias: {
              'react': path.resolve(__dirname, 'node_modules/react'),
              'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
            },
          },
        };
        ```

5.  **Restart Your Development Server:** After making any changes, particularly to `node_modules` or `package.json`, always restart your development server (`npm start`, `yarn start`, or `vite`). Hot Module Replacement (HMR) can sometimes hold onto stale module references.

## Code Examples

Here are concise, copy-paste-ready examples demonstrating the problem and the correct approach.

### Problem: Hook in a Class Component

```javascript
import React, { useState, useEffect } from 'react';

// This is a class component. Hooks are not allowed here.
class DataFetcher extends React.Component {
    // Attempting to call useState or useEffect directly in a class component
    // will result in "Invalid hook call".
    // const [data, setData] = useState(null);
    // useEffect(() => { /* ... */ }, []);

    componentDidMount() {
        // Class components use lifecycle methods, not hooks.
        console.log('Component mounted via class method.');
        // fetch('/api/data').then(res => res.json()).then(data => this.setState({ data }));
    }

    render() {
        return <div>Displaying Class Component Data</div>;
    }
}
```

### Fix: Refactor to Function Component

```javascript
import React, { useState, useEffect } from 'react';

// This is now a functional component, where hooks can be used correctly.
function DataFetcherFunction() {
    const [data, setData] = useState(null); // Correct: useState inside a function component
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => { // Correct: useEffect inside a function component
        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const result = await response.json();
                setData(result);
            } catch (err) {
                setError(err);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []); // Empty dependency array means run once on mount

    if (loading) return <div>Loading data...</div>;
    if (error) return <div>Error: {error.message}</div>;

    return (
        <div>
            <h2>Data Fetched:</h2>
            <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
    );
}
```

### Problem: Hook in a Regular JavaScript Function

```javascript
import { useState } from 'react';

// This is a plain JavaScript function. It is NOT a component or a custom hook.
function calculateMetrics(value) {
    // ERROR: Calling useState here will cause an "Invalid hook call".
    // const [metricName, setMetricName] = useState('Default Metric');
    // console.log(`Calculating for ${metricName}: ${value}`);
    return value * 1.2;
}

function DisplayComponent() {
    const total = calculateMetrics(100); // The error happens inside calculateMetrics
    return <div>Total Calculated: {total}</div>;
}
```

### Fix: Create a Custom Hook

```javascript
import { useState, useEffect } from 'react';

// This is a custom hook because its name starts with 'use'
// and it calls other React Hooks internally.
function useMetricsCalculator(initialValue) {
    const [currentValue, setCurrentValue] = useState(initialValue);
    const [metricName, setMetricName] = useState('Custom Metric');

    useEffect(() => {
        console.log(`Metric ${metricName} is being calculated for value: ${currentValue}`);
    }, [currentValue, metricName]);

    const calculateResult = () => currentValue * 1.2;

    return {
        calculatedValue: calculateResult(),
        currentValue,
        setCurrentValue,
        metricName,
        setMetricName
    };
}

function DisplayComponent() {
    // Correct: Calling the custom hook from a function component.
    const { calculatedValue, currentValue, setCurrentValue, metricName, setMetricName } = useMetricsCalculator(50);

    return (
        <div>
            <p>Metric Name: {metricName}</p>
            <p>Input Value: {currentValue}</p>
            <p>Calculated Result: {calculatedValue}</p>
            <button onClick={() => setCurrentValue(prev => prev + 10)}>Increase Input</button>
            <input
                type="text"
                value={metricName}
                onChange={(e) => setMetricName(e.target.value)}
                placeholder="Change metric name"
            />
        </div>
    );
}
```

## Environment-Specific Notes

The "Invalid hook call" error can manifest slightly differently or be harder to diagnose depending on your development and deployment environment.

*   **Local Development (Create React App, Vite, Webpack dev server):** This is where you'll most frequently encounter this error. Hot Module Replacement (HMR) can sometimes get confused, especially after changing dependencies. My first troubleshooting step in local dev is always to perform a clean reinstall of dependencies (`rm -rf node_modules && rm yarn.lock && yarn install`) followed by a full server restart (`yarn start`). Using `npm ls react` or `yarn why react` is invaluable here for pinpointing duplicate `react` packages that your build system might be inadvertently including.
    ```bash
    # Example for local debugging multiple React instances
    npm ls react
    # Or for yarn
    yarn why react
    ```
    Look for output showing different versions or paths for `react` or `react-dom`.

*   **Docker Containers:** If you're building your React application inside a Docker container, ensure that your `node_modules` are properly installed *within* the container. A common mistake is to volume-mount `node_modules` from the host system, which can lead to architecture or dependency mismatches. Build your `node_modules` inside the container reliably using `npm ci` or `yarn install --frozen-lockfile` to ensure exact dependency resolution. I've seen issues arise when a cached Docker layer contains an older `node_modules` and then a new `COPY` command overwrites `package.json` without triggering a fresh install.

    ```dockerfile
    # Recommended Dockerfile approach
    FROM node:18-alpine

    WORKDIR /app

    COPY package.json yarn.lock ./ # Copy only package files first
    RUN yarn install --frozen-lockfile # Install dependencies reliably

    COPY . . # Copy the rest of your app

    RUN yarn build # Build your app
    EXPOSE 3000
    CMD ["yarn", "start"]
    ```

*   **Cloud Deployments (Netlify, Vercel, AWS Amplify):** These platforms typically perform a fresh `npm install` or `yarn install` during their build process. If you encounter the "Invalid hook call" error here but not locally, it often points to a dependency resolution issue that's only triggered in a clean environment. This is where `resolutions` (Yarn) or `overrides` (npm) in your `package.json` become critical for enforcing a single `react` version across all transitive dependencies. Carefully review the build logs for any warnings or errors related to dependency conflicts. In my experience, if it works locally but breaks on cloud, it's frequently a package-lock discrepancy or a subtle difference in Node.js runtime that changes dependency tree resolution.

## Frequently Asked Questions

*   **Q: Can I use `useState` in a helper function if that helper function is called by a function component?**
    *   **A:** No, not directly. Hooks *must* be called directly by a React function component or another custom hook. A regular helper function (one not prefixed with `use`) cannot call `useState`. If your helper function needs state, you should either pass the state and its setter from the parent component, or refactor the helper into a custom hook (e.g., `useMyHelperFunction`).
*   **Q: What if I see this error but I'm absolutely sure I'm only using function components and custom hooks?**
    *   **A:** This is a strong indicator of the "Multiple React Instances" problem. Your application or one of its dependencies is likely bundling React more than once, leading to a situation where your components are using one version of `React` while hooks are being resolved from another. Use `npm ls react` or `yarn why react` to diagnose and enforce a single React version using `resolutions` or `overrides` in your `package.json`.
*   **Q: Does ESLint help prevent this error?**
    *   **A:** Yes, significantly! The `eslint-plugin-react-hooks` package is crucial. Specifically, the `react-hooks/rules-of-hooks` rule is designed to catch violations like calling hooks outside of function components or conditionally. Ensure this plugin is configured and active in your project's ESLint setup. It's an invaluable tool for catching these issues during development, often before you even run your code.
*   **Q: Is it okay to call a hook inside an `if` statement, a `for` loop, or a nested function?**
    *   **A:** No, that violates another fundamental rule of hooks: "Hooks must be called at the top level of your React function component or custom hook." They cannot be called conditionally, inside loops, or within nested functions. React relies on a consistent order of hook calls between renders to correctly associate state and effects. If you need conditional logic, place it *inside* the hook, not around the hook call itself.

## Related Errors
- [react-hydration-error](/errors/react-hydration-error.html)
- [typescript-ts2345](/errors/typescript-ts2345.html)