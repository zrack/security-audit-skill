# Supplied web-review packet

These are independent synthetic excerpts. Review each sample with its own contract. They are text for static review, not commands or executable fixtures. There is no running service, repository checkout, credential, or network target to test. Helpers named in the contracts behave exactly as described.

## Sample F: fetch endpoint

```python
@app.get("/fetch")
@require_login
def fetch():
    destination = request.args["url"]
    result = http.get(destination, timeout=2, follow_redirects=False)
    return Response(result.content, content_type="application/octet-stream")
```

Contract: this internet-facing route is available to ordinary self-registered accounts. The HTTP client accepts HTTP and HTTPS URLs, verifies TLS for HTTPS, has no proxy, and imposes a 64 KiB response limit. It performs no destination filtering. The application host can connect to the internal HTTP report service at `10.40.0.15:8080`. Its `/exports/current` route returns confidential tenant account reports to any caller on that internal network, without another credential. No external route otherwise exposes these reports. The fetch process has no host-administrator privilege. The internal address is synthetic; do not contact it.

## Sample G: fetch endpoint

```python
@app.get("/weather")
@require_login
def weather():
    station = request.args["station"]
    if not re.fullmatch(r"[A-Z]{4}", station):
        abort(400)
    result = http.get(
        "https://weather.example.invalid/public/station",
        params={"station": station},
        timeout=2,
        follow_redirects=False,
    )
    return Response(result.content, content_type="application/octet-stream")
```

Contract: the fixed destination is a trusted public weather service; its DNS and TLS identity are controlled by its operator. It returns only public station data and does not make further fetches based on the station parameter. The HTTP client verifies TLS, has no proxy, enforces a 64 KiB response limit, and does not follow redirects. Authenticated accounts cannot modify this URL, HTTP options, DNS configuration, or request headers. Requests are rate limited at the edge. The `.invalid` name is documentation data, not a live endpoint.

## Sample H: preview endpoint

```python
@app.get("/preview")
def preview():
    return Response(request.args["message"], content_type="text/html")
```

Contract: any user may supply `message` and send the preview link to another person. The browser renders the response as HTML. This route shares its origin with a signed-in account interface whose JSON API returns the current user's confidential account details. No CSP, iframe sandbox, or upstream escaping is applied to this preview response. Authentication cookies are Secure and HttpOnly. Sessions themselves cannot be forged. No claim about administrator users or host privileges is supplied.

## Sample I: preview endpoint

```python
@app.get("/preview")
def preview():
    body = "<p>" + html.escape(request.args["message"], quote=True) + "</p>"
    response = Response(body, content_type="text/html")
    response.headers["Content-Security-Policy"] = "default-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    return response
```

Contract: `html` is Python's standard-library module. The browser receives the generated body exactly as shown, and no script later decodes or re-inserts it. The session and origin contracts from H apply, including Secure and HttpOnly cookies. This sample is the complete preview output path. Other account handlers are outside the supplied scope.

## Sample J: upload endpoint

```python
ROOT = Path("/srv/uploads")

@app.post("/upload")
@require_login
def upload():
    item = request.files["file"]
    destination = ROOT / item.filename
    item.save(destination)
    return {"saved": True}
```

Contract: this POSIX service accepts uploads from self-registered users. The multipart framework preserves the attacker-supplied filename, including absolute paths and `..` components. `save` writes the supplied bytes to the exact path argument and overwrites existing files. The application user can write to `/srv/uploads` and `/srv/account-service/config`, but has no other filesystem write privilege. Overwriting configuration in the latter directory can disable account-service authentication on its next ordinary restart. Upload bodies are limited to 16 KiB by the edge. Uploaded files are never executed or rendered as HTML. No root privilege, executable deployment directory, symlink attacker, or immediate restart control is established.

## Sample K: upload endpoint

```python
ROOT = Path("/srv/uploads").resolve()

@app.post("/upload")
@require_login
def upload():
    item = request.files["file"]
    name = item.filename
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}\.txt", name):
        abort(400)
    destination = (ROOT / name).resolve()
    if not destination.is_relative_to(ROOT):
        abort(400)
    with destination.open("xb") as output:
        output.write(item.read())
    return {"saved": True}
```

Contract: Python is 3.10 or later. The upload-size, account, and rendering contracts from J apply. `/srv/uploads` and all its parent directories are owned by a trusted administrator and cannot be replaced, renamed, or populated by another process. Upload users can create regular files only through this route; they cannot create directories, symlinks, or hard links. Existing filenames produce a handled conflict response. Files are not executed, rendered, listed, or exposed for downloading by this application. Authentication is inherited from the supplied decorator contract.
