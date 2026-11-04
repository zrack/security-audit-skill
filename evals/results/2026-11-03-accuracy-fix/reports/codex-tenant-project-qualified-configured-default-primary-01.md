**One substantiated finding: High — Cross-tenant confidential document disclosure. Confidence: High (static evidence).**

The export path omits tenant authorization:

`/exports handler` → `DocumentService.export` → `Storage.find_by_id`.

The query filters only by document ID and returns the row, including its confidential body, to the JSON response. `deployment.md` guarantees authentication but explicitly excludes additional tenant controls. It also establishes open registration and a public event through which an attacker can learn another tenant’s document ID. Consequently, a registered user with that ID can retrieve the other tenant’s confidential document.

The `/documents/{document_id}` path correctly carries the trusted tenant ID through `read_for_tenant` to `find_for_tenant`, whose query constrains both ID and tenant. Both storage queries use bound parameters; the supplied evidence does not support SQL injection.

**Fix:** Pass `ctx.tenant_id` into `export` and use `find_for_tenant(tenant_id, document_id)`. Recommended verification after correction: tenant A receives a not-found response when exporting tenant B’s known document ID, while exporting A’s own document succeeds. This check was not executed.

**Coverage and limits:** Reviewed all four supplied files together; no immutable revision was supplied. Inspection was static only: no sample execution, network access, dependency installation, unrelated-file inspection, or file changes. The supported impact is confidential reads for known document IDs; enumeration and broader compromise are not established. Deployment secrets and other services are explicitly “not described” in `deployment.md`.
