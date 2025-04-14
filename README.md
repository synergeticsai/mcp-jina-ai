# Jina AI MCP Server

This project implements a Model Context Protocol (MCP) server integrated with Jina AI's Reader and Search APIs. It provides tools to fetch web content and perform web searches, accessible via Server-Sent Events (SSE) and a REST API.

## Features

- **FastMCP Server**: Uses `FastMCP` from the `mcp` library to handle message processing.
- **Jina AI Integration**:
  - **Web Content Fetching**: Retrieves content from web pages using Jina AI Reader API.
  - **Web Search**: Performs searches using Jina AI Search API.
- **Endpoints**:
  - SSE endpoint (`/sse`) for real-time message streaming.
  - REST API endpoint (`/api`) for direct tool access.
  - Message handling endpoint (`/messages/`) for SSE POST requests.
- **Asynchronous Processing**: Built with `Starlette` and `uvicorn` for high-performance async operations.

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt` (see below for installation).

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment (optional but recommended):
  
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

3. Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

Usage

1. Set up environment variables (optional):
  - The server requires a Jina AI API key for the fetch_web_content and search_web tools. Pass the API key as an argument in requests.

2. Run the server:

  ```bash
  python server.py
  ```
  The server will start on http://0.0.0.0:8080.

3. Access the endpoints:

    - SSE Endpoint: Connect to /sse for real-time message streaming.
    - REST API: Send POST requests to /api to call tools directly.
    - Messages Endpoint: Use /messages/ for SSE POST interactions.


Endpoints

    - POST /api: Direct access to tools (fetch_web_content, search_web).
        Request body: {"tool": "<tool_name>", "args": {...}}
    - GET /sse: Establishes an SSE connection for real-time communication.
    - POST /messages/: Handles SSE message submissions.

Tools

    - fetch_web_content(url, jina_api_key):
        Fetches content from a given URL using Jina AI Reader API.
        Returns content and metadata or an error message.
    - search_web(query, jina_api_key):
        Searches the web for a query using Jina AI Search API.
        Returns a list of results or an error message.

Configuration

    Host/Port: Modify host and port in uvicorn.run() (default: 0.0.0.0:8080).
    Debug Mode: Set debug=True in create_starlette_app() for verbose logging (default: True).

Error Handling

    Missing parameters return {"status": "error", "payload": {"error": "..."}}.
    HTTP errors from Jina AI APIs are captured and returned in the response.
    Invalid JSON or unknown tools return appropriate HTTP status codes (400, 500).