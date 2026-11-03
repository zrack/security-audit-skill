# Example review packet

This is an intentionally insecure, synthetic Flask excerpt for static review. It is documentation, not a runnable application.

## Request

> Review the supplied routes for security issues. Use static analysis, report supported findings, and state what is missing.

## Context supplied by the application owner

- The service is publicly reachable, and ordinary users can register accounts.
- `require_login` verifies a session; it does not check invoice ownership.
- Every logged-in user can reach both handlers.
- `db` is a standard SQLite connection. There is no row-level policy or upstream object-authorization guard.
- The session key is configured by deployment; its value is outside this excerpt.

## Code

```python
@app.get("/api/invoices/<int:invoice_id>")
@require_login
def invoice(invoice_id):
    row = db.execute(
        "SELECT id, owner_id, amount, bank_account FROM invoices WHERE id = ?",
        (invoice_id,),
    ).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))

@app.get("/api/dns")
@require_login
def dns():
    hostname = request.args["hostname"]
    result = subprocess.check_output("nslookup " + hostname, shell=True, text=True)
    return jsonify(result=result)
```

See the [illustrative review](review-report.md) for a report grounded in this packet. A different deployment or additional controls could change the conclusions.
