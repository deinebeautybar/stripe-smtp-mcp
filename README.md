# stripe-smtp-mcp

## Statusdienst auf Render

Start: python server.py. FastMCP (Python SDK 1.x), Streamable HTTP unter /mcp, stateless JSON. GET /healthz liefert ausschließlich den Prozessstatus. Der einzige MCP-Aufruf ist server_status. Keine SMTP- oder Stripe-Clients.

Zugriff: Authorization: Bearer mit dem in Render generierten MCP_STATUS_TOKEN. Kein Token in die URL schreiben. Fehlender, zu kurzer oder falscher Schlüssel sperrt den MCP-Zugang. Zugriff auf den Dienstschlüssel auf die zuständigen Personen beschränken.

## Prüfprotokoll 20.11.2026

Der vorherige Deploy scheiterte mit ImportError beim Import von MCPServer. Commit 3caecf7 korrigiert den Import und startet Uvicorn auf dem Render-PORT. Render meldete Application startup complete und Service is live. Live im Browser: /healthz meldete up, /mcp wies den anonymen Zugriff ab. Lokal unter Python 3.12 und mcp 1.29.0: initialize, tools/list und server_status erfolgreich. Ohne gültigen Schlüssel HTTP 401. Authentifizierter ChatGPT-End-to-End-Test offen.

## IONOS-Vorbereitung

Postausgang smtp.ionos.de, Port 465 mit TLS, Benutzer und Absender inkasso@deine-beautybar.de. Auf Render Free sind ausgehende SMTP-Verbindungen gesperrt. Kein Passwort erforderlich für den Statusdienst. Erst bei gesonderter Freigabe eines internen Tests SMTP-Zugang im Secret-Store hinterlegen. Kein Versandwerkzeug registriert.

Vor Verarbeitung von Kundendaten die tatsächlichen Datenflüsse, Anbietervereinbarungen, Zugriffsrechte, Protokollierung und Löschfristen prüfen. Eine produktive Versandfreigabe liegt nicht vor.
