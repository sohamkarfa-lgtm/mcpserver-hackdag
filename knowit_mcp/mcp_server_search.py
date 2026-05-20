import re
import aiohttp
from fastmcp import FastMCP
from bs4 import BeautifulSoup

mcp = FastMCP()

@mcp.tool()
async def search_url_for_query(url: str, query: str) -> str:
    """A simple search function that takes a URL and a query as input and searches for the query in the URL's content."""
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    # Remove noisy content
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)

    return f"Content from {url}:\n\n{text}..."  



if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8050)