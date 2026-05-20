from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio


def ask_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a whole number.")


async def main():

    client = MultiServerMCPClient(

    #mcp server configuration(json)
    {
        "knowit_mcp_http":{
            "transport": "streamable-http",
            "url": "http://localhost:8050/mcp"
        }    
    }

    )

    #list the tools available in the mcp server
    tools = await client.get_tools()
    print("Tools available in the MCP server:", len(tools))

    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

    #call a tool in the mcp server
    a = ask_int("Enter value for a: ")
    b = ask_int("Enter value for b: ")
    result = await tools[0].ainvoke({"a": a, "b": b})
    print(f"Result from {tools[0].name}: {result[0]['text']}")

if __name__ == "__main__":
    asyncio.run(main())
