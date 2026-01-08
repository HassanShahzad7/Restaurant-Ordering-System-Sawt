"""Streamlit frontend for Sawt Restaurant Ordering Chatbot."""

import asyncio
import uuid

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

import re

from sawt.db.connection import init_db, close_db, DatabasePool
from sawt.graph.state import create_initial_state
from sawt.graph.workflow import graph
from sawt.tools.menu_tools import load_menu_cache


def clean_response(response: str) -> str:
    """Clean AI response by removing internal reasoning/analysis text that shouldn't be shown to users."""
    if not response:
        return response

    # Patterns to remove (LLM internal thinking that leaked into response)
    patterns_to_remove = [
        r'من analysis:.*',  # Arabic "from analysis:" and everything after
        r'\(We need to respond.*',  # English internal reasoning
        r'The last assistant.*',  # English internal reasoning
        r'Now user hasn\'t.*',  # English internal reasoning
        r'But system asks.*',  # English internal reasoning
        r'Given developer instructions.*',  # English internal reasoning
        r'Check instruction.*',  # English internal reasoning
        r'I\'ll reply with.*',  # English internal reasoning
        r'I\'ll send a short.*',  # English internal reasoning
        r'But must output.*',  # English internal reasoning
        r'Maybe expected to.*',  # English internal reasoning
        r'However there is no.*',  # English internal reasoning
        r'The prompt:.*',  # English internal reasoning
        r'Wait the conversation.*',  # English internal reasoning
        r'But the chat shows.*',  # English internal reasoning
        r'Maybe user will.*',  # English internal reasoning
        r'But we must.*',  # English internal reasoning
        r'Given typical tasks.*',  # English internal reasoning
        r'Keep concise.*',  # English internal reasoning
        r'Use Saudi dialect.*',  # English internal reasoning
        r'So final answer:.*',  # English internal reasoning
        r'أكيد follow developer.*',  # Mixed Arabic/English reasoning
        r'follow developer rules.*',  # Developer rules reasoning
        r'After adding, must ask.*',  # Internal instruction
        r'User next\?.*',  # Internal reasoning
        r'Let\'s produce final.*',  # Internal reasoning
        r'No, user hasn\'t.*',  # Internal reasoning
        r'So we already asked.*',  # Internal reasoning
        r'No further action.*',  # Internal reasoning
        r'But system expects.*',  # Internal reasoning
        r'Done\.\s*$',  # Trailing "Done."
        r'We wait\..*',  # Internal reasoning
    ]

    cleaned = response
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Also remove anything after common reasoning markers
    reasoning_markers = [
        'من analysis:',
        '(We need to',
        'analysis:',
        'The last assistant',
        'Now user hasn\'t',
        'أكيد follow',
        'follow developer',
        'After adding,',
        'User next?',
        'Let\'s produce',
        'We wait.',
        'Done.',
        'No further action',
        'But system expects',
    ]

    for marker in reasoning_markers:
        if marker in cleaned:
            idx = cleaned.find(marker)
            cleaned = cleaned[:idx]

    # Clean up extra whitespace and newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()

    return cleaned


