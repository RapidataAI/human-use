# Rapidata and Image Generation Setup

## Clone Repositories
Clone the following repositories along side the current one (do not clone them inside the current one, can be whereever it's convenient).:
```bash
git clone https://github.com/RapidataAI/mcp-imagegen.git

git clone https://github.com/RapidataAI/rapidata-mcp.git
```

## Environment Configuration

1. Create a .env file in each repository directory where it's needed.
2. Use the .env.example file as a template
3. Replace the default values with your own credentials/settings

> **Note:** All paths should be ABSOLUTE paths

## Installation with UV

### Prerequisites
Install uv if you haven't already:
```bash
# For MacOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# For Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup Instructions (in the mcp-app)

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

## Run the application
```bash
streamlit run app.py
```

### Troubleshooting

If you encounter issues, with the dependencies make sure that which python and which streamlit. if they are not the same path. run "python -m streamlit run app.py" instead of "streamlit run app.py".
