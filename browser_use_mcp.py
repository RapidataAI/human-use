from mcp.server.fastmcp import FastMCP
import logging


from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv
load_dotenv()



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("browser_use.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("Initializing FastMCP server with name 'browser_use'")
mcp = FastMCP("browser_use")


@mcp.tool()
async def do_task(task: str) -> str:
    """Do the given task using the browser
    
    Args:
        task: The task to do
            example: "find the current price of bitcoin"

    Returns:
        The result of the task
    """
    logger.info(f"Running agent with task: {task}")
    result = await run_agent(task)
    return result


async def run_agent(task: str) -> str:
    agent = Agent(
        task=task,
        llm=ChatOpenAI(model="gpt-4o"),
    )
    history = await agent.run()
    final_result = history.final_result()
    return final_result


if __name__ == "__main__":
    logger.info("Starting FastMCP server for browser use")
    try:
        logger.info("Running FastMCP server with stdio transport")
        mcp.run(transport='stdio')
    except Exception as e:
        logger.critical(f"Fatal error running MCP server: {str(e)}", exc_info=True)
        print(f"Error running MCP server: {str(e)}")
