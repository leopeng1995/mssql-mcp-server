import os
import logging
import mcp.types as types
from typing import Dict, Any, List

import pymssql
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.server.stdio import stdio_server


app_name = "mssql-mcp-server"
app_version = "0.1.0"
logger = logging.getLogger(app_name)
logger.setLevel(logging.INFO)
server = Server(app_name)


def get_db_config():
    """Get database configuration from environment variables."""
    config = {
        "host": os.getenv("MSSQL_SERVER", "localhost"),
        "port": int(os.getenv("MSSQL_PORT", "1433")),
        "user": os.getenv("MSSQL_USER"),
        "password": os.getenv("MSSQL_PASSWORD"),
        "database": os.getenv("MSSQL_DATABASE"),
        "charset": os.getenv("MSSQL_CHARSET", "UTF-8"),
    }
    
    if not all([config["user"], config["password"], config["database"]]):
        logger.error("Missing required database configuration. Please check environment variables:")
        logger.error("MSSQL_USER, MSSQL_PASSWORD, and MSSQL_DATABASE are required")
        raise ValueError("Missing required database configuration")
    
    return config


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available MSSQL tools."""
    query_tool = types.Tool(
        name="execute_sql",
        description="Execute an SQL query on the MSSQL server",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL query to execute"
                },
            },
            "required": ["query"],
        },
    )
    return [query_tool]


@server.list_resources()
async def list_resources() -> List[types.Resource]:
    """List MSSQL tables as resources."""
    config = get_db_config()
    try:
        conn = pymssql.connect(**config)
        cursor = conn.cursor()
        # Query to get user tables from the current database
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        tables = cursor.fetchall()

        resources = []
        for table in tables:
            resources.append(
                types.Resource(
                    uri=f"mssql://{table[0]}/data",
                    name=f"Table: {table[0]}",
                    mimeType="text/plain",
                    description=f"Data in table: {table[0]}"
                )
            )
        cursor.close()
        conn.close()
        return resources
    except Exception as e:
        logger.error(f"Failed to list resources: {str(e)}")
        return []


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Execute SQL commands."""
    logger.debug(f"Calling tool {name} with arguments {arguments}")
    config = get_db_config()

    if name != "execute_sql":
        raise ValueError(f"Unknown tool: {name}")
    
    query = arguments.get("query")
    if not query:
        raise ValueError("Query is required")
    
    try:
        conn = pymssql.connect(**config)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Special handling for table listing
        if query.strip().upper().startswith("SELECT") and "INFORMATION_SCHEMA.TABLES" in query.upper():
            tables = cursor.fetchall()
            result = ["Tables_in_" + config["database"]]  # Header
            result.extend([table[0] for table in tables])
            cursor.close()
            conn.close()
            return [types.TextContent(type="text", text="\n".join(result))]
        
        # Regular SELECT queries
        elif query.strip().upper().startswith("SELECT"):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [",".join(map(str, row)) for row in rows]
            cursor.close()
            conn.close()
            return [types.TextContent(type="text", text="\n".join([",".join(columns)] + result))]
        
        # Non-SELECT queries
        else:
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            return [types.TextContent(type="text", text=f"Query executed successfully. Rows affected: {affected_rows}")]

    except Exception as e:
        logger.error(f"Error executing SQL '{query}': {e}")
        return [types.TextContent(type="text", text=f"Error executing query: {str(e)}")]


async def start_server():
    """Run the server async context."""
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name=app_name,
                server_version=app_version,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )
