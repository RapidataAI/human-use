import os
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import base64
import logging

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("image_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("Initializing FastMCP server with name 'image_generation'")
mcp = FastMCP("image_generation")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_and_save_image(prompt: str, file_name: str) -> str:
    """
    Generate an image from a prompt and save it to a file.
    """
    
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        # quality="low"
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    if not file_name.endswith(".png"):
        file_name = file_name + ".png"
    file_path = f"temp/generated_images/{file_name}"
    with open(file_path, "wb") as f:
        f.write(image_bytes)
    return file_path

@mcp.tool()
async def generate_image_from_text(
    prompts: list[str],
    file_names: list[str],
    clear_directory_before_generation: bool = False,
) -> list[str]:
    """
    Will generate an image from the prompt. And save them under ./temp/generated_images

    Args:
        prompts (list[str]): The prompts to generate the images from.
        file_names (list[str]): The names of the files to save the images under.
        clear_directory_before_generation (bool): Whether to clear the directory before generation. Defaults to False.
            Set to True if you want to clear the directory before generation.

    Returns:
        list[str]: The paths to the generated images.
    """
    if len(prompts) != len(file_names):
        raise ValueError("prompts and file_names must be the same length")
    
    os.makedirs("temp/generated_images", exist_ok=True)

    if clear_directory_before_generation:
        for file in os.listdir("temp/generated_images"):
            os.remove(os.path.join("temp/generated_images", file))

    file_paths = [generate_and_save_image(prompt, file_name) for prompt, file_name in zip(prompts, file_names)]
    return file_paths

if __name__ == "__main__":
    logger.info("Starting FastMCP server for image generation")
    
    try:
        logger.info("Running FastMCP server with stdio transport")
        mcp.run(transport='stdio')
    except Exception as e:
        logger.critical(f"Fatal error running MCP server: {str(e)}", exc_info=True)
        print(f"Error running MCP server: {str(e)}")
