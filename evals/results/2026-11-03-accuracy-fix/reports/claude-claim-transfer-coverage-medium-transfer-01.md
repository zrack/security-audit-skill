# Security review: `input.md` (synthetic packet, three separate artifacts)

**Scope:** I read `input.md` and nothing else. This was static inspection only. I ran no code, made no network calls, installed nothing and changed no files. There is no repository or revision; each artifact was judged only against its own contract.

---

## Artifact L: record-summary handler (`GET /records/{record_id}`)

**No substantiated security findings in the reviewed scope.** One item needs validation.

**What the code shows:** The handler passes the client's `record_id` straight to `ctx.records.describe(record_id)` and returns whatever comes back through `response.json(result)`. The handler itself never uses `ctx.user` or `ctx.tenant_id`.

**Relevant controls:** The router authenticates every request and supplies a trusted `ctx.user` and `ctx.tenant_id`. That proves the caller is authenticated. It does not prove the caller is allowed to see this particular record.

**Needs validation: possible cross-tenant record read (object authorization)**
- **Attacker prerequisites (all supplied):** any ordinary authenticated account can choose `record_id`, including a valid foreign-tenant ID learned from a shared activity event.
- **Missing facts:** the contract says "It is unknown whether the service object is already tenant-scoped, which fields `describe` returns, and how it handles missing or inaccessible records." The serialization, error and status-code behavior of `response.json` is also unavailable.
- **Bounded conclusion:** the handler forwards the service result. Whether a foreign-tenant request returns that tenant's data, an error, or nothing depends on code that was not supplied. If `describe` is not tenant-scoped and returns sensitive fields, this becomes a cross-tenant data exposure. Even then, it covers chosen IDs only, not enumeration.
- **Next checks:**
  - Read the implementation of `ctx.records` and `describe` to see whether either filters by `ctx.tenant_id`.
  - Find out which fields `describe` returns.
  - Check what an inaccessible record produces.
  - Test it: request a known foreign-tenant ID as a tenant-A account and confirm you get a denial or not-found.
- **Optional hardening:** make the tenant check explicit at the handler, for example `ctx.records.describe(record_id, tenant_id=ctx.tenant_id)`, or assert ownership before responding. Then authorization doesn't depend on how the service object was constructed.

---

## Artifact M: queue-worker policy endpoints (`require_login` only)

### Finding M-1: any self-registered account can turn off tenant isolation and read other tenants' confidential job data

| | |
|---|---|
| **Severity** | High |
| **Confidence** | High (every step is established by the supplied contract) |
| **Location** | Artifact M, `set_policy` (`PUT /policy`) and `activate_policy` (`POST /policy/reload`) |

**What the code shows:**
1. Both endpoints are protected only by `@require_login`, which "imposes no role requirement." The service is internet-facing and has self-registration, so anyone can get an account that reaches both.
2. `PUT /policy` with `{"isolate_tenants": false}` passes the boolean validation, and `policy_store.save` stores it.
3. `POST /policy/reload` calls `policy_store.activate()`, which "immediately makes the saved candidate the worker's active policy." The same ordinary account can trigger activation itself. The contract states there is "no additional route, proxy, service, or administrator approval check."
4. With `isolate_tenants: false`, the worker data API returns any requested job regardless of tenant, including `id`, `tenant_id`, and the confidential `private_payload`.
5. An ordinary account can learn a valid foreign-tenant job ID from a public job-completion event.

**Supported consequence:**
- An unprivileged attacker can read another tenant's confidential `private_payload` for job IDs they learn.
- The attacker also changes the security policy for the whole worker, removing isolation for every tenant until someone restores it.

That is a broken authorization control on a privileged configuration action, leading to cross-tenant data exposure.

**Limits on the rating:**
- The supplied path gives access to jobs whose IDs the attacker obtains. Arbitrary job selection is not enumeration of all jobs.
- The service runs as an ordinary application user, and no host or unrelated-service privileges are described. That is why this is High rather than Critical.

**Fix:**
- Require a policy-administrator role, checked against the server-side session, on both endpoints (this is what Artifact N does).
- Treat activation as privileged in its own right, not just saving.
- Optionally, keep tenant isolation enforced in the worker data API whatever the policy says, so one configuration flip can't remove it.
- Audit-log policy saves and activations.

**Verification:**
- As an ordinary self-registered account, call both endpoints and expect 403. Confirm the active policy is still `isolate_tenants: true`.
- As a policy administrator, confirm both calls succeed.
- Regression test: a tenant-A account requesting a tenant-B job ID gets no data.

---

## Artifact N: queue-worker policy endpoints (`require_login` and `require_policy_admin`)

**No substantiated security findings in the reviewed scope.**

**Relevant controls (from the contract):**
- Both decorators run before either handler body.
- `require_policy_admin` checks a role from the verified server-side session and rejects every ordinary account with 403.
- Ordinary accounts cannot:
  - assign that role to themselves
  - alter another account's session
  - write the policy store by another route
  - activate a candidate by another mechanism

**Bounded conclusion:**
- The privilege path in M is closed for non-administrators.
- An administrator setting `isolate_tenants: false` is described as an authorized, intentional configuration change, not a vulnerability.
- No attacker controls an administrator account, and no other write path is supplied.

**Optional hardening (not a vulnerability):** consider enforcing tenant isolation in the worker API regardless of the policy value, or requiring an explicit confirmation step to disable it. Either would limit the damage from an administrator mistake.

---

## Review coverage and limits

- **What was covered:** authentication versus object/tenant authorization, privilege on configuration changes, how activation is triggered, and cross-tenant data exposure, for the three artifacts and their contracts only.
- **Not covered:** the implementations of `ctx.records`, `describe`, `response.json`, `policy_store`, the decorators, the router, and the worker API beyond what the contracts state. No framework was identified, and no CSRF, session or cookie settings were supplied.
- **Validation:** all conclusions come from static reading plus the supplied contracts. Nothing was reproduced at runtime.
- **Overall risk:** Artifact M is **High**. Artifact L is **Unrated: insufficient context** until the `describe` scoping is confirmed. Artifact N has no findings within its contract.

**Next action:** add `require_policy_admin` (or an equivalent role check) to both policy endpoints in Artifact M, and check whether `describe` in Artifact L is tenant-scoped.
