One substantiated finding: **High severity — authenticated cross-tenant document disclosure. Confidence: High.**

The export path omits tenant authorization throughout the call chain:

- `routes.py.txt:16` calls `ctx.documents.export(document_id)` without the trusted tenant ID.
- `service.py.txt:8` delegates to `storage.find_by_id(document_id)`.
- `storage.py.txt:14` selects by document ID alone, including the confidential `body`.
- `routes.py.txt:19` returns the resulting dictionary directly.

The supplied deployment contract establishes that ordinary users can self-register, learn another tenant’s document ID from public activity, and encounter no additional authorization filter. Such a user can therefore retrieve that document through `/exports/{document_id}`. This supports unauthorized disclosure of documents whose IDs are known; it does not establish enumeration or broader compromise.

**Recommended fix:** pass `ctx.tenant_id` through `export` and use `find_for_tenant`. After fixing, verify with two tenants that exports return an owner’s document but return not-found for another tenant’s document.

The ordinary document route correctly carries the trusted tenant ID through `read_for_tenant` to the query’s `id AND tenant_id` restriction. Both storage queries use bound parameters; the supplied paths do not support a SQL-injection finding.

I reviewed all four supplied files as one target using static inspection only. No code was executed, network accessed, dependencies installed, or files modified. No immutable revision was supplied. The finding follows from the packet’s explicit authentication, database, and response contracts; runtime behavior and any deployment outside that packet were not validated.
