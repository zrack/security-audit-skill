# Security audit: synthetic tenant document service

**Scope:** I read `deployment.md`, `routes.py.txt`, `service.py.txt` and `storage.py.txt` in the workspace. There's no git revision; these are text excerpts as supplied. This was static inspection only: I ran nothing, installed nothing, used no network and changed no files. I assumed the deployment facts in `deployment.md` are true: the router always runs `authenticate`, `ctx.tenant_id` comes from a trusted server-side session, and there's no other tenant filter or row policy.

## Findings

### 1. The export endpoint lets any user read other tenants' documents — **High**, confidence **High**

**Where:**
- `routes.py.txt:14-19`: `export_document` calls `ctx.documents.export(document_id)` and never passes `ctx.tenant_id`.
- `service.py.txt:8-9`: `DocumentService.export(document_id)` takes no tenant and calls `storage.find_by_id`.
- `storage.py.txt:12-17`: `find_by_id` runs `SELECT id, tenant_id, title, body FROM documents WHERE id = ?`, with no `tenant_id` condition.

**How the call path works:** `GET /exports/{document_id}` → `authenticate`, which only checks that the session is valid → `export_document` → `DocumentService.export` → `Storage.find_by_id`. The full row comes back through `response.json(row)`, including the confidential `body`, whichever tenant owns it.

**Counterexample checked:** the other route, `GET /documents/{id}` at `routes.py.txt:7-12`, is safe. It goes through `read_for_tenant(ctx.tenant_id, …)` → `find_for_tenant`, which filters on `id = ? AND tenant_id = ?` (`storage.py.txt:5-10`). So the export path skips a control the codebase already uses. `deployment.md` says there's no other layer that would catch this.

**What an attacker needs:**
- **An account:** anyone can self-register into a tenant, so getting an authenticated session is easy.
- **A target document ID:** another tenant's IDs leak through the shared public activity event.

The opaque IDs don't help, because the IDs are disclosed.

**Impact:** any registered user can read the title and confidential body of any other tenant's document whose ID they have seen. That breaks tenant isolation for confidentiality. The evidence supports read access only; neither route writes or deletes anything.

**Fix:** scope the export by tenant at every layer:

```python
# routes.py
row = ctx.documents.export(ctx.tenant_id, document_id)

# service.py
def export(self, tenant_id, document_id):
    return self.storage.find_for_tenant(tenant_id, document_id)
```

Then remove `Storage.find_by_id`, or make it private, so it can't be reached from a request handler. If cross-tenant lookup is ever really needed (for example by an admin), put it behind an explicit privileged check.

**How to verify:** add a test with two tenants, A and B. B calls `GET /exports/{A's document id}` and should get 404, just as `/documents/{id}` does. A exporting its own document should still return 200. Also add a test that fails if any request handler reaches `find_by_id`.

## Checked with no issue found
- **SQL injection:** both queries use bound `?` parameters, so no injection.
- **`/documents/{id}`:** filtered by tenant correctly.
- **Authentication:** handled outside these files (the router guarantee in `deployment.md`). I didn't review it.

## Coverage and limits
- I traced both routes end to end across the three source files.
- I relied on `deployment.md` for:
  - the guarantee that `authenticate` always runs first
  - how sessions and tenants are bound
  - how the activity event leaks IDs
  - how the SQLite connection is set up

  I did not verify any of these. If any of them is wrong, other risks could appear (for example, a broken `authenticate`), but none of that would make the export finding go away.
- I didn't review: how sessions are created, the self-registration flow, the activity-event feature, response serialisation beyond what `deployment.md` describes, deployment secrets, or infrastructure.
- **Overall risk for the reviewed scope: High,** because of finding 1.

**Next step:** apply the tenant-scoped export fix and add the cross-tenant regression test above.
