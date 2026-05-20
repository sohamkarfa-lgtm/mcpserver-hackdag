from fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers together."""

    return a + b

@mcp.tool()
async def subtract(a: int, b: int) -> int:
    """Subtract one number from another."""

    return a - b


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8050)