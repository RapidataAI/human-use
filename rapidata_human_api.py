from mcp.server.fastmcp import FastMCP
from rapidata import RapidataClient, LanguageFilter, LabelingSelection, RetrievalMode 
import os
from typing import Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rapidata_mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
logger.info("Initializing FastMCP server with name 'rapidata'")
mcp = FastMCP("rapidata")

@mcp.tool()
async def get_free_text_responses(
    name: str, 
    instruction: str, 
    total_responses: int = 5,
    dir_path: Optional[str] = None,
    language: str | None = None,
) -> dict[str, Any]:
    """get free text responses from humans

    Will ask actual humans to provide some short free text responses to the question.

    Args:
        name (str): The name of the order (will not effect the results but used to identify the order).
        instruction (str): The question asked to the people. They will try to answer is. (example "Who is your favorite actor?")
        total_responses (int): The total number of responses that will be collected. More responses will take SIGNIFICANTLY longer. defaults to 5.
        dir_path (Optional[str]): path to the directory containing images. If not provided, a default image will be used.
            If provided, the images in the directory will be used as datapoints. (EACH datapoint will get the amount of responses specified in total_responses)
        language (str | None): The language the respondents speak. Has to be given as 2 LOWERCASE letters. If not provided, the question will be asked to all respondents.
    Returns:
        dict[str, Any]: dictionary containing the final elo rankings of the images
    """
    logger.info(f"get_free_text_responses called with name: {name}, instruction: {instruction}")
    logger.debug(f"Total responses: {total_responses}, dir_path: {dir_path}")
    
    try:
        client = RapidataClient()

        if dir_path is not None:
            files = os.listdir(dir_path)
            datapoints = [os.path.join(dir_path, f) for f in files]
            logger.debug(f"Using images from directory: {dir_path}")
        else:
            datapoints = ["https://assets.rapidata.ai/152c11b5-c428-4489-ad83-1651ebfe0efd.jpeg"]
            logger.debug("No directory path provided, using default image")

        filters = []
        if language:
            filters.append(LanguageFilter(language_codes=[language]))

        logger.info("Creating free text order")
        order = client.order.create_free_text_order(
            name=name,
            instruction=instruction,
            datapoints=datapoints,
            responses_per_datapoint=total_responses,
            selections=[LabelingSelection(amount=1, retrieval_mode=RetrievalMode.Random)],
            filters=filters,
        ).run()
        
        logger.info("Free text order created and run successfully")

        try:
            order.view()
        except Exception as e:
            logger.error(f"Error viewing order: {str(e)}. Make sure to update your rapidata version.")
        
        results = order.get_results()
        processed_results = {result["originalFileName"]: result["aggregatedResults"] for result in results["results"]}
        logger.debug(f"Free text results processed: {processed_results}")
        logger.info("Successfully retrieved free text results")
        
        return processed_results
    except Exception as e:
        logger.error(f"Error in get_free_text_responses: {str(e)}", exc_info=True)
        return {"error": f"Failed to get free text responses: {str(e)}"}

@mcp.tool()
async def get_human_image_classification(
    name: str,
    instruction: str,
    answer_options: list[str],
    dir_path: Optional[str] = None,
    total_responses: int = 25,
    language: str | None = None,
) -> list[dict[str, float]]:
    """get classification responses from humans

    Will ask actual humans to classify the images in the directory.

    Args:
        name (str): The name of the order (will not effect the results but used to identify the order).
        instruction (str): The question asked to the people. They will try to select the answer based on the question. (example "What is shown in the image?")
        answer_options (list[str]): The options that will be shown to the people. They will have to choose one of them. (maximum 6 options).
            (example ["cat", "dog", "car", "tree"])
        dir_path (Optional[str]): path to the directory containing images. If not provided, a default image will be used.
        total_responses (int): The total number of responses that will be collected. More responses will take longer but give a clearer results. defaults to 25.
            if a directory is provided, this will be the number of responses PER image.
        language (str | None): The language the respondants speak. Has to be given as 2 LOWERCASE letters. If not provided, the question will be asked to all respondants.
    Returns:
        list[dict[str, float]]: list of dictionaries containing the classification results for each image
    """
    logger.info(f"get_human_image_classification called with name: {name}, instruction: {instruction}")
    logger.debug(f"Answer options: {answer_options}, total_responses: {total_responses}, dir_path: {dir_path}")
    
    try:
        client = RapidataClient()

        if dir_path is not None:
            files = os.listdir(dir_path)
            full_paths = [os.path.join(dir_path, f) for f in files]
            logger.debug(f"Using images from directory: {dir_path}")
        else:
            full_paths = ["https://assets.rapidata.ai/152c11b5-c428-4489-ad83-1651ebfe0efd.jpeg"]
            logger.debug("No directory path provided, using default image")

        filters = []
        if language:
            filters.append(LanguageFilter(language_codes=[language]))

        logger.info("Creating classification order")
        order = client.order.create_classification_order(
            name=name,
            instruction=instruction,
            answer_options=answer_options,
            datapoints=full_paths,
            responses_per_datapoint=total_responses,
            filters=filters,
            selections=[LabelingSelection(amount=3, retrieval_mode=RetrievalMode.Random)],
        ).run()

        logger.info("Classification order created and run successfully")

        try:
            order.view()
        except Exception as e:
            logger.error(f"Error viewing order: {str(e)}. Make sure to update your rapidata version.")

        results = order.get_results()["results"]
        processed_results = {result["originalFileName"]: result["summedUserScoresRatios"] for result in results}
        logger.debug(f"Classification results processed")
        logger.info("Successfully retrieved classification results")
        
        return processed_results
    except Exception as e:
        logger.error(f"Error in get_human_image_classification: {str(e)}", exc_info=True)
        return {"error": f"Failed to get classification results: {str(e)}"}

