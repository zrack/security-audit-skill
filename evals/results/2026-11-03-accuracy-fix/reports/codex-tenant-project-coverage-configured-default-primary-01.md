**High — Cross-tenant document disclosure through exports. Confidence: High, based on static evidence.**

An authenticated user can obtain another tenant’s document ID from the public activity event described in `deployment.md:7`, then request `/exports/{document_id}` to retrieve its confidential body.

The complete call path is:

1. `Export handler` passes only `document_id` to `ctx.documents.export`.
2. `Service export` calls `storage.find_by_id`.
3. `Storage lookup` selects `id`, `tenant_id`, `title`, and `body` using only `WHERE id = ?`.
4. The handler returns that dictionary through `response.json`.

Authentication establishes the caller’s tenant, but this path never checks it against the document’s tenant. The deployment explicitly excludes additional authorization controls. The `/documents/{document_id}` path correctly carries the trusted tenant ID through the service to the tenant-filtered query; this confirms the control omitted by export.

Fix the export handler to pass `ctx.tenant_id`, and make the export service use `find_for_tenant`. Verify with two tenants that exports return the caller’s own document and return not-found for a known foreign document ID. These checks are recommended, not executed.

Reviewed only the four supplied files as one static packet; no immutable revision was supplied. No code execution, network access, dependency installation, or file changes occurred. Bound parameters support no SQL-injection finding here. The supported impact is cross-tenant document disclosure; deployment states that “deployment secrets and other services are not described,” so consequences involving those assets remain unestablished.
