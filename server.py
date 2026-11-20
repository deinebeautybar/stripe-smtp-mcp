"""Read-only MCP endpoint. No mail transport or Stripe client is loaded."""
import os
import secrets

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse


def create_app():
    token = os.environ.get("MCP_STATUS_TOKEN", "")
    host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost")
    security = TransportSecuritySettings(enable_dns_rebinding_protection=True,
        allowed_hosts=[host, "localhost:*", "127.0.0.1:*"], allowed_origins=["https://" + host])
    mcp = FastMCP("Beautybar SMTP MCP", stateless_http=True, json_response=True,
                  transport_security=security)

    @mcp.tool()
    def server_status() -> dict:
        """Report service status without accessing any customer systems."""
        return {"status": "running", "mode": "read_only", "smtp_enabled": False,
                "customer_emails_enabled": False}

    endpoint = mcp.streamable_http_app()

    async def app(scope, receive, send):
        if scope["type"] == "http":
            if scope["path"] == "/healthz" and scope["method"] == "GET":
                await JSONResponse({"status": "up"})(scope, receive, send)
                return
            headers = [v for k, v in scope["headers"] if k == b"authorization"]
            if len(token) < 32 or len(headers) != 1 or not secrets.compare_digest(
                headers[0], b"Bearer " + token.encode()
            ):
                await JSONResponse({"error": "unauthorized"}, status_code=401,
                                   headers={"WWW-Authenticate": "Bearer"})(scope, receive, send)
                return
        await endpoint(scope, receive, send)

    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=int(os.getenv("PORT", "10000")),
                access_log=False)
