# TypeScript TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'
> Encountering `TS2345` means a value's type doesn't match the expected parameter type; this guide explains how to fix it.

As an API & Integration Engineer, few error messages are as ubiquitous as `TS2345` when working with TypeScript. This compile-time error is TypeScript's way of telling you, "Hold on, the data you're trying to use here isn't the shape or type I expected for this operation." It's a cornerstone of TypeScript's type safety, designed to catch potential runtime bugs before your code even executes.

### What This Error Means

`TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'` directly translates to: "You tried to pass a value whose inferred or declared type is `X` into a function (or constructor, or method) that expects a parameter of type `Y`." The TypeScript compiler has detected a mismatch. It's not a suggestion; it's a mandatory correction before compilation can successfully complete.

This error is a good thing! It's TypeScript protecting you from potential runtime errors that would typically manifest as `TypeError` or unexpected behavior in dynamically typed JavaScript. It ensures that the contracts you've defined for your functions and data structures are being honored, which is especially critical in complex API integrations where data schemas are paramount.

### Why It Happens

At its core, `TS2345` occurs because of a disconnect between what you *intend* to pass and what TypeScript *expects* based on your type definitions. TypeScript rigorously checks every piece of data flowing through your application against the types you've established. When it finds a deviation, it flags `TS2345`.

This strictness is intentional. Imagine an API integration where a service expects a `user_id` as a number, but you inadvertently pass it as a string. In plain JavaScript, this might lead to subtle issues: a database query failing, an ID not being properly matched, or a type-sensitive algorithm producing incorrect results. TypeScript prevents this by forcing you to address the type mismatch at compile time, ensuring data integrity and predictable behavior. In my experience, `TS2345` has saved me countless hours of debugging downstream system failures that would have been incredibly hard to trace back to a simple type error.

### Common Causes

While the error message is generic, the underlying causes often fall into a few categories:

1.  **Simple Type Mismatch:** This is the most straightforward case. You might pass a `string` where a `number` is expected, or a `boolean` instead of an `object`.
    ```typescript
    function greet(name: string) { /* ... */ }
    greet(123); // TS2345: Argument of type 'number' is not assignable to parameter of type 'string'.
    ```

2.  **Incorrect Interface or Type Usage:** When working with objects, you might pass an object that doesn't fully conform to the expected interface or type alias. This could mean missing required properties, having extra unexpected properties (if strict object literal checks are enabled), or properties having the wrong type themselves.
    ```typescript
    interface User {
        id: number;
        name: string;
    }
    function createUser(user: User) { /* ... */ }
    createUser({ name: "Alice" }); // TS2345: Property 'id' is missing...
    ```

3.  **Union Types Not Handled:** If a parameter expects a union type (e.g., `string | number`), but your argument is of a type not explicitly included in the union, or you're trying to use a union type without narrowing it first.
    ```typescript
    type Status = 'active' | 'inactive';
    function setStatus(status: Status) { /* ... */ }
    setStatus('pending'); // TS2345: Argument of type '"pending"' is not assignable to parameter of type 'Status'.
    ```

4.  **Asynchronous Operations and Promises:** Promises often resolve to a specific type. If you assign the result of a promise (or an `async` function) without correctly typing the awaited value, you might encounter `TS2345`.
    ```typescript
    async function fetchData(): Promise<string> {
        return "data";
    }
    async function processData() {
        const data = await fetchData(); // 'data' is inferred as string
        // function takes a number
        // processNumber(data); // TS2345 if processNumber expects number
    }
    ```

5.  **External Library/API Mismatches:** Sometimes, the TypeScript declaration files (`.d.ts`) for a third-party library might not perfectly reflect its runtime behavior, or you might be using a function incorrectly according to its definition. This is less common but can be tricky.

6.  **`any` Type Implicitly or Explicitly:** If you've used `any` somewhere upstream, TypeScript loses its ability to track the type. When this `any` value is then passed to a strictly typed parameter, `TS2345` can appear, forcing you to reconsider the actual type.

### Step-by-Step Fix

Debugging `TS2345` is a systematic process. I usually follow these steps:

1.  **Read the Error Message Precisely:**
    The error provides crucial information: `Argument of type 'X' is not assignable to parameter of type 'Y'`.
    *   **Identify `X`:** This is the *actual* type of the value you're trying to pass.
    *   **Identify `Y`:** This is the *expected* type for the parameter.
    *   **Locate the Error:** The file name and line number are your starting point.

2.  **Inspect the Function Signature:**
    Go to the definition of the function, method, or constructor causing the error. What type does the specific parameter (`Y`) actually expect? Is it `string`, `number`, a custom interface, a union type? Use your IDE's "Go to Definition" feature.

3.  **Inspect the Argument Type (`X`):**
    Examine the variable or literal you are passing as the argument. What is its inferred type? Hovering over the variable in your IDE (like VS Code) will often show its inferred type. If it's a complex object, inspect its properties.

4.  **Identify the Discrepancy:**
    Compare `X` and `Y`. Where do they differ?
    *   Is it a primitive type mismatch (e.g., `string` vs. `number`)?
    *   Is it an object shape mismatch (missing properties, extra properties, wrong property types)?
    *   Is it a union type that hasn't been narrowed?

