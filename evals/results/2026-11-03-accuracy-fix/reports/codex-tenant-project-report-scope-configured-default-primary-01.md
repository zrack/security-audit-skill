Found **one substantiated vulnerability: High severity, High confidence — cross-tenant confidential document disclosure.**

An ordinary authenticated tenant user who knows another tenant’s document ID can retrieve its confidential body through `/exports/{document_id}`. The supplied deployment explicitly establishes self-registration, foreign-ID discovery through public activity events, and no additional authorization or tenant filter (`deployment.md:5`, `deployment.md:7`).

The cross-file path is:

1. The export handler passes only `document_id` to `ctx.documents.export` (`routes.py.txt:16`).
2. `DocumentService.export` calls `storage.find_by_id` without tenant context (`service.py.txt:8`).
3. Storage selects `id`, `tenant_id`, `title`, and `body` using only `WHERE id = ?` (`storage.py.txt:14`).
4. The handler returns the resulting dictionary (`routes.py.txt:19`).

Authentication does not prevent this disclosure: it establishes the caller’s tenant, but the export path never uses that identity. Opaque IDs do not prevent the stated known-ID attack.

**Fix:** Pass trusted `ctx.tenant_id` into the export method and reuse `find_for_tenant`. That is the control already used by the ordinary document route: tenant identity flows through `read_for_tenant` into a query requiring both document ID and tenant ID (`routes.py.txt:9`, `service.py.txt:5`, `storage.py.txt:7`).

**Recommended verification:** With two tenants, confirm each can export its own document and receives 404 when requesting the other tenant’s known document ID.

Reviewed all four supplied artifacts using static inspection only; no immutable revision was supplied. No code execution, network access, dependency installation, file modification, or unrelated-file inspection occurred. Bound SQL parameters support no SQL-injection finding here. The disclosure follows from the supplied contracts, but runtime behavior was not tested. Deployment secrets and other services “are not described” (`deployment.md:7`); their exposure remains unassessed.
