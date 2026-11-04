# Security review: input.md (synthetic packet)

**Scope:** The three artifacts L, M and N in `input.md`, each judged against its own contract. I only read the source and contracts. I ran nothing, made no network requests and changed no files. There is no repository revision or running service, so every conclusion below rests on the supplied code and contract text.

---

## Artifact L: record-summary handler

**Result: No substantiated finding. Needs validation.**

**What the code shows:** `record_summary` (input.md:8–11) passes a caller-chosen `record_id` straight to `ctx.records.describe(record_id)` and returns whatever comes back. The handler body never refers to `ctx.user` or `ctx.tenant_id`.

**Relevant controls:** The router authenticates every request and supplies a trusted `ctx.user` and `ctx.tenant_id`. Authentication alone doesn't prove the caller may see a given record. Per the contract, an ordinary account can supply a valid foreign-tenant `record_id`.

**Why it isn't a finding:** The contract says it "is unknown whether the service object is already tenant-scoped." It also says it's unknown "which fields `describe` returns" and "how it handles missing or inaccessible records." If `ctx.records` is tenant-scoped, the handler is safe. Without that fact, cross-tenant exposure isn't established.

**Open questions:**
- Is `ctx.records` bound to `ctx.tenant_id` or `ctx.user`? Check how `ctx.records` is built and how `describe` filters records.
- If it isn't scoped, does `describe` return sensitive fields for a foreign record?
- Does `response.json` reveal whether a record exists, through its status code or error body?

**Bounded next check:** Test with two tenants. As a tenant A account, request a tenant B `record_id` and confirm the response is a 403 or 404 that reveals nothing about B's record. If the service turns out not to be scoped, add an explicit ownership check in the handler or the service against `ctx.tenant_id`.

---

## Artifact M: queue-worker policy endpoints

### Finding M-1: Any self-registered account can turn off tenant isolation and read other tenants' confidential job data

| | |
|---|---|
| **Severity** | High |
| **Confidence** | High (every link in the chain is stated in the contract) |
| **Location** | `set_policy` and `activate_policy` (input.md:19–30) |

**What an attacker can do:**
1. Anyone can create an account, because the service is internet-facing and offers self-registration.
2. `require_login` checks only for a valid session and "imposes no role requirement." No other route, proxy or admin-approval check exists.
3. `PUT /policy` with `{"isolate_tenants": false}` passes the boolean validation, and `policy_store.save` stores it as the candidate policy.
4. `POST /policy/reload` calls `policy_store.activate()`, which "immediately" makes that candidate the worker's active policy.
5. With isolation off, the worker data API returns any requested job "regardless of tenant." The response includes `id`, `tenant_id` and the confidential `private_payload`.
6. The attacker learns a valid foreign-tenant job ID from the public job-completion event and gets back the other tenant's `private_payload`.

**Supported consequence:** An unprivileged account turns off tenant isolation for the whole service. Two things follow:
- **Integrity:** the setting is unauthorized and affects every tenant.
- **Confidentiality:** the attacker can read another tenant's confidential `private_payload` for any job ID they know. Once activated, the same exposure applies to every authenticated account, not just the attacker.

**Limits on this rating:**
- The contract supplies a way to learn job IDs one at a time from public events. It doesn't show the attacker can list or enumerate all jobs, so I rate only access to known IDs.
- The service runs as an ordinary application user, and no host or other-service privileges are described. That's why I rate it High, not Critical.

**Fix:**
- Add a policy-administrator role check to both handlers, enforced from the server-side session. This is the same control Artifact N uses.
- As defence in depth, have the worker data API check that the job's tenant matches the caller's tenant on every request, even when `isolate_tenants` is false. One global flag then can't expose every tenant.
- Consider logging and alerting on policy changes.

**Verification:**
- As an ordinary account, call `PUT /policy` and `POST /policy/reload`. Both should return 403, and the active policy should be unchanged.
- As tenant A, request a tenant B job ID from the worker API. It should be rejected under every policy state.

---

## Artifact N: queue-worker policy endpoints with admin check

**Result: No substantiated security findings in the reviewed scope.**

**Controls in place:**
- `@require_policy_admin` runs before both handler bodies (input.md:42, 50). It checks a policy-administrator role from the verified server-side session and rejects every ordinary account with a 403.
- The contract explicitly rules out the bypass routes:
  - assigning the role to oneself
  - tampering with another account's session
  - writing the policy store by another route
  - activating a candidate by another mechanism
- When an administrator deliberately sets `isolate_tenants: false`, that's an authorized change, and the contract states no attacker controls an administrator account.

**Optional hardening, not a vulnerability:** The worker API still relies on one global flag for tenant isolation. A per-request tenant check there would limit the damage from an administrator's mistake or a future compromise. Logging every save and activation would also help.

---

## Review coverage and limits

- **Inspected:** The three code fragments and their contracts. I focused on authorization, tenant isolation and how the policy activation path is reached.
- **Not available:**
  - the implementations of `ctx.records`, `describe`, `response.json`, `require_login`, `require_policy_admin`, `policy_store` and the worker API
  - the framework
  - deployment details
- **Not done:** I ran no code, made no requests, did no dynamic testing and changed no files.
- **Overall risk:**
  - M: High, based on the supplied contract.
  - L and N: unrated beyond what's stated above. L has insufficient context; N has no supported finding.