# Page configuration
st.set_page_config(
    page_title="Sawt - نظام طلبات المطعم",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS for RTL support and Arabic styling
st.markdown("""
<style>
    /* RTL support for Arabic */
    .stChatMessage {
        direction: rtl;
        text-align: right;
    }

    .stChatMessage [data-testid="stMarkdownContainer"] {
        direction: rtl;
        text-align: right;
    }

    /* User message styling */
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #e8f4f8;
    }

    /* Assistant message styling */
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #f0f2f6;
    }

    /* Input field RTL */
    .stChatInput textarea {
        direction: rtl;
        text-align: right;
    }

    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    .main-header h1 {
        margin: 0;
        font-size: 2rem;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }

    /* Sidebar styling */
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    /* Order summary card */
    .order-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize Streamlit session state."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_state" not in st.session_state:
        st.session_state.chat_state = create_initial_state(st.session_state.session_id)

    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = False

    if "menu_loaded" not in st.session_state:
        st.session_state.menu_loaded = False


async def initialize_backend():
    """Initialize database and load menu cache."""
    if not st.session_state.db_initialized:
        try:
            await init_db()
            st.session_state.db_initialized = True
        except Exception as e:
            st.warning(f"Database connection issue: {e}")

    if not st.session_state.menu_loaded and st.session_state.db_initialized:
        try:
            pool = await DatabasePool.get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, name_ar, name_en, description_ar, category_ar, category_en, price, is_combo, is_available
                    FROM menu_items
                    WHERE is_available = TRUE
                    """
                )
                items = [
                    {
                        "id": str(row["id"]),
                        "name_ar": row["name_ar"],
                        "name_en": row["name_en"],
                        "description_ar": row["description_ar"],
                        "category_ar": row["category_ar"],
                        "category_en": row["category_en"],
                        "price": float(row["price"]),
                        "is_combo": row["is_combo"],
                    }
                    for row in rows
                ]
                load_menu_cache(items)
                st.session_state.menu_loaded = True
                st.session_state.menu_count = len(items)
        except Exception as e:
            st.warning(f"Could not load menu: {e}")


async def process_message(user_message: str) -> str:
    """Process a user message through the LangGraph workflow."""
    import logging
    from langchain_core.messages import ToolMessage
    logger = logging.getLogger("sawt.streamlit")

    state = st.session_state.chat_state
    logger.info(f"Processing message: {user_message[:50]}...")
    logger.info(f"Current agent: {state.get('current_agent', 'greeting')}")

    # Add user message to state
    state["messages"].append(HumanMessage(content=user_message))

    try:
        # Run the graph with recursion limit to prevent infinite loops
        result = graph.invoke(state, {"recursion_limit": 25})

        # Update session state
        st.session_state.chat_state = result
        logger.info(f"After processing, agent: {result.get('current_agent', 'unknown')}")

        # Get the last AI message (check for AIMessage type, not tool_calls attribute)
        messages = result.get("messages", [])
        logger.info(f"Total messages: {len(messages)}")

        # Log message types for debugging
        for i, msg in enumerate(messages[-5:] if len(messages) > 5 else messages):
            msg_type = type(msg).__name__
            content_preview = str(msg.content)[:50] if hasattr(msg, "content") else "N/A"
            logger.debug(f"  Msg[{i}] {msg_type}: {content_preview}...")

        for msg in reversed(messages):
            # Skip non-AI messages
            if isinstance(msg, (HumanMessage, ToolMessage)):
                continue
            # Skip messages without content
            if not hasattr(msg, "content") or not msg.content:
                continue
            # Skip tool call messages (they have tool_calls list)
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls and len(tool_calls) > 0:
                continue
            # Skip messages that look like JSON (tool results)
            content_str = str(msg.content)
            if content_str.startswith("{") or content_str.startswith("["):
                continue
            # Found a valid response - clean it before returning
            cleaned_content = clean_response(content_str)
            response_preview = cleaned_content[:200] + "..." if len(cleaned_content) > 200 else cleaned_content
            logger.info(f"Returning response ({len(cleaned_content)} chars): {response_preview}")
            return cleaned_content

        logger.warning("No valid AI response found in messages")
        return "عذراً، حدث خطأ. حاول مرة ثانية."

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
        return f"عذراً، حدث خطأ في النظام: {str(e)}"


def reset_conversation():
    """Reset the conversation."""
    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.session_state.messages = []
    st.session_state.chat_state = create_initial_state(st.session_state.session_id)


def render_sidebar():
    """Render the sidebar with info and controls."""
    with st.sidebar:
        st.markdown("### 🍽️ نظام الطلبات")
        st.markdown("---")

        # Session info
        st.markdown(f"**معرف الجلسة:** `{st.session_state.session_id}`")

        if hasattr(st.session_state, 'menu_count'):
            st.markdown(f"**عناصر القائمة:** {st.session_state.menu_count}")

        # Current state
        current_agent = st.session_state.chat_state.get("current_agent", "greeting")
        agent_names = {
            "greeting": "👋 الترحيب (Greeting)",
            "order": "🍔 الطلب (Order)",
            "location": "📍 الموقع (Location)",
            "checkout": "💳 الدفع (Checkout)",
        }
        st.markdown(f"**المرحلة الحالية:**")
        st.info(agent_names.get(current_agent, current_agent))

        st.markdown("---")

        # Reset button
        if st.button("🔄 محادثة جديدة", use_container_width=True):
            reset_conversation()
            st.rerun()

        st.markdown("---")

        # Help section
        with st.expander("💡 أمثلة للمحادثة"):
            st.markdown("""
            - **للترحيب:** مرحبا، السلام عليكم
            - **للطلب:** أبي أطلب أكل، أبي برجر
            - **للبحث:** وش عندكم حار؟ عندكم عصير؟
            - **للموقع:** أنا في حي النرجس
            - **للسلة:** وش في طلبي؟
            """)

        with st.expander("ℹ️ عن النظام"):
            st.markdown("""
            نظام طلبات مطعم ذكي يتحدث اللهجة السعودية.

            **المميزات:**
            - بحث ذكي في القائمة
            - إدارة السلة
            - التحقق من التوصيل
            - أكواد الخصم
            """)


def render_chat():
    """Render the chat interface."""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🍽️ صوت - Sawt</h1>
        <p>نظام طلبات المطعم باللهجة السعودية</p>
    </div>
    """, unsafe_allow_html=True)

    # Chat container
    chat_container = st.container()

    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]

            with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
                st.markdown(content)

    # Welcome message if no messages
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("أهلاً وسهلاً! كيف أقدر أساعدك اليوم؟ 😊")

    # Chat input
    if prompt := st.chat_input("اكتب رسالتك هنا..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("جاري الرد..."):
                response = asyncio.run(process_message(prompt))
                st.markdown(response)

        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()


def main():
    """Main app entry point."""
    # Initialize session state
    init_session_state()

    # Initialize backend
    asyncio.run(initialize_backend())

    # Render UI
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
