Found **one substantiated security issue** in the supplied four-file snapshot.

**High severity, High confidence — cross-tenant document disclosure through exports**

An authenticated user can retrieve another tenant’s confidential document using an ID learned from a public activity event, as described in `deployment.md`.

The complete call path bypasses tenant authorization:

1. The `export route` passes only `document_id` to `DocumentService.export`.
2. The `service method` calls `storage.find_by_id`.
3. The `storage query` filters only by document ID and selects the confidential `body`. The route returns that dictionary.

Authentication is required, but the export path never uses the trusted tenant identity. The supplied deployment explicitly excludes compensating authorization controls. This supports disclosure of a known foreign document; it does not establish ID enumeration.

**Fix:** Pass `ctx.tenant_id` into `export` and use `find_for_tenant`, matching the tenant-scoped document-read path. Bound SQL parameters already address SQL injection; they do not enforce ownership.

**Suggested verification, not performed:** Using tenant A’s session, request tenant B’s known document ID through both routes and confirm neither returns its contents. Confirm tenant A can still export its own document.

Review covered both routes through service and storage, plus deployment assumptions. Static inspection only: no sample execution, network access, dependency installation, unrelated-file inspection, or modifications. No immutable revision was supplied; authentication and deployment guarantees were accepted as stated.
