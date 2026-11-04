I found one serious problem: any logged-in user can read another tenant's confidential documents through the export route.

**Scope:** I read `deployment.md`, `routes.py.txt`, `service.py.txt` and `storage.py.txt`, and followed both routes from the router through the service to the database query. There is no immutable revision; these are supplied text excerpts. Static inspection only: nothing was run, no network was used, nothing was installed and no files were changed.

## Findings

### 1. The export route skips the tenant check — High severity, High confidence

**Where:**
- The route handler at `routes.py.txt:14-19` calls `ctx.documents.export(document_id)` and never passes `ctx.tenant_id`.
- `service.py.txt:8-9` passes that call straight to `storage.find_by_id(document_id)`.
- The query at `storage.py.txt:12-17` filters only by `WHERE id = ?`. It returns `id`, `tenant_id`, `title` and the confidential `body`.
- `response.json(row)` sends that whole row back to the caller.

**Comparison:** `/documents/{document_id}` takes the safe path. It goes through `read_for_tenant` → `find_for_tenant`, whose query adds `AND tenant_id = ?` using the session's trusted `ctx.tenant_id` (`storage.py.txt:7`). For another tenant's ID it returns not-found. `/exports/{document_id}` returns the same row with no tenant check.

**Why other layers don't stop it:** `deployment.md` says the router only checks that the session is valid. It also says there is no separate route authorization, no database row policy, no proxy and no tenant filter beyond these files. So nothing outside these files limits the export route to the caller's tenant.

**Attacker requirements:** anyone can self-register on this public service and get a valid session. They also need another tenant's document ID. `deployment.md` says such IDs appear in shared public activity events.

**What it exposes:** for each document ID the attacker obtains, they get that document's title, body and owning tenant. This breaks tenant isolation for confidential data. The supplied evidence does not show a way to list or guess IDs beyond those public events, because the IDs are described as opaque. So the exposure is every document whose ID becomes known, not proven bulk access to all documents.

**Fix:** make the export path take the tenant into account:
```python
# routes.py
row = ctx.documents.export(ctx.tenant_id, document_id)
# service.py
def export(self, tenant_id, document_id):
    return self.storage.find_for_tenant(tenant_id, document_id)
```
Also remove or rename `find_by_id`, or limit it to clearly internal callers, so it can't be wired to a request handler again.

**Check the fix with a test:** create two tenants, A and B, each with one document. While logged in as A:
- `GET /exports/{B_doc_id}` should return not-found.
- `GET /exports/{A_doc_id}` should still return A's document.

Add the same pair of checks for `/documents/{id}` as a regression guard.

## Not a finding
- **SQL injection:** both queries use bound `?` parameters. No injection path shown.
- **`/documents/{document_id}`:** correctly limited to the caller's tenant, given `deployment.md`'s statement that `ctx.tenant_id` comes from the trusted session.

## Coverage and limits
- All four supplied files were reviewed. The authentication middleware, session handling, router, `response` helpers, database schema and wider deployment were not provided. I relied on `deployment.md`'s statements about them and did not verify them.
- Nothing was confirmed at runtime; the finding rests on static tracing alone.
- I can't rate the overall risk of the whole application from this packet.

**Next step:** apply the tenant check to the export route and add the two-tenant test above.
