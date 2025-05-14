from PIL import Image
import streamlit as st
import os
from datetime import datetime
from mcp_client import MCPClient
import asyncio
from dotenv import load_dotenv
import logging
import json
import time
from typing import Any, List, Dict, Optional, Union
import random

load_dotenv()

# Global theme color constant
THEME_COLOR = "#0077ff"  # Default blue theme

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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


def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "client" not in st.session_state:
        st.session_state.client = None
    if "client_initialized" not in st.session_state:
        st.session_state.client_initialized = False
    if "sidebar_visible" not in st.session_state:
        st.session_state.sidebar_visible = True
    if "model" not in st.session_state:
        st.session_state.model = "claude-3-7-sonnet-20250219"
    if "previous_model" not in st.session_state:
        st.session_state.previous_model = st.session_state.model
    if "animation_speed" not in st.session_state:
        st.session_state.animation_speed = 50  # milliseconds


def set_api_key():
    """Set the API key and update session state"""
    if st.session_state.claude_api_key:
        os.environ["ANTHROPIC_API_KEY"] = st.session_state.claude_api_key
        st.session_state.api_key_set = True
        st.success("API key set successfully!")
    else:
        st.error("Please enter an API key.")


async def initialize_client(model: str = "claude-3-7-sonnet-20250219") -> MCPClient:
    """Initialize the MCPClient if it hasn't been initialized yet"""
    client = MCPClient(model=model)
    rapidata_mcp_path = os.environ.get("PATH_TO_RAPIDATA_MCP")
    if rapidata_mcp_path:
        await client.connect_to_server(rapidata_mcp_path)
    else:
        logger.warning("Rapidata MCP path not found")
    image_generation_mcp_path = os.environ.get("PATH_TO_IMAGE_GENERATION_MCP")
    if image_generation_mcp_path:
        await client.connect_to_server(image_generation_mcp_path)
    else:
        logger.warning("Image generation MCP path not found")
    
    return client


def format_tool_input(tool_input: Dict[str, Any]) -> str:
    """Format tool input for display in a more readable way"""
    try:
        formatted = json.dumps(tool_input, indent=2)
        return formatted
    except:
        return str(tool_input)


