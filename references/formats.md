# Doc Comment Formats

Per-language syntax reference for the doc-comments skill. When generating or refreshing a doc comment, use the format that matches the file's language. Never apply one language's format to another.

---

## PHP — DocBlock

**Extensions:** `.php`

**Syntax:**

```php
/**
 * Brief statement of the contract — what this does, not how.
 *
 * Expand here if the contract has non-obvious behavior, side effects,
 * edge cases, or ordering constraints that aren't clear from the signature.
 *
 * @param  Type   $name  What this value represents, not just its type.
 * @param  Type   $name  Use multiple @param lines, one per parameter.
 *
 * @return Type  What the returned value represents. If nullable, say so and why.
 *
 * @throws ExceptionType  Condition under which this is thrown.
 *
 * @side-effect  Describe any write to DB, API call, cache mutation, or global state.
 */
```

**Rules:**
- Opening `/**` on its own line
- Each line prefixed with ` * `
- Closing ` */` on its own line
- One blank line between the description block and the tag block
- `@param` tags aligned for readability
- Use `@side-effect` (custom tag) when the function writes to external state — database, filesystem, API, cache, session

**Example:**

```php
/**
 * Resolves the active subscription tier for a given user.
 *
 * Returns null if the user has no active subscription. Does not throw
 * on expired subscriptions — returns null instead.
 *
 * @param  int  $userId  The primary key of the user record.
 *
 * @return SubscriptionTier|null  The active tier, or null if none exists.
 *
 * @side-effect  Reads from the subscriptions table. No writes.
 */
```

---

## Swift — Documentation Comment

**Extensions:** `.swift`

**Syntax:**

```swift
/// Brief statement of the contract — what this does, not how.
///
/// Expand here if the contract has non-obvious behavior, side effects,
/// edge cases, or ordering constraints that aren't clear from the signature.
///
/// - Parameters:
///   - name: What this value represents, not just its type.
///   - name: One entry per parameter.
/// - Returns: What the returned value represents. If optional, say so and why.
/// - Throws: Condition under which this throws and what error type.
/// - Note: Side effects, ordering constraints, or non-obvious behavior.
```

**Rules:**
- Use `///` triple-slash format (not `/** */` block style)
- `- Parameters:` block with indented `- name:` entries for multiple params
- For a single parameter, use `- Parameter name:` instead
- Use `- Note:` for side effects and non-obvious behavior
- Use `- Important:` for contract constraints that are easy to violate

**Example:**

```swift
/// Resolves the active subscription tier for the given user ID.
///
/// Returns `nil` if the user has no active subscription. Does not throw
/// on expired subscriptions.
///
/// - Parameter userID: The unique identifier of the user record.
/// - Returns: The active `SubscriptionTier`, or `nil` if none exists.
/// - Note: Performs a synchronous read from the local data store. Do not call on the main thread.
```

---

## JavaScript — JSDoc

**Extensions:** `.js`, `.mjs`, `.cjs`

**Syntax:**

```javascript
/**
 * Brief statement of the contract — what this does, not how.
 *
 * Expand here if the contract has non-obvious behavior, side effects,
 * edge cases, or ordering constraints that aren't clear from the signature.
 *
 * @param {Type} name - What this value represents, not just its type.
 * @param {Type} [name] - Square brackets indicate optional parameter.
 * @param {Type} [name=default] - Include default value if meaningful.
 *
 * @returns {Type} What the returned value represents. If nullable, say so.
 *
 * @throws {ErrorType} Condition under which this throws.
 *
 * @async - Include if the function returns a Promise.
 */
```

**Rules:**
- Same block structure as PHP (`/**`, ` * `, ` */`)
- Use `@returns` (not `@return`)
- Wrap types in curly braces: `{string}`, `{number}`, `{User|null}`
- Mark optional params with square brackets: `{string} [label]`
- Add `@async` tag on async functions
- Use `@deprecated` with a reason and migration note when applicable

**Example:**

```javascript
/**
 * Resolves the active subscription tier for a given user.
 *
 * Returns null if the user has no active subscription. Does not throw
 * on missing records — resolves null instead.
 *
 * @param {number} userId - The primary key of the user record.
 *
 * @returns {Promise<SubscriptionTier|null>} The active tier, or null if none exists.
 *
 * @async
 */
```

---

## TypeScript — JSDoc with Types

**Extensions:** `.ts`, `.tsx`

**Syntax:**

Same as JavaScript JSDoc. In TypeScript, type annotations in the signature are the source of truth — doc comment types should match but do not need to be exhaustive if the signature is clear.

**Rules (TypeScript-specific):**
- Omit `{Type}` from `@param` and `@returns` when the TypeScript signature is fully typed and unambiguous. Focus the tag on *what the value means*, not its type.
- Include `{Type}` when the type is a union, generic, or otherwise non-obvious from the signature alone.
- Always document nullable returns and thrown errors even when types are explicit — the *condition* under which null is returned is not expressed by the type system.

**Example:**

```typescript
/**
 * Resolves the active subscription tier for a given user.
 *
 * Returns null if the user has no active subscription. Does not throw
 * on missing records.
 *
 * @param userId - The primary key of the user record.
 * @returns The active tier, or null if no active subscription exists.
 */
```

---

## Adding a New Language

To add support for a new language:

1. Add a section to this file following the pattern above
2. Include: file extensions, syntax example, rules, and a concrete example
3. Update the `## Supported Languages` section in `README.md`
