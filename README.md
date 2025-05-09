<a href="https://www.rapidata.ai">
<img src="https://cdn-uploads.huggingface.co/production/uploads/66f5624c42b853e73e0738eb/jfxR79bOztqaC6_yNNnGU.jpeg" alt="Rapidata Logo">
</a>

# Human Use 🤝
[![GitHub stars](https://img.shields.io/github/stars/RapidataAI/human-use?style=social)](https://github.com/RapidataAI/human-use/stargazers)
[![Documentation](https://img.shields.io/badge/Documentation-📗-blue)](https://docs.rapidata.ai)
[![Twitter Follow](https://img.shields.io/twitter/follow/RapidataAI?style=social)](https://x.com/RapidataAI)

🤖 Human Use is the easiest way to connect your AI agents with human intelligence via the Rapidata API.


## Human Use in Action

Ranking different image generation models.

[![AI Agent Ranking](https://github.com/user-attachments/assets/8e6697c0-3ffa-44fa-89eb-e40e30d4ab53)](https://youtu.be/YYjGM4ihuw8)

Finding the best slogan

[![AI Agent Slogan](https://github.com/user-attachments/assets/28148703-7fb2-4876-9528-bcfd8ce9b50a)](https://youtu.be/n36ovFDvH-Y)

## App Setup

### Clone Repositories
Clone the following repositories along side the current one (do not clone them inside the current one, can be whereever it's convenient).:
```bash
git clone https://github.com/RapidataAI/human-use.git
```

## Environment Configuration

1. Create a .env file in the human-use repository
2. Use the .env.example file as a template
3. Replace the default values with your own credentials/settings

> **Note:** paths should be ABSOLUTE paths

## Installation with UV

### Prerequisites
Install uv if you haven't already:
```bash
# For MacOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# For Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup Instructions (in the human-use repository)

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

If you encounter issues, with the dependencies make sure that "which python" and "which streamlit" are the same path. If they are not the same path, run "python -m streamlit run app.py" instead of "streamlit run app.py".