async def get_chat_response(query: str, client: MCPClient) -> str:
    """
    Get a response from Claude API, maintaining conversation history
    
    Args:
        query: User's query text
        client: MCPClient instance
        
    Returns:
        Response from Claude
    """
    # Initialize conversation_history if it doesn't exist
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # Add current user query to conversation history
    st.session_state.conversation_history.append({
        "role": "user", 
        "content": [{"type": "text", "text": query}]
    })
    
    # Get response using the full conversation history
    response = await client.get_response(history=st.session_state.conversation_history)

    while True:
        has_tool_calls = False

        # Process text content
        text_content = ""
        for content in response.content:
            if content.type == 'text':
                text_content += content.text
        
        if text_content:
            st.session_state.messages.append({"role": "assistant", "content": text_content, "type": "text"})
            with st.chat_message("assistant", avatar="🤖"):
                st.write(text_content)

        # Create assistant message for conversation history
        assistant_content = []
        for content in response.content:
            if content.type == 'text':
                assistant_content.append({"type": "text", "text": content.text})
            elif content.type == 'tool_use':
                has_tool_calls = True
                assistant_content.append({
                    "type": "tool_use",
                    "id": content.id,
                    "name": content.name,
                    "input": content.input
                })
                
                # Store tool call info in session state
                tool_call_msg = {"role": "assistant", "content": content.input, "type": "tool_call", "name": content.name, "id": content.id}
                st.session_state.messages.append(tool_call_msg)
                
                # Display animated tool call in UI
                with st.chat_message("assistant", avatar="🛠️"):
                    tool_container = st.container()
                    with tool_container:
                        st.markdown(f"<div class='tool-header'><span class='tool-name'>{content.name}</span> Tool</div>", unsafe_allow_html=True)
                        st.json(content.input)

                # Execute the tool with a progress animation
                with st.spinner(f"Running tool: {content.name}..."):
                    tool_result = await client.use_tool(content.name, content.input, content.id)

                # Format tool result for display
                formatted_result = ""
                if isinstance(tool_result.content, list):
                    # Extract text from TextContent objects if it's a list of objects
                    text_items = []
                    for item in tool_result.content:
                        if hasattr(item, 'text'):
                            text_items.append(item.text.strip())
                        elif isinstance(item, str):
                            text_items.append(item.strip())
                        elif isinstance(item, dict) and 'text' in item:
                            text_items.append(item['text'].strip())
                    
                    formatted_result = ", ".join(text_items)
                else:
                    # If it's not a list, just use the content directly
                    formatted_result = str(tool_result.content)

                # Store and display the tool result in UI
                tool_result_msg = {"role": "assistant", "content": formatted_result, "type": "tool_result", "for_tool": content.name}
                st.session_state.messages.append(tool_result_msg)
                
                # Display the formatted tool result with proper styling
                with st.chat_message("assistant", avatar="📊"):
                    result_container = st.container()
                    with result_container:
                        st.markdown(f"<div class='result-header'>Result from <span class='tool-name'>{content.name}</span></div>", unsafe_allow_html=True)
                        st.markdown(f"```\n{formatted_result}\n```")

                # Add assistant message with tool_use to conversation history
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_content
                })

                # Add tool result as user message
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": tool_result.content
                        }
                    ]
                })

                # Get next response from Claude
                response = await client.get_response(history=st.session_state.conversation_history)
                break  # Break to process the new response
        
        # If no tool calls were made, add the assistant message and exit loop
        if not has_tool_calls and assistant_content:
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": assistant_content
            })
            break
        
        # If we got an empty response with no tool calls, just exit the loop
        if not has_tool_calls and not assistant_content:
            break
    
    return response.content


