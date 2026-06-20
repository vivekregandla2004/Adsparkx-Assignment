# API Authentication Guide

## Overview

Our platform uses Bearer Token authentication for all API endpoints. Every request must include a valid Authorization header.

## Authentication Methods

### Bearer Token (Primary)

Include the token in the HTTP Authorization header:

```
Authorization: Bearer YOUR_API_TOKEN
```

### API Key via Query Parameter (Legacy)

```
GET /api/v1/resource?api_key=YOUR_API_KEY
```

> **Note:** Query parameter authentication is deprecated and will be removed in API v3. Migrate to Bearer tokens immediately.

## Generating API Tokens

1. Log into your dashboard at `https://platform.example.com`
2. Navigate to **Settings → Developer → API Tokens**
3. Click **Generate New Token**
4. Choose the token scope: `read`, `write`, or `admin`
5. Copy the token immediately — it will not be shown again
6. Store it securely in environment variables, never in code

## Token Scopes

| Scope | Permissions |
|-------|-------------|
| `read` | GET requests only |
| `write` | GET, POST, PUT, PATCH |
| `admin` | Full access including DELETE and user management |

## Common Error Codes

### 401 Unauthorized

**Causes:**
- Token is missing from the request
- Token has expired (tokens expire after 90 days by default)
- Token was revoked manually
- Invalid token format (must be Base64-encoded JWT)

**Resolution Steps:**
1. Verify the `Authorization` header is present and formatted correctly
2. Check token expiry: `jwt decode YOUR_TOKEN | jq .exp`
3. Regenerate the token from the dashboard
4. Ensure no trailing whitespace or newline in the token string
5. Check if the token scope matches the endpoint requirements

**Debug Example:**
```bash
curl -v -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/v1/ping
```
Look for `HTTP/2 200` in the response. If you see `401`, examine the `WWW-Authenticate` response header for details.

### 403 Forbidden

The token is valid but lacks permission for the requested operation.

**Resolution:** Regenerate with the appropriate scope or contact your admin.

### 429 Too Many Requests

Rate limit exceeded. Default limits: 100 requests/minute for `read`, 30/minute for `write`.

**Resolution:** Implement exponential backoff and check the `Retry-After` header.

## Token Rotation Best Practices

- Rotate tokens every 30 days in production environments
- Use separate tokens for each service/microservice
- Store tokens in a secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Audit token usage via **Settings → Developer → Token Audit Log**
- Revoke unused tokens immediately

## Webhook Signature Verification

All webhooks are signed using HMAC-SHA256:

```python
import hmac
import hashlib

def verify_webhook(payload_bytes, signature_header, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header.replace('sha256=', ''))
```

## OAuth 2.0 Integration (Enterprise)

Enterprise customers may use OAuth 2.0 with the authorization code flow:

- **Authorization URL:** `https://auth.example.com/oauth/authorize`
- **Token URL:** `https://auth.example.com/oauth/token`
- **Scopes:** `openid`, `profile`, `api:read`, `api:write`

Contact enterprise support for client credentials.
