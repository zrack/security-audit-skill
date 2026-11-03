# Example security review

Illustrative output for the [synthetic review packet](review-packet.md). This is not a finding about this repository or a real deployed service.

## Scope

Static inspection of the supplied `invoice()` and `dns()` handlers and the owner's stated deployment context. No repository revision, dependency inventory, live service, or complete application was supplied. No code was executed.

## Findings

| Severity | Confidence | Location | Issue |
| --- | --- | --- | --- |
| High | High | `dns()`: `subprocess.check_output` | A logged-in caller controls part of a shell command. |
| High | High | `invoice()`: invoice query | A logged-in caller can request another user's invoice. |

### Shell command injection

**Evidence and impact:** `hostname` comes directly from a request parameter and is concatenated into a string executed with `shell=True`. Given the supplied reachability assumptions, a self-registered account can influence shell syntax and execute commands with the service's privileges. The login check does not validate this input.

**Fix:** Pass the executable and hostname as separate arguments with `shell=False`, validate the hostname, and set a timeout.

**Verify:** Use an isolated test with a mocked subprocess call to confirm that input cannot change the executable or enable shell interpretation. Check that invalid hostnames are rejected.

### Cross-account invoice disclosure

**Evidence and impact:** The query filters by a caller-selected `invoice_id` but never constrains `owner_id` to the authenticated user. The packet rules out an external object-authorization guard. A logged-in caller can retrieve another account's invoice, including its bank-account field, if that invoice ID exists.

**Fix:** Enforce invoice ownership in the query or the application's authorization layer, and return only fields the caller needs.

**Verify:** Confirm that one account cannot retrieve a second account's invoice, while authorized retrieval still works.

## Coverage and limits

Both findings follow from the code and the supplied context; neither was runtime-tested. Session implementation, all other routes, infrastructure, dependencies, and deployed controls were not reviewed. No risk rating is assigned to the whole application.
