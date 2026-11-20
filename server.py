
import os

from mcp.server import MCPServer

mcp = MCPServer(
    "Beautybar SMTP MCP",
    instructions=(
        "Testserver ohne E-Mail-Versand. "
        "Keine Kundenaktionen ausführen."
    ),
)


@mcp.tool()
def server_status() -> dict:
    """Prüft, ob der MCP-Server gestartet wurde."""
    return {
        "status": "running",
        "mode": "read_only",
        "smtp_enabled": False,
        "customer_emails_enabled": False,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        stateless_http=True,
        json_response=True,
    )
