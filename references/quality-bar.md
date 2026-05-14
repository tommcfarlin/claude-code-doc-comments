# Quality Bar

The standard the doc-comments skill applies when generating and evaluating doc comments. Every generated or refreshed comment is measured against this bar.

The primary consumer is an agent, not a human. Write for that audience.

---

## The Core Test

> Would an agent reading only this doc comment — without reading the implementation — correctly understand the contract well enough to call this function, handle its return value, and avoid triggering its failure conditions?

If yes: the comment meets the bar.
If no: generate or rewrite until it does.

---

## Required Signal

A doc comment must cover all of the following that apply to the symbol:

### 1. Purpose as a Contract

State what the symbol does in terms of its inputs and outputs, not its implementation.

**Pass:**
> Resolves the active subscription tier for a given user. Returns null if no active subscription exists.

**Fail:**
> Queries the subscriptions table, filters by user ID and status, and returns the first matching record.

The first tells an agent what to expect. The second describes implementation the agent can read itself — it adds tokens without adding signal.

### 2. Parameters — Meaning, Not Just Type

Describe what each parameter *represents*, especially when the name alone is ambiguous.

**Pass:**
> `$userId` — The primary key of the user record in the users table.

**Fail:**
> `$userId` — The user ID.

"The user ID" restates the parameter name. It tells the agent nothing it didn't already know.

### 3. Return Value — Meaning and Nullability

State what the returned value represents and, critically, the conditions under which it can be null, empty, or a failure state.

**Pass:**
> Returns the active `SubscriptionTier`, or `null` if the user has no active subscription. Never returns an expired tier.

**Fail:**
> Returns `SubscriptionTier|null`.

The type is already in the signature. The comment needs to tell the agent *when* null is returned and what that means for the caller.

### 4. Side Effects

Document any external state the symbol reads from or writes to that is not expressed by the signature.

Covers: database reads/writes, API calls, cache reads/writes, filesystem operations, session or global state mutations, event emissions.

**Pass:**
> Writes the resolved tier to the local cache. Subsequent calls within the session return the cached value without hitting the database.

**Fail:**
> *(no mention of cache behavior)*

An agent that doesn't know about the cache may make redundant calls or misattribute stale data.

### 5. Throws and Failure Conditions

Document the conditions under which the symbol throws or returns an error, and what type is thrown.

**Pass:**
> Throws `AuthorizationException` if the requesting user does not have read access to the target record.

**Fail:**
> Throws an exception on error.

"On error" tells the agent nothing. The condition and the type are both required.

### 6. Non-Obvious Behavior

Document edge cases, ordering constraints, performance characteristics, or behavioral quirks that are not obvious from the name and signature.

Examples:
- "Does not throw on expired records — returns null instead"
- "Results are sorted by created_at descending; the first item is always the most recent"
- "Performs a synchronous disk read; do not call on the main thread"
- "Safe to call multiple times; subsequent calls are no-ops"

---

## What to Omit

### Restatements of the Name

If the comment says nothing the function name doesn't already say, it is noise.

**Omit:**
```php
// Gets the user.
public function getUser(int $id): User
```

**Keep only if there is additional contract information:**
```php
/**
 * Retrieves a user by primary key.
 *
 * @param  int   $id  The primary key of the user record.
 * @return User       Always returns a hydrated User. Throws if not found.
 * @throws UserNotFoundException  If no record exists for the given ID.
 */
```

### Implementation Description

If the comment describes *how* the function works rather than *what it contracts*, it describes the wrong thing.

**Omit:**
> Iterates over the results array, checks each item's status field against the allowed statuses list, and appends matching items to the output array.

**Keep:**
> Returns only items with an allowed status. Items with unknown or deprecated statuses are excluded without error.

### Boilerplate With No Signal

Do not generate comments that exist only to satisfy a coverage requirement. A symbol with no meaningful contract information beyond its name and typed signature should be skipped rather than documented with noise.

---

## Stale Comment Standard

A comment is **stale** if any of the following are true:

- A parameter documented in the comment no longer exists in the signature
- A parameter in the signature is not documented in the comment
- The return type or nullability documented does not match the current implementation
- A side effect is documented that the function no longer performs
- A side effect exists that the comment does not mention
- A throws condition documented no longer applies
- A throws condition exists that is not documented

**Stale is worse than missing.** An agent that reads a stale comment and acts on it confidently produces incorrect output. When a comment is stale, replace it entirely rather than patching inline.
