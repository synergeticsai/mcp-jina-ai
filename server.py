from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from mcp.server.sse import SseServerTransport
from mcp.server import Server
import uvicorn
import httpx
import json

# Initialize the MCP server
mcp = FastMCP("JinaAI")

# Jina AI API base URLs
JINA_READER_URL = "https://r.jina.ai/"
JINA_SEARCH_URL = "https://s.jina.ai/"

@mcp.tool()
async def fetch_web_content(url: str, jina_api_key: str) -> dict:
    """Fetch web content using Jina AI Reader API."""
    print(f"fetch_web_content called with url: {url}")
    if not url or not jina_api_key:
        return {"status": "error", "payload": {"error": "URL and API key required"}}
    
    headers = {"Authorization": f"Bearer {jina_api_key}", "Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            request_url = f"{JINA_READER_URL}{url}"
            print(f"Making request to: {request_url}")
            response = await client.get(request_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            return {
                "status": "success",
                "payload": {
                    "content": result.get("data", {}).get("content", ""),
                    "metadata": result.get("data", {}).get("metadata", {})
                }
            }
        except httpx.HTTPStatusError as e:
            return {"status": "error", "payload": {"error": f"HTTP error: {e}"}}
        except Exception as e:
            return {"status": "error", "payload": {"error": f"Request failed: {e}"}}

@mcp.tool()
async def search_web(query: str, jina_api_key: str) -> dict:
    """Search the web using Jina AI Search API."""
    print(f"search_web called with query: {query}")
    if not query or not jina_api_key:
        return {"status": "error", "payload": {"error": "Query and API key required"}}
    
    headers = {
        "Authorization": f"Bearer {jina_api_key}",
        "Accept": "application/json",
        "X-Respond-With": "no-content"
    }
    async with httpx.AsyncClient() as client:
        try:
            request_url = f"{JINA_SEARCH_URL}?q={query}"
            print(f"Making request to: {request_url}")
            response = await client.get(request_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            # Handle the response as a list of results
            if not isinstance(result, list):
                return {"status": "error", "payload": {"error": "Unexpected response format: expected a list"}}
            return {
                "status": "success",
                "payload": {
                    "results": result,  # Use the list directly as results
                    "metadata": {}     # No metadata provided in the response
                }
            }
        except httpx.HTTPStatusError as e:
            return {"status": "error", "payload": {"error": f"HTTP error: {e}"}}
        except Exception as e:
            return {"status": "error", "payload": {"error": f"Request failed: {e}"}}

# Direct REST API handlers
async def handle_api_request(request):
    """Handle direct API requests to tools."""
    try:
        data = await request.json()
        if not data.get("tool"):
            return JSONResponse({"error": "tool name is required"}, status_code=400)
        tool_name = data.get("tool")
        args = data.get("args", {})
        # Call the appropriate tool function
        if tool_name == "fetch_web_content":
            if not args.get("url") or not args.get("jina_api_key"):
                return JSONResponse({"error": "url and jina_api_key are required"}, status_code=400)
            result = await fetch_web_content(args.get("url"), args.get("jina_api_key"))
            return JSONResponse(result)
        elif tool_name == "search_web":
            if not args.get("query") or not args.get("jina_api_key"):
                return JSONResponse({"error": "query and jina_api_key are required"}, status_code=400)
            result = await search_web(args.get("query"), args.get("jina_api_key"))
            return JSONResponse(result)
        else:
            return JSONResponse({"error": f"Unknown tool: {tool_name}"}, status_code=400)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Server error: {str(e)}"}, status_code=500)

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette app for the MCP server."""
    sse = SseServerTransport("/messages/")
    async def handle_sse(request):
        print("Handling SSE connection")
        async with sse.connect_sse(request.scope, request.receive, request._send) as (
            read_stream,
            write_stream,
        ):
            await mcp_server.run(
                read_stream, write_stream, mcp_server.create_initialization_options()
            )
    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/api", endpoint=handle_api_request, methods=["POST"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    mcp_server = mcp._mcp_server
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8080)