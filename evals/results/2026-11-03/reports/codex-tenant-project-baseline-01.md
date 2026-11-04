Found **one substantiated security issue**.

**High — Cross-tenant document disclosure through export. Confidence: High.**

The complete call path drops tenant authorization:

1. `export_document, routes.py.txt:16` passes only the caller-supplied document ID.
2. `DocumentService.export, service.py.txt:8` forwards it to `find_by_id`.
3. `Storage.find_by_id, storage.py.txt:12` selects the confidential `body` using only `WHERE id = ?`.
4. The route returns that dictionary as JSON.

An ordinary authenticated tenant can therefore retrieve another tenant’s document using its known ID. The `deployment evidence` explicitly establishes public ID discoverability and the absence of additional tenant filters. Opaque IDs and authentication do not prevent this disclosure.

**Fix:** Pass trusted `ctx.tenant_id` through `export` and use `find_for_tenant`, requiring both document ID and tenant ID.

**Verification after correction:** For both endpoints, confirm tenant A can retrieve its own document, while tenant B’s known document ID and nonexistent IDs return not found.

The normal `/documents` path correctly carries trusted tenant identity through the service into the tenant-filtered query. Both storage queries bind parameters; the supplied evidence does not support an SQL-injection finding.

This was static inspection of the four supplied files, with no immutable revision supplied. No sample code was executed, network accessed, dependencies installed, unrelated project files inspected, or files modified. Conclusions rely on the stated deployment guarantees; runtime behavior and the proposed correction remain untested.
