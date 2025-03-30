# mssql-mcp-server

mssql-mcp-server is a Model Context Protocol (MCP) server for connecting to Microsoft SQL Server.

## Installation

```
git clone https://github.com/leopeng1995/mssql-mcp-server.git
cd mssql-mcp-server

uv sync
uv run mssql-mcp-server
```

## Configuration in Cline

```json
{
  "mcpServers": {
    "mssql-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "H:/workspaces/leopeng1995/mssql-mcp-server",
        "run",
        "mssql-mcp-server"
      ],
      "env": {
        "MSSQL_SERVER": "localhost",
        "MSSQL_PORT": "1433",
        "MSSQL_USER": "username",
        "MSSQL_PASSWORD": "password",
        "MSSQL_DATABASE": "database",
        "MSSQL_CHARSET": "UTF-8" # or CP936 ...
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Note:** The `MSSQL_CHARSET` value is case-sensitive.
