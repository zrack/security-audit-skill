I found one serious problem: any user who signs up can read another tenant's confidential documents through the export route. This is from reading the code only; nothing was run.

**What I reviewed:** the four files you supplied, read as one project — `deployment.md`, `routes.py.txt`, `service.py.txt` and `storage.py.txt`. They aren't in a git repository, so there's no fixed version to cite; this covers the files as they are on disk now. I followed both routes through the service and storage layers.

## Finding

| # | Severity | Confidence | Issue |
|---|---|---|---|
| 1 | **High** | High | The export route reads any document by ID without checking which tenant owns it |

**Where it happens:**
1. `routes.py.txt:14-19`: `export_document` calls `ctx.documents.export(document_id)`. It never passes `ctx.tenant_id`.
2. `service.py.txt:8-9`: `export` calls `storage.find_by_id(document_id)`.
3. `storage.py.txt:12-17`: `find_by_id` runs `SELECT id, tenant_id, title, body FROM documents WHERE id = ?`. Nothing restricts it to the caller's tenant.
4. The route returns the whole row, including the confidential `body`.

**Why it's exploitable:** `deployment.md` describes a public internet service where anyone can sign up into a tenant. It also says the router checks only that the user is logged in, and nothing else filters by tenant: no further route checks, row policies or proxy. And it says other tenants' document IDs show up in a shared public activity feed. So an attacker who signs up can take a document ID from that feed and request `GET /exports/{id}`. They get back that document's `title` and `body`.

**What the evidence doesn't show:** The code proves an attacker can read a document whose ID they already know. Nothing in the files shows they can list or bulk-collect documents beyond the IDs that appear in the activity feed.

**Contrast:** `/documents/{document_id}` is scoped correctly. It goes through `find_for_tenant`, which filters on `id = ? AND tenant_id = ?` using the session's tenant (`storage.py.txt:5-10`). The export path skips that check, and that's the whole bug.

**Fix:**
- Have the route pass `ctx.tenant_id` into `export`.
- Change `DocumentService.export(self, tenant_id, document_id)` to call `self.storage.find_for_tenant(tenant_id, document_id)`.
- Remove `find_by_id`, or make it require a tenant ID, so no future caller can do an unscoped read by accident.

**How to verify:** Write a test with two tenants, A and B, and one document owned by B. As a user in A, request `/exports/<B's document ID>` and expect a 404. Then confirm B can still export its own document.

## Other checks (no issues found)
- **SQL injection:** both queries use bound `?` parameters.
- **Tenant source:** the tenant ID used for scoping comes from the session (`ctx.tenant_id`), which `deployment.md` says clients can't change.
- **Existence leak:** the correctly scoped route returns the same 404 for a missing document and for another tenant's document, so it doesn't reveal which IDs exist.

## Limits
- **Analysis was static only.** As you asked, I didn't execute anything, use the network or change any files.
- **Router and login code weren't supplied.** That includes `authenticate`. My conclusion relies on `deployment.md`'s description of them and of the absence of any other tenant controls. If a tenant filter actually exists somewhere outside these files, the finding would need re-checking against it.
- **Deployment and secrets** aren't described, so I didn't assess them.
