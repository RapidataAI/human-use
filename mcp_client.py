import asyncio
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv
from typing import cast
import logging
from mcp.types import CallToolResult, TextContent
import os

load_dotenv()  # load environment variables from .env

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rapidata_mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MODEL = "claude-3-7-sonnet-20250219"  # replace with your model name

# Read in human prompting from markdown file
def read_human_prompting():
    try:
        with open("human_prompting.md", "r", encoding="utf-8") as f:
            prompting = f.read()
        return prompting
    except FileNotFoundError:
        logger.error("human_prompting.md file not found")
        return ""
    except Exception as e:
        logger.error(f"Error reading human_prompting.md: {e}")
        return ""

# Get initial system prompt
PROMPTING_GUIDE = read_human_prompting()

class MCPClient:
    def __init__(self, model: str = MODEL):
        # Initialize collections for multiple sessions
        self.sessions: dict[str, dict] = {}  # dict to store sessions by server path
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Initialize Anthropic client with API key
        self.available_tools = []  # Maintain a list of all available tools
        self.model = model  # Store the model name
        self.system_prompt = "You're a helpful assistant that has different tools at their disposal. You have the ability to as REAL HUMANS using the rapidata API.\n\
When you use the Rapidata tool, you may consider the prompting guides that are provided here: \n" + PROMPTING_GUIDE + "\n\
If asked about something like 'i wonder what peoples favorite X is', feel free to first gather the free text options and then combine it with a classification to find out which option is the most popular."
    
    async def connect_to_server(self, server_script_path: str, env: dict[str, str] | None = None):
        """Connect to an MCP server and add its tools to the available tools

        Args:
            server_script_path: Path to the server script (.py or .js)
            env: Optional environment variables to pass to the server
        """
        if not server_script_path:
            logger.error("Server script path is empty")
            return
        
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        print("Connecting to server script:", server_script_path)
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=env
        )

        logger.debug(f"Connecting to server: {server_script_path} with command: {command}")
        logger.debug(f"Server parameters: {server_params}")
        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}, error type: {type(e)}")
            raise
        stdio, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

        await session.initialize()

        # List available tools from this server
        response = await session.list_tools()
        server_tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in server_tools])
        
        # Store session with its path and tools
        self.sessions[server_script_path] = {
            "session": session,
            "tools": server_tools
        }
        
        # Update our combined list of available tools
        self._update_available_tools()

    def _update_available_tools(self):
        """Update the complete list of all available tools from all connected servers"""
        tools = []
        for server_info in self.sessions.values():
            tools.extend(server_info["tools"])
        
        # Filter out any duplicate tools (same name)
        tool_names = set()
        unique_tools = []
        for tool in tools:
            if tool.name not in tool_names:
                tool_names.add(tool.name)
                unique_tools.append(tool)
        
        self.available_tools = unique_tools

    async def get_response(self, history: list[dict]) -> Message:
        """Get a response from Claude using the provided conversation history
        
        Args:
            history: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            The Claude Message response
        """
        # Convert our tools to the format expected by Anthropic API
        anthropic_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in self.available_tools]
        
        # Get response from Claude
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=1000,
            system=self.system_prompt,
            messages=history,
            tools=anthropic_tools
        )
        
        return response

    async def use_tool(self, tool_name: str, tool_args: dict, id: str) -> CallToolResult:
        """Use a specific tool with the provided arguments
        
        Args:
            tool_name: Name of the tool to use
            tool_args: Arguments to pass to the tool
            id: Unique identifier for the tool call
            
        Returns:
            Dictionary with the tool result and metadata
        """
        # Find which server has this tool
        server_path = None
        for path, server_info in self.sessions.items():
            if any(tool.name == tool_name for tool in server_info["tools"]):
                server_path = path
                break
        
        if not server_path:
            raise ValueError(f"Tool {tool_name} not found in any connected server")

        # Execute tool call using the correct session
        session = self.sessions[server_path]["session"]
        session = cast(ClientSession, session)  # Ensure correct type
        result = await session.call_tool(tool_name, tool_args)
        return self.decode_results(result)
    
    def decode_results(self, results: CallToolResult) -> CallToolResult:
        """Decode the results from Rapidata

        Args:
            results (CallToolResult): The results from Rapidata

        Returns:
            CallToolResult: The decoded results
        """
        decoded_contents = []

        for content in results.content:
            if content.type == 'text':
                try:
                    # Check if the text contains escape sequences that need decoding
                    if '\\u' in content.text:
                        decoded_text = content.text.encode('utf-8').decode('unicode_escape')
                        decoded_contents.append(TextContent(type='text', text=decoded_text))
                    else:
                        # Keep the original text if no escape sequences
                        decoded_contents.append(content)
                except Exception as e:
                    logger.error(f"Error decoding text: {str(e)}", exc_info=True)
                    decoded_contents.append(content)
            else:
                decoded_contents.append(content)

        return CallToolResult(content=decoded_contents, isError=results.isError)
    
    def get_available_tools_info(self) -> str:
        """Get information about available tools
        
        Returns:
            A string with information about connected servers and tools
        """
        return f"Connected to {len(self.sessions)} servers with {len(self.available_tools)} total tools\nAvailable tools: {', '.join([tool.name for tool in self.available_tools])}"

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def chat_loop(client: MCPClient):
    """Run an interactive chat loop with the given MCPClient instance
    
    Args:
        client: An initialized MCPClient instance
    """
    print("\nMCP Client Started!")
    print(client.get_available_tools_info())
    print("\nType your queries, 'clear' to reset conversation, or 'quit' to exit.")

    while True:
        try:
            query = input("\nQuery: ").strip()

            if query.lower() == 'quit':
                break
            
            if query.lower() == 'clear':
                # Clear conversation history
                print("\nClearing conversation history...")
                client.reset_conversation()
                continue

            # Process query with real-time updates (prints happen inside the method)
            await client.get_response(query)
            # We don't need to print the response again since it's already printed incrementally

        except Exception as e:
            print(f"\nError: {str(e)}")
            import traceback
            print(traceback.format_exc())


async def main():
    client = MCPClient()
    try:
        await client.connect_to_server("C:\\Rapidata\\Claude\\rapidata\\rapidata_human_api.py")
        await client.connect_to_server("C:\\Rapidata\\Claude\\image-gen\\imagegen.py")
        
        # Now the chat loop is separate from the MCPClient class
        await chat_loop(client)
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
