import asyncio
from typing import List, Dict, Any
import os

# URL du serveur MCP (n8n)
N8N_MCP_SERVER_URL = os.environ.get(
    "N8N_MCP_SERVER_URL",
    "https://n8n-ephw.onrender.com/mcp/f89eb4ed-5d78-40e2-9ec2-941a403c0b91"
)

# Vérification si MCP est disponible
try:
    from mcp.client.sse import sse_client
    from mcp.client.session import ClientSession
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️ MCP non disponible (environnement Vercel ou dépendance manquante)")
    MCP_AVAILABLE = False


class MCPService:
    def __init__(self, url: str):
        self.url = url

    async def get_tools_async(self) -> List[Any]:
        """Récupère les outils MCP (async safe)"""
        if not MCP_AVAILABLE:
            return []

        try:
            async with sse_client(self.url) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    response = await session.list_tools()
                    return response.tools or []
        except Exception as e:
            print(f"❌ Erreur MCP get_tools_async: {e}")
            return []

    async def execute_tool_async(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Exécute un outil MCP (async safe)"""
        if not MCP_AVAILABLE:
            return None

        try:
            async with sse_client(self.url) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    response = await session.call_tool(tool_name, arguments=args)
                    return response
        except Exception as e:
            print(f"❌ Erreur MCP execute_tool_async: {e}")
            return None

    # -------------------------
    # WRAPPERS SYNCHRONES SAFE
    # -------------------------

    def get_tools(self) -> List[Any]:
        """Version synchrone safe"""
        try:
            return asyncio.run(self.get_tools_async())
        except RuntimeError:
            # Si event loop déjà actif (cas Flask / Vercel)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return []
            return loop.run_until_complete(self.get_tools_async())
        except Exception as e:
            print(f"❌ Erreur get_tools sync: {e}")
            return []

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Version synchrone safe"""
        try:
            return asyncio.run(self.execute_tool_async(tool_name, args))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return None
            return loop.run_until_complete(self.execute_tool_async(tool_name, args))
        except Exception as e:
            print(f"❌ Erreur execute_tool sync: {e}")
            return None


# Instance globale safe
mcp_service = MCPService(N8N_MCP_SERVER_URL)