@mcp.tool()
async def get_human_image_ranking(
    dir_path: str, 
    name: str,
    instruction: str,
    total_comparison_budget: int = 25,
) -> dict[str, Any]:
    """rank images in a local dir based on *human* preference

    Will ask hundreds of actual humans to rank the images in the directory.

    Args:
        dir_path (str): path to the directory containing images
        name (str): The name of the order (will not effect the results but used to identify the order).
        instruction (str): The question asked to the people. Based on this they will rank the images. (example "Which image looks better?")
            There will be pair wise matchups rated by humans. The results will effect the elo score of the images. The question will be shown with 2 images.
        total_comparison_budget (int): The total number of comparisons to be made. This is the total number of pairwise matchups that will be shown to humans. 
            The more images there are the more budget is required and the more precise the results will be. But it will also take longer. defaults to 25.

    Returns:
        dict[str, Any]: dictionary containing the final elo rankings of the images
    """
    logger.info(f"get_human_image_ranking called with name: {name}, instruction: {instruction}, dir_path: {dir_path}")
    logger.debug(f"Total comparison budget: {total_comparison_budget}")
    
    try:
        client = RapidataClient()
        
        files = os.listdir(dir_path)
        paths = [os.path.join(dir_path, f) for f in files]
        logger.debug(f"Using images from directory: {dir_path}")

        logger.info("Creating ranking order")
        order = client.order.create_ranking_order(
            name=name,
            instruction=instruction,
            datapoints=paths,
            responses_per_comparison=1,
            total_comparison_budget=total_comparison_budget,
            selections=[LabelingSelection(amount=3, retrieval_mode=RetrievalMode.Random)],
        ).run()
        
        logger.info("Ranking order created and run successfully")
        
        try:
            order.view()
        except Exception as e:
            logger.error(f"Error viewing order: {str(e)}. Make sure to update your rapidata version.")
        
        results = order.get_results()
        processed_results = results["summary"]
        logger.debug(f"Ranking results processed")
        logger.info("Successfully retrieved ranking results")
        
        return processed_results  
    except Exception as e:
        logger.error(f"Error in get_human_image_ranking: {str(e)}", exc_info=True)
        return {"error": f"Failed to rank images: {str(e)}"}

@mcp.tool()
async def get_human_text_comparison(
    text_pairs: list[list[str]],
    name: str, 
    instruction: str, 
    total_responses: int = 15,
    language: str = "en",
) -> list[dict[str, int]]:
    """compare two texts and get human preference

    Will ask actual humans to compare the two texts and choose the better one.

    Args:
        text_pairs (list[list[str]]): list of pairs of texts to be compared. Each pair should be a list of exactly two strings.
        name (str): The name of the order (will not effect the results but used to identify the order).
        instruction (str): The question asked to the people. They will try to choose the better text based on this. (example "Which text is do you prefer?")
        total_responses (int): The total number of responses that will be collected. More responses will take longer but give a clearer results. defaults to 15.
        language (str): The language of the texts. Has to be given as 2 LOWERCASE letters defaults to "en".

    Returns:
        list[dict[str, int]]: list of dictionaries containing the comparison results for each pair of texts
    """
    logger.info(f"get_human_text_comparison called with name: {name}, instruction: {instruction}")
    logger.debug(f"Total responses: {total_responses}, language: {language}")
    
    try:
        client = RapidataClient()

        logger.info("Creating text comparison order")
        order = client.order.create_compare_order(
            name=name,
            instruction=instruction,
            datapoints=text_pairs,
            responses_per_datapoint=total_responses,
            data_type="text",
            filters=[LanguageFilter(language_codes=[language])],
            selections=[LabelingSelection(amount=2, retrieval_mode=RetrievalMode.Random)],
        ).run()

        logger.info("Text comparison order created and run successfully")

        try:
            order.view()
        except Exception as e:
            logger.error(f"Error viewing order: {str(e)}. Make sure to update your rapidata version.")
        
        results = order.get_results()
        processed_results = [result["aggregatedResults"] for result in results["results"]]
        logger.debug(f"Text comparison results processed")
        logger.info("Successfully retrieved text comparison results")
        
        return processed_results
    except Exception as e:
        logger.error(f"Error in get_human_text_comparison: {str(e)}", exc_info=True)
        return {"error": f"Failed to compare texts: {str(e)}"}

if __name__ == "__main__":
    logger.info("Starting FastMCP server for rapidata")
    
    try:
        logger.info("Running FastMCP server with stdio transport")
        mcp.run(transport='stdio')
    except Exception as e:
        logger.critical(f"Fatal error running MCP server: {str(e)}", exc_info=True)
        print(f"Error running MCP server: {str(e)}")
