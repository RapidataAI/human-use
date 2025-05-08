import streamlit as st
import os
from datetime import datetime
from mcp_client import MCPClient
import asyncio
from dotenv import load_dotenv
import logging
load_dotenv()


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
    
    return client


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
            st.session_state.messages.append({"role": "assistant", "content": text_content})
            with st.chat_message("assistant"):
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
                
                # Display tool call info in UI
                tool_call_msg = f"[Calling tool {content.name} with args {content.input}]"
                st.session_state.messages.append({"role": "assistant", "content": tool_call_msg})
                with st.chat_message("assistant"):
                    st.write(tool_call_msg)

                # Execute the tool
                tool_result = await client.use_tool(content.name, content.input, content.id)

                # Display tool result in UI
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
                    
                    # Join the text items into a nicely formatted list
                    formatted_result = ", ".join(text_items)
                else:
                    # If it's not a list, just use the content directly
                    formatted_result = str(tool_result.content)

                # Display the formatted tool result in UI
                tool_result_msg = f"[Tool result: {formatted_result}]"
                st.session_state.messages.append({"role": "assistant", "content": tool_result_msg})
                with st.chat_message("assistant"):
                    st.write(tool_result_msg)

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


async def main():
    st.title("Chat with Claude")
    
    initialize_session_state()

    # Add CSS for the collapsible sidebar and toggle button
    st.markdown("""
    <style>
        /* Hide the sidebar when not visible */
        .sidebar-hidden {
            display: none !important;
        }
        
        /* Toggle button styles */
        .toggle-button {
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
        }
        
        /* Rotate triangle for open/closed state */
        .triangle-right {
            width: 0;
            height: 0;
            border-top: 8px solid transparent;
            border-bottom: 8px solid transparent;
            border-left: 12px solid #4c4c4c;
            display: inline-block;
        }
        
        .triangle-left {
            width: 0;
            height: 0;
            border-top: 8px solid transparent;
            border-bottom: 8px solid transparent;
            border-right: 12px solid #4c4c4c;
            display: inline-block;
        }
    </style>
    """, unsafe_allow_html=True)

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
    
    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
                
        # Model selection
        model = st.selectbox(
            "Select Claude Model",
            ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"],
            index=0,
            key="model",
            on_change=on_model_change
        )
        
        # Add a button to reset the conversation
        if st.button("New Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_history = []  # Also reset the API conversation history
            st.rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
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


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