@st.cache_resource
def get_event_loop():
    """Get or create an event loop that can be reused"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def toggle_sidebar():
    """Toggle sidebar visibility"""
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible


def on_model_change():
    """Callback function when model is changed"""
    if st.session_state.previous_model != st.session_state.model:
        # Clear conversation history when model changes
        st.session_state.messages = []
        st.session_state.conversation_history = []
        # Update the previous model to current
        st.session_state.previous_model = st.session_state.model
        # Update client model if client exists
        if st.session_state.client:
            st.session_state.client.model = st.session_state.model


def apply_custom_css():
    """Apply custom CSS for a more visually appealing interface"""
    theme_color = THEME_COLOR
    
    # Calculate complementary colors for visual hierarchy
    light_theme = f"rgba({int(theme_color[1:3], 16)}, {int(theme_color[3:5], 16)}, {int(theme_color[5:7], 16)}, 0.1)"
    medium_theme = f"rgba({int(theme_color[1:3], 16)}, {int(theme_color[3:5], 16)}, {int(theme_color[5:7], 16)}, 0.3)"
    dark_theme = f"rgba({max(0, int(theme_color[1:3], 16) - 40)}, {max(0, int(theme_color[3:5], 16) - 40)}, {max(0, int(theme_color[5:7], 16) - 40)}, 1.0)"
    
    st.markdown(f"""
    <style>
        /* Overall app styling */

        :root {{
            
            /* bg */          
            --color-background: oklch(16.34% 0.0091 264.28);
            --color-background-secondary: oklch(20.27% 0.0118 254.1);
            
            /* text */
            --color-text-primary: oklch(0.967 0.003 264.542);
            --color-text-secondary: oklch(55.55% 0 0);

            /* borders */          
            --color-border-primary: oklch(28.04% 0.0119 264.36);           
        }}
        
        /* Sidebar, dropdown menu */
        
        .stSelectbox > div > div {{
            background-color: var(--color-background) !important;
            border-color: var(--color-border-primary) !important;
        }}

        ul[data-testid="stSelectboxVirtualDropdown"] {{
            background-color: var(--color-background) !important;
        }}
    
        /* dropdown top right */
        
        .stMainMenuPopover > div  {{
            background-color: var(--color-background) !important;
            border-color: var(--color-border-primary) !important;
        }}

        .stMainMenuPopover li {{
            background-color: inherit !important;
        }}
   
        /* dialog */
        
        .stDialog > div > div {{
            background-color: var(--color-background) !important;
            border-color: var(--color-border-primary) !important;
        }}
        
        .stDialog > div > div .st-bp {{
            background-color: inherit !important;  
        }}
        
        /* button */
        
        button[kind="secondary"] {{
            background-color: var(--color-background) !important;
            color: var(--color-text-primary) !important;
            border-color: var(--color-border-primary) !important;
        }}
        
        /* chat */
        
        .stMainBlockContainer {{
            max-width: 800px;
        }}
        
        .stChatMessage {{
            background-color: var(--color-background-secondary) !important;
        }}
        
        div[data-testid="stChatMessageContent"] {{
            background-color: var(--color-background-secondary) !important;
            border-radius: 4px !important;
        }}
        
        .react-json-view {{
            background-color: inherit !important;
        }}

        .stCode pre {{
            background-color: inherit !important;
            border: none !important;
            color: inherit !important;
        }}
        
        /* textarea input */

        .stChatInput {{
            border-color: var(--color-border-primary) !important;
        }}
        
        .stChatInput > div{{
            background-color: var(--color-background-secondary) !important;
        }}
        
        .stChatInput > div > div > div {{
            background-color: var(--color-background-secondary) !important;
        }}
        
        .stChatInput button {{
            color: var(--color-text-secondary) !important;
        }}
        
        textarea::placeholder {{
            color: var(--color-text-secondary) !important;
        }}
        
        textarea::placeholder {{
            color: white !important;
        }}
        textarea::placeholder {{
            color: var(--color-text-secondary) !important;
        }} 
       
        hr {{
            background-color: var(--color-border-primary) !important;
        }}

        * {{   
            color: var(--color-text-primary) !important;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--color-background) !important;
        }}
        
        .stBottom > div {{
            background-color: var(--color-background) !important;
        }}
        
        .stAppHeader {{
            background-color: var(--color-background) !important;
        }}
        
        .stMain {{
            background-color: var(--color-background) !important;
        }}
        
        .stApp {{
            background-color: var(--color-background) !important;
        }}
        
        .stSidebar {{
            background-color: var(--color-background) !important;
            border-color: var(--color-border-primary) !important;
        }}
        
        /* Header styling */
        .main h1 {{
            color: {theme_color};
            font-size: 2.5rem;
            margin-bottom: 2rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .main h1:before {{
            content: "🚀";
            font-size: 2.2rem;
        }}
        
        /* Message container styling */
        .stChatMessage {{
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }}
        
        .stChatMessage:hover {{
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        
        /* Tool styling */
        
        .tool-header {{
            background-color: {theme_color};
            color: white;
            padding: 8px 15px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
            margin-bottom: 0;
            display: flex;
            align-items: center;
        }}
        
        .tool-name {{
            background-color: rgba(255,255,255,0.2);
            border-radius: 4px;
            padding: 3px 8px;
            margin-right: 8px;
            font-family: 'Courier New', monospace;
        }}
        
        .result-header {{
            background-color: {dark_theme};
            color: white;
            padding: 8px 15px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
            margin-bottom: 0;
            display: flex;
            align-items: center;
        }}
        
        /* Chat message styling */

        [data-testid="stChatMessageContent"] {{
            background-color: white;
            border-radius: 10px;
            padding: 10px 15px;
            border-left: 4px solid {theme_color};
        }}
        
        /* User message specific styling */
        
        [data-testid="stChatMessage"] [data-testid="stHorizontalBlock"]:has([data-testid="stChatMessageContent"]) {{
            background-color: {light_theme};
            border-radius: 12px;
            padding: 0.5rem;
        }}
        
        /* Assistant avatar styling */

        .stChatMessage .stAvatar {{
            border: 2px solid {medium_theme};
            padding: 2px;
            border-radius: 50%;
            background-color: white;
        }}
        
        /* Sidebar specific styling */
        
        [data-testid="stSidebar"] {{
            background-color: #f0f2f5;
            border-right: 1px solid #e1e4e8;
        }}
        
        [data-testid="stSidebar"] .stButton button {{
            background-color: {theme_color};
            color: white !important;
            border-radius: 8px;
            font-weight: 500;
            border: none;
            padding: 0.5rem 1rem;
            transition: all 0.2s;
        }}
        
        [data-testid="stSidebar"] .stButton button:hover {{
            background-color: {theme_color}dd;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        /* Fix button color on focus/active state */
        
        [data-testid="stSidebar"] .stButton button:focus,
        [data-testid="stSidebar"] .stButton button:active {{
            color: white !important;
            background-color: {theme_color};
            box-shadow: 0 0 0 0.2rem {medium_theme};
            outline: none;
        }}
        
        /* Code block styling */
        
        pre {{
            background-color: #f1f3f5;
            border-radius: 0 0 8px 8px;
            padding: 1rem;
            margin-top: 0;
            overflow-x: auto;
            border: 1px solid #dee2e6;
            border-top: none;
        }}
        
        code {{
            font-family: 'Courier New', monospace;
        }}
        
        /* Hide the sidebar when not visible */
        .sidebar-hidden {{
            display: none !important;
        }}
        
        /* Toggle button styles */

        .toggle-button {{
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 1000;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px 8px;
            cursor: pointer;
            transition: transform 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .toggle-button:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        /* Rotate triangle for open/closed state */
        
        .triangle-right {{
            width: 0;
            height: 0;
            border-top: 8px solid transparent;
            border-bottom: 8px solid transparent;
            border-left: 12px solid {theme_color};
            display: inline-block;
        }}
        
        .triangle-left {{
            width: 0;
            height: 0;
            border-top: 8px solid transparent;
            border-bottom: 8px solid transparent;
            border-right: 12px solid {theme_color};
            display: inline-block;
        }}
        
        /* Chat input styling */
        
        [data-testid="stChatInput"] {{
            border-radius: 12px;
            border: 2px solid {medium_theme};
            padding: 0.5rem;
            transition: all 0.3s ease;
        }}
        
        [data-testid="stChatInput"]:focus-within {{
            border-color: {theme_color};
            box-shadow: 0 0 0 3px {light_theme};
        }}
        
        /* Loading animation */
        
        .stSpinner {{
            border-color: {theme_color} !important;
        }}
        
        /* Animated badge for tool calls */
        
        @keyframes pulse {{
            0% {{ opacity: 0.6; transform: scale(1); }}
            50% {{ opacity: 1; transform: scale(1.05); }}
            100% {{ opacity: 0.6; transform: scale(1); }}
        }}
        
        .animated-badge {{
            display: inline-block;
            background-color: {theme_color};
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            animation: pulse 1.5s infinite;
        }}
        
        /* Branding in footer */

        .footer {{
            position: fixed;
            bottom: 0;
            right: 0;
            background-color: rgba(255,255,255,0.8);
            padding: 10px 15px;
            border-radius: 8px 0 0 0;
            font-size: 12px;
            color: #666;
            backdrop-filter: blur(5px);
        }}
        
        .powered-by {{
            font-weight: bold;
            color: {theme_color};
        }}
    </style>
    """, unsafe_allow_html=True)


im = Image.open("favicon.ico")


async def main():
    st.set_page_config(
        page_title="Rapidata - Human Use",
        page_icon=im,
    )
    
    initialize_session_state()
    
    # Apply custom styling
    apply_custom_css()
    
    # Main app header
 
    
    st.markdown("<h1>Human Use</h1>", unsafe_allow_html=True)
    
    # Add toggle button outside of the sidebar
    if st.session_state.sidebar_visible:
        toggle_icon = '<div class="triangle-left"></div>'
        toggle_position = "left: calc(var(--sidebar-width) - 25px);"
    else:
        toggle_icon = '<div class="triangle-right"></div>'
        toggle_position = "left: 10px;"
    
    st.markdown(f"""
    <div onclick="window.parent.document.querySelector('[data-testid=stSidebar]').classList.toggle('sidebar-hidden'); 
                 this.querySelector('div').classList.toggle('triangle-right');
                 this.querySelector('div').classList.toggle('triangle-left');
                 this.style.left = this.style.left === '10px' ? 'calc(var(--sidebar-width) - 25px)' : '10px';"
         class="toggle-button" style="{toggle_position}">
        {toggle_icon}
    </div>
    """, unsafe_allow_html=True)

    # Add JavaScript to toggle the sidebar class based on session state
    if not st.session_state.sidebar_visible:
        st.markdown("""
        <script>
            (function() {
                const sidebar = window.parent.document.querySelector('[data-testid=stSidebar]');
                if(sidebar) {
                    sidebar.classList.add('sidebar-hidden');
                }
            })();
        </script>
        """, unsafe_allow_html=True)

    # Initialize client if not already initialized
    if not st.session_state.client_initialized:
        with st.spinner("Initializing client..."):
            # Get the selected model from the selectbox
            model = st.session_state.get("model", "claude-3-7-sonnet-20250219")
            st.session_state.client = await initialize_client(model)
            st.session_state.client_initialized = True
    
    client = st.session_state.client
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("<h2 style='color: #333; margin-bottom: 20px;'>⚙️ Configuration</h2>", unsafe_allow_html=True)
        
        # Add some space between sections
        st.markdown("### 🤖 AI Model")
        
        # Model selection with nicer UI
        model = st.selectbox(
            "Select Claude Model",
            ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"],
            index=0,
            key="model",
            on_change=on_model_change
        )
        
        st.markdown("---")
        st.markdown("### 💬 Conversation")
        
        # Add a button to reset the conversation
        if st.button("🔄 New Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.rerun()
    
    # Display chat messages with improved styling
    for i, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]
        msg_type = message.get("type", "text")
        
        # Different avatars based on message type
        avatar = "👤" if role == "user" else "🤖"
        if msg_type == "tool_call":
            avatar = "🛠️"
        elif msg_type == "tool_result":
            avatar = "📊"
        
        with st.chat_message(role, avatar=avatar):
            if msg_type == "text":
                st.write(content)
            elif msg_type == "tool_call":
                tool_name = message.get("name", "Unknown Tool")
                st.markdown(f"<div class='tool-header'><span class='tool-name'>{tool_name}</span> Tool</div>", unsafe_allow_html=True)
                st.json(content)
            elif msg_type == "tool_result":
                tool_name = message.get("for_tool", "Tool")
                st.markdown(f"<div class='result-header'>Result from <span class='tool-name'>{tool_name}</span></div>", unsafe_allow_html=True)
                st.markdown(f"```\n{content}\n```")
    
    # Chat input with placeholder text
    user_input = st.chat_input("Ask anything or request data from real humans...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input, "type": "text"})
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.write(user_input)
        
        # Format messages for API
        api_messages = []
        for msg in st.session_state.messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Get Claude's response with a spinner
        with st.spinner("Claude is thinking..."):
            try:
                await get_chat_response(user_input, client)
            except Exception as e:
                st.error(f"Error communicating with Claude API: {str(e)}")
    
    # Add branding footer
    st.markdown(
        """
        <div class="footer">
            <span class="powered-by">Powered by Rapidata</span> • Human insights at scale
        </div>
        """, 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
