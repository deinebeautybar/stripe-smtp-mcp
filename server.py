"""Read-only MCP server with optional WorkOS AuthKit authentication."""
import os
import secrets
from urllib.parse import urlsplit

import jwt
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse


def create_app():
    token = os.getenv("MCP_STATUS_TOKEN", "").encode()
    host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost")
    resource = f"https://{host}/mcp"
    metadata_path = "/.well-known/oauth-protected-resource/mcp"
    issuer = os.getenv("MCP_OAUTH_ISSUER", "").strip().rstrip("/")
    subject = os.getenv("MCP_OAUTH_ALLOWED_SUBJECT", "").strip()
    if issuer or subject:
        parsed = urlsplit(issuer)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.netloc != parsed.hostname
            or parsed.path
            or parsed.query
            or parsed.fragment
            or not subject.startswith("user_")
        ):
            raise ValueError("Configure an HTTPS AuthKit origin and an allowed WorkOS user ID")
        jwks = jwt.PyJWKClient(f"{issuer}/oauth2/jwks", timeout=5)

    def oauth_authorized(candidate):
        try:
            encoded = candidate.decode("ascii")
            header = jwt.get_unverified_header(encoded)
            if header.get("alg") != "RS256" or not header.get("kid"):
                return False
            key = jwks.get_signing_key_from_jwt(encoded)
            claims = jwt.decode(
                encoded,
                key=key,
                algorithms=["RS256"],
                audience=resource,
                issuer=issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except (UnicodeError, jwt.PyJWTError):
            return False
        return claims["sub"] == subject and claims.get("sub_profile") != "ai_agent"

    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[host, "localhost:*", "127.0.0.1:*"],
        allowed_origins=[f"https://{host}"],
    )
    mcp = FastMCP(
        "Beautybar SMTP MCP",
        stateless_http=True,
        json_response=True,
        transport_security=security,
    )

    @mcp.tool()
    def server_status() -> dict:
        """Report service status without accessing any customer systems."""
        return {
            "status": "running",
            "mode": "read_only",
            "smtp_enabled": False,
            "customer_emails_enabled": False,
        }

    endpoint = mcp.streamable_http_app()

    async def app(scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            if path == "/healthz" and scope["method"] == "GET":
                await JSONResponse({"status": "up"})(scope, receive, send)
                return
            if issuer and scope["method"] == "GET" and path in (
                metadata_path, "/.well-known/oauth-protected-resource"
            ):
                await JSONResponse({
                    "resource": resource,
                    "authorization_servers": [issuer],
                    "bearer_methods_supported": ["header"],
                })(scope, receive, send)
                return

            headers = [value for name, value in scope["headers"] if name == b"authorization"]
            authorized = False
            if len(headers) == 1:
                scheme, _, candidate = headers[0].partition(b" ")
                if scheme.lower() == b"bearer" and candidate:
                    authorized = len(token) >= 32 and secrets.compare_digest(candidate, token)
                    if not authorized and issuer and path == "/mcp":
                        authorized = await run_in_threadpool(oauth_authorized, candidate)
            if not authorized:
                challenge = "Bearer"
                if issuer and path == "/mcp":
                    challenge += f' resource_metadata="https://{host}{metadata_path}"'
                await JSONResponse(
                    {"error": "unauthorized"},
                    status_code=401,
                    headers={"WWW-Authenticate": challenge},
                )(scope, receive, send)
                return
        await endpoint(scope, receive, send)

    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=int(os.getenv("PORT", "10000")), access_log=False)
