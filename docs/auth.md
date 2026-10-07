# Authentication flow

This connector authenticates to WooCommerce with a **REST API key pair**
(`consumer_key` + `consumer_secret`), sent as **HTTP Basic** over **HTTPS**.

## How the key is created (the flow)

1. WooCommerce admin → **WooCommerce → Settings → Advanced → REST API → Add key**.
2. Description: `agent-studio-connector`.
3. User: pick a user. **Use a dedicated least-privilege user**, not an admin.
4. Permissions: **Read** (this connector is read-only by design).
5. Generate. WooCommerce shows `ck_…` (consumer key) and `cs_…` (consumer secret)
   **once**. Store them in your secret manager — never in git.

## How the connector uses it

```
Authorization: Basic base64(consumer_key:consumer_secret)
GET https://<store>/wp-json/wc/v3/orders?per_page=50&page=1
```

Over HTTPS this is safe (the credential is inside TLS). We deliberately do
**not** put the key in the query string, because query strings leak into
access logs, proxies, and browser history.

WooCommerce also supports OAuth 1.0a for HTTP-only stores; we do not support
that path, because an HTTP-only store would expose the credentials and order
data in plaintext. **HTTPS is a hard requirement.**

## Failure handling

| Store response | Connector behaviour |
|---|---|
| 401 / 403 | `AuthError` — key invalid, revoked, or missing Read scope |
| 404 | `NotFoundError` — id does not exist |
| 429 | retry with `Retry-After`/backoff, then `RateLimitedError` |
| 5xx | retry with backoff, then `UpstreamError` |

## Rotation & least privilege

- Keys are rotatable: create a new key, deploy it, then revoke the old one.
- A Read-only key cannot create/update/delete anything, so a leaked key
  cannot damage the merchant's store — only read what the agent is meant to read.
- Production should read the secret from a vault/secret manager at boot, not
  from a file on disk.