5.  **Apply a Fix Strategy:**

    *   **Option A: Modify the Argument (Most Common & Recommended):**
        Transform `X` to match `Y`. This is usually the safest and most robust solution because it ensures the data truly conforms to the expectation.
        *   **Type Conversion:** If `X` can be logically converted to `Y`.
            ```typescript
            // If X is 'string' and Y is 'number'
            const stringId = "123";
            const numericId = Number(stringId); // Transform string to number
            // pass numericId
            ```
        *   **Object Restructuring/Mapping:** If `X` is an object, but `Y` expects a slightly different shape. Create a new object that matches `Y`.
            ```typescript
            interface ApiUser { id: string; name: string; email: string; }
            interface LocalUser { userId: number; fullName: string; }
            const apiUser: ApiUser = { id: "1", name: "Alice", email: "a@b.com" };

            // Function expects LocalUser
            function processLocalUser(user: LocalUser) { /* ... */ }

            // Transform apiUser to LocalUser
            const localUser: LocalUser = {
                userId: Number(apiUser.id),
                fullName: apiUser.name,
            };
            processLocalUser(localUser);
            ```
        *   **Type Guards / Narrowing:** If `Y` is a union type and `X` is also a union, but you need to ensure `X` matches a specific part of `Y`.
            ```typescript
            type IdType = number | string;
            function displayId(id: number) { /* ... */ }
            const myId: IdType = "456";

            if (typeof myId === 'number') {
                displayId(myId); // myId is narrowed to 'number' here
            } else {
                displayId(Number(myId)); // Or convert if it's safe to assume
            }
            ```

    *   **Option B: Modify the Parameter Type (If Appropriate):**
        If `X` is indeed a valid input for the function's logic, but the parameter `Y` is too restrictive, you might consider broadening `Y`. This should be done cautiously, as it impacts all callers of the function.
        ```typescript
        // Original: function acceptId(id: number)
        // If you truly need to accept strings that can be parsed to numbers:
        function acceptId(id: number | string) {
            const numericId = typeof id === 'string' ? Number(id) : id;
            // Now handle numericId
        }
        ```

    *   **Option C: Type Assertion (`as Y` or `<Y>X`) - Use with Caution!**
        This is "telling TypeScript you know better." It bypasses the type checker. Only use this when you are absolutely certain that at runtime, `X` *will* be of type `Y`, and TypeScript simply can't infer it (e.g., from a dynamic API response you've validated at runtime). Overuse leads to potential runtime errors.
        ```typescript
        const rawData: any = { status: "active" };
        interface WidgetStatus { status: 'active' | 'inactive'; }
        // setWidgetStatus(rawData); // TS2345: Argument of type 'any' is not assignable to type 'WidgetStatus'.
        setWidgetStatus(rawData as WidgetStatus); // "Trust me, TypeScript, it's a WidgetStatus"
        ```

6.  **Recompile and Test:**
    After applying a fix, recompile your project. Ensure the `TS2345` error is gone and that your application functions as expected. It's not uncommon for a fix to one type error to reveal another downstream!

### Code Examples

Here are some concise examples demonstrating common `TS2345` scenarios and their fixes.

```typescript
// --- Example 1: Primitive Type Mismatch ---

function processMeasurement(value: number): void {
  console.log(`Measurement: ${value} units`);
}

const stringValue = "150";
// TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
// processMeasurement(stringValue); // Error line

// Fix: Convert the string to a number
processMeasurement(Number(stringValue));
// Or, if you control the function and it's truly meant to handle both:
// function processMeasurement(value: number | string): void { /* ... */ }


// --- Example 2: Interface Mismatch (Missing Property) ---

interface Product {
  id: string;
  name: string;
  price: number;
}

function displayProductDetails(product: Product): void {
  console.log(`Product: ${product.name} (${product.id}) - $${product.price}`);
}

const incompleteProduct = { id: "P001", name: "Laptop" };
// TS2345: Property 'price' is missing in type '{ id: string; name: string; }'
// but required in type 'Product'.
// displayProductDetails(incompleteProduct); // Error line

// Fix: Provide all required properties
const completeProduct = { id: "P001", name: "Laptop", price: 1200.50 };
displayProductDetails(completeProduct);


// --- Example 3: Union Type - Missing Narrowing ---

type UserIdentifier = { type: 'email'; value: string } | { type: 'id'; value: number };

function fetchUserByEmail(email: string): void {
  console.log(`Fetching user by email: ${email}`);
}

const userLookup: UserIdentifier = { type: 'id', value: 12345 };
// TS2345: Argument of type '{ type: "id"; value: number; }' is not assignable
// to parameter of type 'string'.
// Property 'email' is missing... (indirectly)
// fetchUserByEmail(userLookup); // Error line (userLookup isn't directly a string)

// Fix: Use a type guard to narrow the union type
if (userLookup.type === 'email') {
  fetchUserByEmail(userLookup.value);
} else {
  console.warn("User lookup is by ID, not email.");
  // You would call a different function here, e.g., fetchUserById(userLookup.value);
}


// --- Example 4: Type Assertion (Use with extreme caution) ---
// When you are SURE about the type, but TypeScript cannot infer it.

interface Configuration {
  apiUrl: string;
  timeout: number;
}

// Imagine this comes from a very dynamic source, like an environment variable parser
const rawConfig: any = { apiUrl: "https://api.example.com", timeout: 5000 };

function initializeSystem(config: Configuration): void {
  console.log(`Initializing with API: ${config.apiUrl}, Timeout: ${config.timeout}`);
}

// initializeSystem(rawConfig); // TS2345: Argument of type 'any' is not assignable...

// Fix: Assert the type (use only if you've validated 'rawConfig' externally)
initializeSystem(rawConfig as Configuration); // "I promise it's a Configuration!"
```

