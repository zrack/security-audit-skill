# Review packet

Review these two supplied Flask code samples for security issues. Use static inspection only. There is no repository checkout or running service. Treat the supplied files as the complete samples, and report each sample separately.

## Sample A: api.py

```python
import subprocess
from flask import Flask, request, session, jsonify, abort
from functools import wraps

app = Flask(__name__)
# The session key is configured by the deployment and is not part of this sample.

def require_login(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            abort(401)
        return fn(*args, **kwargs)
    return wrapped

@app.get("/api/invoices/<int:invoice_id>")
@require_login
def invoice(invoice_id):
    row = db.execute("SELECT id, owner_id, amount, bank_account FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))

@app.get("/api/dns")
@require_login
def dns():
    hostname = request.args["hostname"]
    result = subprocess.check_output("nslookup " + hostname, shell=True, text=True)
    return jsonify(result=result)

# Deployment contract: public internet service; ordinary accounts are available
# by self-registration. Every authenticated account reaches both routes.
# db is a standard SQLite connection with row_factory=sqlite3.Row, so fetched rows
# support dict(row). No database row policy or proxy guard exists.
```

## Sample B: api.py

```python
import subprocess
import re
from flask import Flask, request, session, jsonify, abort
from functools import wraps

app = Flask(__name__)
DOCUMENTATION_KEY = "sk-example-not-a-real-credential"

def require_login(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            abort(401)
        return fn(*args, **kwargs)
    return wrapped

@app.get("/api/invoices/<int:invoice_id>")
@require_login
def invoice(invoice_id):
    row = db.execute("SELECT id, amount FROM invoices WHERE id = ? AND owner_id = ?", (invoice_id, session["user_id"])).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))

@app.get("/api/dns")
@require_login
def dns():
    hostname = request.args["hostname"]
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?", hostname):
        abort(400)
    result = subprocess.run(["nslookup", hostname], shell=False, capture_output=True, text=True, timeout=2)
    return jsonify(result=result.stdout)

@app.get("/public/status")
def status():
    response = jsonify(status="ok")
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# Deployment contract: session key is external, cookies are secure/HttpOnly,
# sessions cannot be forged, and db is a standard SQLite connection configured
# with row_factory=sqlite3.Row, so fetched rows support dict(row). All routes are rate
# limited by the edge proxy to 5 requests/minute/account, with concurrency caps.
# DNS egress is restricted by the host, and resolved names return no internal
# records. Public status contains only the literal value above.
```
