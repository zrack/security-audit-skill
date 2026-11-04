The `/exports/{document_id}` route lets a signed-in user of one tenant read any other tenant's document, including its confidential body. That is the one finding, rated High.

**Scope:** I read `deployment.md`, `routes.py.txt`, `service.py.txt` and `storage.py.txt` statically and traced each route through the service and storage code. I ran nothing, used no network, installed nothing and changed no files. The files have no revision ID; I reviewed them as they are in the workspace. For things the code can't show, I relied on the guarantees in `deployment.md`: `authenticate` runs before both routes, `ctx.tenant_id` comes from a trusted server-side session, and there is no other tenant filter.

## Finding

### High — Export route skips the tenant check (High confidence)

**Locations:** `routes.py.txt:14-19`, `service.py.txt:8-9`, `storage.py.txt:12-17`

**How the call runs:**
1. `export_document(ctx, document_id)` calls `ctx.documents.export(document_id)`. It never passes `ctx.tenant_id`.
2. `DocumentService.export` calls `storage.find_by_id(document_id)`.
3. `find_by_id` runs `SELECT id, tenant_id, title, body FROM documents WHERE id = ?`, which looks only at the ID.
4. The route returns the whole row with `response.json(row)`.

**For comparison:** `/documents/{document_id}` (`routes.py.txt:7-12`) goes through `read_for_tenant` and `find_for_tenant`, which filter on `id = ? AND tenant_id = ?`. So the intended rule is clear, and only the export route skips it. `deployment.md` says no other layer checks tenants, and nothing else in the call path does either.

**What an attacker needs:**
- **A valid session.** `deployment.md` says ordinary users can sign themselves up into a tenant.
- **Another tenant's document ID.** The IDs are opaque and not assumed to be sequential, so this is not an enumeration attack. But `deployment.md` says a tenant "can learn the identifier of another tenant's document from a shared public activity event."

**What it costs:** The other tenant's `title` and confidential `body` are disclosed. The route is read-only, so it allows no changes.

**Fix:** Make export tenant-scoped the same way reads are:
- In the route, call `ctx.documents.export(ctx.tenant_id, document_id)`.
- In the service, change it to `def export(self, tenant_id, document_id): return self.storage.find_for_tenant(tenant_id, document_id)`.
- Remove `find_by_id`, or keep it out of anything a request can reach.

**How to check the fix:** Add a test with tenants A and B, each with its own document.
- As A, export B's document ID: expect `not_found`.
- As A, export A's own document: expect the row back.
- Run the same pair against `/documents/` to show the two routes now match.

## Still to confirm

- **How many IDs leak?** I couldn't measure how much is exposed because the activity-event code wasn't supplied. To find out, check which document events are public and whether they cover every document or only some.
- **Does anything else call `find_by_id`?** Nothing outside these four files was reviewed. Once the fix is in, search the full codebase for calls to `find_by_id` or `export` that don't pass a tenant.

## Coverage and limits

- **What I checked:** authentication and tenant authorization on both routes, SQL handling, and how the response is built. Both queries pass values as bound parameters, so I found no SQL injection.
- **What I didn't cover:** the router and `authenticate` implementations, session handling, activity events and the database schema. For these I relied on the descriptions in `deployment.md`.
- **Evidence:** static analysis only. Nothing was reproduced at runtime.
- **Overall risk:** I can only rate these four files, not the application as a whole. Within them, the cross-tenant read through the export route is the substantiated issue.