### Environment-Specific Notes

`TS2345` is a compile-time error, meaning it largely manifests before runtime. However, how you encounter and address it can differ slightly based on your development and deployment environment.

*   **Local Development:** This is where you'll see `TS2345` most frequently. Your IDE (like VS Code) will highlight these errors in real-time as you type, often with helpful quick-fix suggestions. Running `tsc --watch` in your terminal provides continuous feedback, recompiling on file changes. I recommend fixing these as they appear; ignoring them means your `tsc` build command will fail.

*   **CI/CD Pipelines:** In a continuous integration/continuous deployment pipeline, your build step will typically include `tsc --noEmit` or `tsc --build`. Any `TS2345` errors will cause the build to fail, preventing un-typable code from being merged or deployed. I've seen this in production when a critical type definition was changed but not all dependent code was updated, leading to a blocked deployment. This is a crucial gate for code quality and stability, especially for API integrations where consistent data contracts are paramount. Ensure your `tsconfig.json` settings are consistent across local and CI environments to avoid surprises.

*   **Docker Containers:** If you're building your TypeScript application inside a Docker container, `TS2345` errors will manifest during the build stage (e.g., in your `Dockerfile` during `npm run build` or `tsc`). Ensure that your `node_modules` are correctly installed and that your `tsconfig.json` paths align with the container's file system. Differences in Node.js versions or even `npm` vs. `yarn` in the build environment versus local can sometimes subtly affect package resolution and expose type errors that weren't obvious locally.

*   **Cloud Functions/Serverless (AWS Lambda, Azure Functions, Google Cloud Functions):** For serverless deployments, you almost always pre-compile your TypeScript code to JavaScript before deploying. `TS2345` errors will be caught during this pre-compilation step. If your CI/CD pipeline correctly runs `tsc` before packaging the function, these errors will prevent deployment. It's rare to see `TS2345` directly in a running cloud function unless you're attempting to compile TypeScript on the fly within the function's runtime, which is highly discouraged for performance and security reasons.

### Frequently Asked Questions

**Q: Can I ignore this error and deploy my code?**
**A:** No, `TS2345` is a compile-time error. TypeScript will actively prevent your code from compiling to JavaScript if these errors exist (unless you're using a very permissive `tsconfig.json` that allows emitting JavaScript even with errors, which is generally a bad practice). It's designed to stop you dead in your tracks until the type contract is honored.

**Q: Is using `any` a good workaround for `TS2345`?**
**A:** Using `any` bypasses TypeScript's type checking entirely. While it will suppress `TS2345`, it defeats the purpose of TypeScript and reintroduces the very runtime errors TypeScript aims to prevent. Use `any` only as a last resort for truly dynamic data that cannot be typed, or as a temporary placeholder during rapid development. In my experience, relying on `any` is a quick way to introduce tech debt and future debugging headaches.

**Q: How can I debug a complex `TS2345` error where the types are very long or nested?**
**A:** Break down the types. Hover over the variable and the parameter in your IDE to see their full inferred types. Sometimes the error is deeply nested within an object. You can create temporary `type Alias = typeof myVariable;` aliases to inspect the inferred type in isolation. Look at the specific properties or union members that are causing the mismatch. Often, a single missing or mistyped property is the culprit.

**Q: Why does this error occur even if the JavaScript code would run without issue?**
**A:** TypeScript's primary goal is to catch potential runtime errors *statically*, before your code runs. JavaScript is dynamically typed, meaning it performs type checks at runtime. While `greet(123)` might execute in JavaScript, the `typeof` check or subsequent operations on that `name` variable might fail or produce unexpected results. TypeScript aims to prevent this category of bugs by enforcing type contracts at compile time.

**Q: What's the difference between `X as Y` and `<Y>X` for type assertion?**
**A:** Both `X as Y` and `<Y>X` are equivalent syntaxes for type assertion in TypeScript. They perform the same function: telling the compiler to treat `X` as type `Y`. The `as` syntax is generally preferred in `.tsx` files (React components) to avoid ambiguity with JSX syntax, which also uses angle brackets. For consistency, `as` is often used everywhere.

### Related Errors
*   [typescript-ts2339](/errors/typescript-ts2339.html)
*   [python-typeerror](/errors/python-typeerror.html)