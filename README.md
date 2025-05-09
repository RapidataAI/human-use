<a href="https://www.rapidata.ai">
<img src="https://github.com/user-attachments/assets/d8ff0f04-c636-4e04-b2de-399b33a2805d" alt="Rapidata Human Use Logo">
</a>

<h1 align="center">Human Use 🤝 Enable AI to ask anyone anything</h1>

[![GitHub stars](https://img.shields.io/github/stars/RapidataAI/human-use?style=social&cachebust=1)](https://github.com/RapidataAI/human-use/stargazers)
[![Documentation](https://img.shields.io/badge/Documentation-📗-blue)](https://docs.rapidata.ai)
[![Twitter Follow](https://img.shields.io/twitter/follow/RapidataAI?style=social)](https://x.com/RapidataAI)

🤖 Human Use is the easiest way to connect your AI agents with human intelligence via the Rapidata API.


## Human Use in Action

Finding the best slogan

[![AI Agent Slogan](https://github.com/user-attachments/assets/28148703-7fb2-4876-9528-bcfd8ce9b50a)](https://youtu.be/n36ovFDvH-Y)

Function Naming

[![Cursor Function Naming](https://github.com/user-attachments/assets/5675e705-7dc1-4912-9e5d-389d0798df95)](https://youtu.be/Rc5IIZJ6fgw)

Ranking different image generation models.

[![AI Agent Ranking](https://github.com/user-attachments/assets/8e6697c0-3ffa-44fa-89eb-e40e30d4ab53)](https://youtu.be/YYjGM4ihuw8)

## MCP Server

### Overview

The MCP server is a tool that allows you to connect your AI agents with human intelligence via the Rapidata API.

### Tools

1. get_free_text_responses
    - Will ask actual humans to provide some short free text responses to the question.
2. get_human_image_classification
    - Will ask actual humans to classify the images in the directory.
3. get_human_image_ranking
    - Will ask actual humans to rank the images in the directory.
4. get_human_text_comparison
    - Will ask actual humans to compare two texts and select which one is better.

### Configuration

**Cursor**

add the following to your cursor mcp.json file (usually in ~/.cursor/mcp.json)
```json
{
    "mcpServers": {
        "human-use": {
            "command": "uv",
            "args": [
                "--directory",
                "YOUR_ABSOLUTE_PATH_HERE",
                "run",
                "rapidata_human_api.py"
            ]
        }
    }
}
```

You should now be able to see the human-use server in Cursor settings.

![Cursor MCP](https://github.com/user-attachments/assets/385865dc-af6d-4ea5-8693-62c259185c06)

## App

### Overview

The app is a custom Streamlit app that allows you to use the MCP server. We have built because of [issues](https://github.com/AgentDeskAI/browser-tools-mcp/issues/103) with other clients. Namely the Claude desktop app.

### App Setup

#### Clone Repository

```bash
git clone https://github.com/RapidataAI/human-use.git
```

#### Environment Configuration

Copy the .env.example file to .env and fill it in with your own credentials/settings

> **Note:** paths should be ABSOLUTE paths

#### Installation with UV

##### Prerequisites
Install uv if you haven't already:
```bash
# For MacOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# For Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Setup Instructions (in the human-use repository)

1. Create and activate a virtual environment:
    ```bash
    uv venv

    # On Unix/macOS
    source .venv/bin/activate

    # On Windows
    .venv\Scripts\activate
    ```
2. Install dependencies:
    ```bash
    uv sync
    ```

#### Run the application
```bash
streamlit run app.py
```

#### Troubleshooting

If you encounter issues, with the dependencies make sure that "which python" and "which streamlit" are the same path. If they are not the same path, run "python -m streamlit run app.py" instead of "streamlit run app.py".

If UV is not found, make sure you close all terminals and editors, then re-open a new one and try again.

## Contact

If you have any questions or need further assistance, please contact us at info@rapidata.ai.
