import json
from typing import Dict, Any, Optional
from app.mcp_servers.payment_mcp_server import mcp_server

class RaahMCPClient:
    """
    Standard MCP Client wrapper for invoking RAAH's official MCPServer tools.
    Provides uniform execution, response parsing, error handling, and audit tracing.
    """

    @classmethod
    async def call_tool(cls, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        args = arguments or {}
        try:
            # Invokes the tool via the official MCPServer protocol
            res = await mcp_server.call_tool(name, args)
            
            # Parse MCP result structure: res.content contains TextContent objects
            raw_text = ""
            if hasattr(res, "content") and res.content:
                first = res.content[0]
                raw_text = getattr(first, "text", str(first))
            elif hasattr(res, "structured_content") and res.structured_content:
                return res.structured_content
            else:
                raw_text = str(res)

            try:
                return json.loads(raw_text)
            except Exception:
                return {"result": raw_text, "raw": True}
        except Exception as e:
            return {
                "error": str(e),
                "tool": name,
                "success": False
            }
