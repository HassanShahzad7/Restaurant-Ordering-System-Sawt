"""LangGraph workflow for the restaurant ordering agent using proper LangGraph agents."""

from typing import Literal, Annotated
import operator
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.checkpoint.memory import MemorySaver

from sawt.graph.state import AgentState
from sawt.logging_config import log_agent_handoff, log_agent_response, log_state_transition

# Logger for context/token logging
context_logger = logging.getLogger("sawt.context")
from sawt.tools import (
    check_delivery_district,
    set_order_type,
    get_order_type_info,
    search_menu,
    get_item_details,
    add_to_order,
    get_current_order,
    update_order_item,
    remove_from_order,
    calculate_total,
    confirm_order,
)
from sawt.config import settings


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses approximation: ~4 characters per token for English, ~2 for Arabic.
    """
    if not text:
        return 0
    # Count Arabic characters (rough heuristic)
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    other_chars = len(text) - arabic_chars
    # Arabic is roughly 2 chars/token, English ~4 chars/token
    return int(arabic_chars / 2 + other_chars / 4)


def estimate_messages_tokens(messages: list) -> int:
    """Estimate total tokens for a list of messages."""
    total = 0
    for msg in messages:
        if hasattr(msg, "content"):
            content = str(msg.content) if msg.content else ""
            total += estimate_tokens(content)
            # Add overhead for message structure
            total += 4  # role, separators
    return total


def log_handoff_context(from_agent: str, to_agent: str, messages: list, memory: dict):
    """Log context transfer at handoff with token estimation."""
    msg_count = len(messages)
    token_estimate = estimate_messages_tokens(messages)

    context_logger.info(f"HANDOFF: {from_agent} → {to_agent}")
    context_logger.info(f"CONTEXT: Transferred {msg_count} messages (est. {token_estimate} tokens)")

    # Log memory/state being transferred
    memory_items = {k: v for k, v in memory.items() if v and k not in ['messages']}
    if memory_items:
        # Truncate long values for logging
        memory_log = {}
        for k, v in memory_items.items():
            if isinstance(v, str) and len(v) > 50:
                memory_log[k] = v[:50] + "..."
            else:
                memory_log[k] = v
        context_logger.info(f"MEMORY: {memory_log}")

    return token_estimate


# Saudi Arabic system prompts for each agent
GREETING_SYSTEM_PROMPT = """أنت موظف استقبال في مطعم سعودي. تتحدث باللهجة السعودية.

مهمتك فقط:
1. ترحب بالعميل بحرارة
2. تحدد نية العميل

مهم جداً: أنت لا تعرف القائمة! لا تذكر أي أصناف أو أسعار.

إذا كان يبي يطلب أكل أو يسأل عن القائمة أو البرجر أو أي صنف:
- قول له "أهلاً وسهلاً! تمام، خلني أحولك لزميلي يحدد موقع التوصيل أول"
- أضف [HANDOFF:location] في نهاية ردك
- لا تذكر أي أصناف من القائمة

إذا كان عنده شكوى، اعتذر له وقول له بنتواصل معه وأضف [HANDOFF:end] في نهاية ردك.

كن ودود وطبيعي. استخدم: تمام، أهلاً، حياك."""

LOCATION_SYSTEM_PROMPT = """أنت موظف توصيل في مطعم سعودي. تتحدث باللهجة السعودية.

لديك الأدوات:
- check_delivery_district: للتحقق من تغطية التوصيل
- set_order_type: لتحديد نوع الطلب (توصيل أو استلام) - مهم جداً!

مهمتك:
1. أولاً اسأل العميل: "تبي توصيل ولا استلام من الفرع؟"

2. إذا اختار توصيل:
   - اسأله عن الحي/المنطقة
   - استخدم check_delivery_district للتحقق من التغطية
   - إذا المنطقة مغطاة: استخدم set_order_type(order_type="delivery", district="اسم الحي", delivery_fee=الرسوم)
   - إذا ما نغطي المنطقة: اعرض عليه الاستلام من الفرع

3. إذا اختار استلام (أو غيّر رأيه من توصيل لاستلام):
   - استخدم set_order_type(order_type="pickup")
   - أخبره إن الفرع في حي العليا

مهم جداً: يجب استخدام set_order_type قبل التحويل!

بعد استخدام set_order_type:
- قول "تمام!" وأضف [HANDOFF:order] في نهاية ردك

كن ودود ومختصر."""

ORDER_SYSTEM_PROMPT = """أنت موظف طلبات في مطعم سعودي. تتحدث باللهجة السعودية.

لديك الأدوات:
- search_menu: للبحث في القائمة
- add_to_order: لإضافة صنف للسلة
- get_current_order: لعرض السلة
- remove_from_order: لحذف صنف من السلة
- update_order_item: لتعديل الكمية

قواعد صارمة - يجب اتباعها:
1. استخدم أداة واحدة أو اثنتين فقط في كل رد
2. بعد إضافة صنف، أرسل رد فوراً واسأل "تبي شي ثاني؟"
3. لا تبحث عن أصناف إضافية من نفسك (مشروبات، بطاطس، حلويات)
4. فقط ابحث عما يطلبه العميل بالضبط

ممنوع:
- البحث عن مشروبات أو جانبيات بدون طلب العميل
- اقتراح أصناف إضافية
- استدعاء search_menu أكثر من مرتين في الرد الواحد

لما العميل يقول "خلاص" أو "بس" أو "لا شكراً" أو "تمام كذا":
قول "تمام! خلني أحولك للمحاسبة لتأكيد الطلب" وأضف [HANDOFF:checkout]

تغيير الرأي (مهم):
- إذا العميل يبي يغير موقع التوصيل أو يغير من توصيل لاستلام:
  قول "تمام، خلني أرجعك لتحديد الموقع" وأضف [HANDOFF:location]

كن مختصر جداً."""

CHECKOUT_SYSTEM_PROMPT = """أنت موظف محاسبة في مطعم سعودي. تتحدث باللهجة السعودية.

لديك الأدوات:
- get_current_order: لعرض السلة
- calculate_total: لحساب المجموع (استخدمها مرة واحدة فقط)
- confirm_order: لتأكيد الطلب النهائي

مهم جداً - قواعد استخدام الأدوات:
- استخدم كل أداة مرة واحدة فقط في كل رد
- بعد استخدام الأداة، أرسل رد للعميل فوراً
- لا تستدعي نفس الأداة مرتين متتاليتين

خطوات العمل:

1. أول رد: استخدم get_current_order و calculate_total، ثم اعرض الملخص واسأل "عندك كود خصم؟"

2. إذا أعطاك كود: استخدم calculate_total مع الكود، اعرض المجموع الجديد، واسأل "وش اسمك الكريم؟"

3. إذا ما عنده كود أو قال لا: اسأل "وش اسمك الكريم؟"

4. بعد الاسم: اسأل "وش رقم جوالك؟"

5. بعد الجوال: استخدم confirm_order وأضف [HANDOFF:end]

تغيير الرأي (مهم جداً):
- إذا العميل يبي يغير موقع التوصيل أو يغير من توصيل لاستلام أو العكس:
  قول "تمام، خلني أرجعك لتحديد الموقع" وأضف [HANDOFF:location]

- إذا العميل يبي يضيف صنف أو يحذف صنف أو يعدل الطلب:
  قول "تمام، خلني أرجعك لموظف الطلبات" وأضف [HANDOFF:order]

تذكر:
- لا تخترع اسم أو رقم - اسألهم دائماً
- الدفع عند الاستلام فقط
- كن مختصر"""


def create_llm():
    """Create the LLM client for OpenRouter."""
    return ChatOpenAI(
        model=settings.openrouter_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=2000,
    )


# Define tools for each agent
location_tools = [check_delivery_district, set_order_type]
order_tools = [search_menu, get_item_details, add_to_order, get_current_order, update_order_item, remove_from_order]
checkout_tools = [calculate_total, confirm_order, get_current_order]


def create_greeting_agent():
    """Create the greeting agent using LangGraph's create_react_agent."""
    llm = create_llm()
    # Greeting agent has no tools, just conversation
    return create_react_agent(
        llm,
        tools=[],
        prompt=GREETING_SYSTEM_PROMPT,
    )


def create_location_agent():
    """Create the location agent using LangGraph's create_react_agent."""
    llm = create_llm()
    return create_react_agent(
        llm,
        tools=location_tools,
        prompt=LOCATION_SYSTEM_PROMPT,
    )


def create_order_agent():
    """Create the order agent using LangGraph's create_react_agent."""
    llm = create_llm()
    # Lower temperature for more focused behavior
    llm.temperature = 0.5
    return create_react_agent(
        llm,
        tools=order_tools,
        prompt=ORDER_SYSTEM_PROMPT,
    )


def create_checkout_agent():
    """Create the checkout agent using LangGraph's create_react_agent."""
    llm = create_llm()
    # Use a lower temperature for checkout to be more deterministic
    llm.temperature = 0.3
    return create_react_agent(
        llm,
        tools=checkout_tools,
        prompt=CHECKOUT_SYSTEM_PROMPT,
    )


# Create the agents
greeting_agent = create_greeting_agent()
location_agent = create_location_agent()
order_agent = create_order_agent()
checkout_agent = create_checkout_agent()


def extract_handoff(content: str) -> str | None:
    """Extract handoff target from message content."""
    if "[HANDOFF:location]" in content:
        return "location"
    elif "[HANDOFF:order]" in content:
        return "order"
    elif "[HANDOFF:checkout]" in content:
        return "checkout"
    elif "[HANDOFF:end]" in content:
        return "end"
    return None


def clean_handoff_tag(content: str) -> str:
    """Remove handoff tags from content."""
    for tag in ["[HANDOFF:location]", "[HANDOFF:order]", "[HANDOFF:checkout]", "[HANDOFF:end]"]:
        content = content.replace(tag, "").strip()
    return content


def call_greeting_agent(state: AgentState) -> dict:
    """Call the greeting agent."""
    log_agent_response("greeting", ">>> ENTERING GREETING AGENT <<<")

    # Invoke the ReAct agent
    result = greeting_agent.invoke({"messages": state["messages"]})

    messages = result.get("messages", [])
    log_agent_response("greeting", str(messages[-1].content) if messages else "")

    # Check for handoff
    updates = {"messages": messages}
    if messages:
        last_content = str(messages[-1].content)
        handoff = extract_handoff(last_content)
        if handoff:
            updates["current_agent"] = handoff
            # Clean the handoff tag from the message
            if hasattr(messages[-1], "content"):
                messages[-1] = AIMessage(content=clean_handoff_tag(last_content))
            updates["messages"] = messages
            log_state_transition("greeting", handoff, "handoff_detected")

            # Set handoff summary based on target
            if handoff == "location":
                updates["handoff_summary_ar"] = "عميل جديد يبي يطلب أكل"

            # Log context transfer with token estimation
            log_handoff_context("greeting", handoff, messages, {
                "intent": "delivery_order",
                "handoff_summary_ar": updates.get("handoff_summary_ar", "")
            })

    return updates


def call_location_agent(state: AgentState) -> dict:
    """Call the location agent."""
    log_agent_response("location", ">>> ENTERING LOCATION AGENT <<<")

    # Add context to messages
    context_msg = SystemMessage(content=f"[معلومات: {state.get('handoff_summary_ar', '')}]")
    messages_with_context = [context_msg] + state["messages"]

    # Invoke the ReAct agent
    result = location_agent.invoke({"messages": messages_with_context})

    messages = result.get("messages", [])
    # Filter out the context message we added
    messages = [m for m in messages if not (isinstance(m, SystemMessage) and "[معلومات:" in str(m.content))]

    log_agent_response("location", str(messages[-1].content) if messages else "")

    updates = {"messages": messages}

    # Extract order type info from set_order_type tool result
    # This is the authoritative source - the AI decides based on conversation
    for msg in messages:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            import json
            try:
                data = json.loads(msg.content)
                if isinstance(data, dict):
                    # Check for set_order_type result
                    if data.get("success") and "order_type" in data:
                        updates["order_type"] = data["order_type"]
                        updates["district"] = data.get("district", "")
                        updates["delivery_fee"] = data.get("delivery_fee", 0.0)
                        if data["order_type"] == "delivery":
                            updates["district_validated"] = True
                    # Also check for check_delivery_district result (for delivery_fee/time)
                    elif data.get("covered"):
                        updates["estimated_time"] = data.get("estimated_time", "")
            except:
                pass

    # Fallback: get from stored order type info if tool was called
    if "order_type" not in updates:
        stored_info = get_order_type_info()
        if stored_info.get("order_type") != "delivery" or stored_info.get("district"):
            updates["order_type"] = stored_info.get("order_type", "delivery")
            updates["district"] = stored_info.get("district", "")
            updates["delivery_fee"] = stored_info.get("delivery_fee", 0.0)

    # Check for handoff
    if messages:
        last_content = str(messages[-1].content)
        handoff = extract_handoff(last_content)
        if handoff:
            # Override handoff target based on where user came from
            came_from_checkout = state.get("came_from_checkout", False)

            # If user came from checkout and is going to "order", redirect to checkout instead
            if handoff == "order" and came_from_checkout:
                handoff = "checkout"
                # Clean the tag and replace with correct one
                last_content = last_content.replace("[HANDOFF:order]", "")
            # If user came from order (not checkout), ensure they go to order
            elif handoff == "checkout" and not came_from_checkout:
                handoff = "order"
                last_content = last_content.replace("[HANDOFF:checkout]", "")

            updates["current_agent"] = handoff
            messages[-1] = AIMessage(content=clean_handoff_tag(last_content))
            updates["messages"] = messages
            log_state_transition("location", handoff, "handoff_detected")

            # Clear the came_from flags after using them
            updates["came_from_checkout"] = False
            updates["came_from_order"] = False

            order_type = updates.get("order_type", state.get("order_type", "delivery"))

            # Set handoff summary based on target
            if handoff == "order":
                if order_type == "pickup":
                    updates["handoff_summary_ar"] = "العميل يبي استلام من الفرع، جاهز يختار أكله"
                else:
                    updates["handoff_summary_ar"] = f"العميل من {updates.get('district', state.get('district', 'غير محدد'))}، رسوم التوصيل {updates.get('delivery_fee', state.get('delivery_fee', 0))} ريال"
            elif handoff == "checkout":
                # Returning to checkout after location change
                if order_type == "pickup":
                    updates["handoff_summary_ar"] = "العميل غيّر لاستلام من الفرع"
                else:
                    updates["handoff_summary_ar"] = f"العميل غيّر الموقع إلى {updates.get('district', state.get('district', 'غير محدد'))}"

            # Log context transfer with token estimation
            log_handoff_context("location", handoff, messages, {
                "order_type": order_type,
                "district": updates.get("district", state.get("district", "")),
                "delivery_fee": updates.get("delivery_fee", state.get("delivery_fee", 0)),
                "handoff_summary_ar": updates.get("handoff_summary_ar", "")
            })

    return updates


def call_order_agent(state: AgentState) -> dict:
    """Call the order agent."""
    log_agent_response("order", ">>> ENTERING ORDER AGENT <<<")

    # Add context to messages
    context_parts = []
    if state.get("handoff_summary_ar"):
        context_parts.append(state["handoff_summary_ar"])
    order_type = state.get("order_type", "delivery")
    if order_type == "pickup":
        context_parts.append("نوع الطلب: استلام من الفرع")
    elif state.get("district"):
        context_parts.append(f"التوصيل إلى: {state['district']}")

    context_msg = SystemMessage(content=f"[معلومات: {' | '.join(context_parts)}]") if context_parts else None
    messages_with_context = ([context_msg] if context_msg else []) + state["messages"]

    # Invoke the ReAct agent with recursion limit to prevent infinite tool loops
    result = order_agent.invoke(
        {"messages": messages_with_context},
        {"recursion_limit": 8}
    )

    messages = result.get("messages", [])
    # Filter out context messages
    messages = [m for m in messages if not (isinstance(m, SystemMessage) and "[معلومات:" in str(m.content))]

    log_agent_response("order", str(messages[-1].content) if messages else "")

    updates = {"messages": messages}

    # Extract order info from tool results
    for msg in messages:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            import json
            try:
                data = json.loads(msg.content)
                if isinstance(data, dict) and "current_total" in data:
                    updates["subtotal"] = data["current_total"]
            except:
                pass

    # Check for handoff
    if messages:
        last_content = str(messages[-1].content)
        handoff = extract_handoff(last_content)
        if handoff:
            updates["current_agent"] = handoff
            messages[-1] = AIMessage(content=clean_handoff_tag(last_content))
            updates["messages"] = messages
            log_state_transition("order", handoff, "handoff_detected")

            # Set handoff summary based on target
            if handoff == "checkout":
                order_type = state.get("order_type", "delivery")
                if order_type == "pickup":
                    updates["handoff_summary_ar"] = "العميل خلص الطلب، استلام من الفرع"
                else:
                    updates["handoff_summary_ar"] = f"العميل خلص الطلب، توصيل إلى {state.get('district', 'غير محدد')}"
            elif handoff == "location":
                # Backward routing - user wants to change delivery/pickup
                # Mark that user came from Order (not from Checkout)
                updates["handoff_summary_ar"] = "العميل يبي يغير الموقع (راجع من الطلبات)"
                updates["came_from_order"] = True

            # Log context transfer with token estimation
            log_handoff_context("order", handoff, messages, {
                "order_type": state.get("order_type", "delivery"),
                "district": state.get("district", ""),
                "subtotal": updates.get("subtotal", state.get("subtotal", 0)),
                "handoff_summary_ar": updates.get("handoff_summary_ar", "")
            })

    return updates


def call_checkout_agent(state: AgentState) -> dict:
    """Call the checkout agent."""
    log_agent_response("checkout", ">>> ENTERING CHECKOUT AGENT <<<")

    # Add context to messages - include order type
    order_type = state.get("order_type", "delivery")
    context_parts = [state.get("handoff_summary_ar", "")]
    context_parts.append(f"نوع الطلب: {'توصيل' if order_type == 'delivery' else 'استلام من الفرع'}")
    if order_type == "delivery" and state.get("delivery_fee"):
        context_parts.append(f"رسوم التوصيل: {state['delivery_fee']} ريال")
    else:
        context_parts.append("رسوم التوصيل: 0 (استلام)")

    context_msg = SystemMessage(content=f"[معلومات: {' | '.join(context_parts)}]")
    messages_with_context = [context_msg] + state["messages"]

    # Invoke the ReAct agent with higher recursion limit for checkout flow
    result = checkout_agent.invoke(
        {"messages": messages_with_context},
        {"recursion_limit": 15}
    )

    messages = result.get("messages", [])
    # Filter out context messages
    messages = [m for m in messages if not (isinstance(m, SystemMessage) and "[معلومات:" in str(m.content))]

    log_agent_response("checkout", str(messages[-1].content) if messages else "")

    updates = {"messages": messages}

    # Extract order confirmation from tool results
    for msg in messages:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            import json
            try:
                data = json.loads(msg.content)
                if isinstance(data, dict) and data.get("order_id"):
                    updates["order_id"] = data["order_id"]
                    updates["order_confirmed"] = True
            except:
                pass

    # Check for handoff
    if messages:
        last_content = str(messages[-1].content)
        handoff = extract_handoff(last_content)
        if handoff:
            updates["current_agent"] = handoff
            messages[-1] = AIMessage(content=clean_handoff_tag(last_content))
            updates["messages"] = messages
            log_state_transition("checkout", handoff, "handoff_detected")

            # Set handoff summary based on target (backward routing)
            if handoff == "location":
                # Mark that user came from Checkout (not from Order)
                updates["handoff_summary_ar"] = "العميل يبي يغير الموقع (راجع من المحاسبة)"
                updates["came_from_checkout"] = True
            elif handoff == "order":
                updates["handoff_summary_ar"] = "العميل يبي يعدل الطلب"

            # Log context transfer with token estimation
            log_handoff_context("checkout", handoff, messages, {
                "order_type": order_type,
                "district": state.get("district", ""),
                "delivery_fee": state.get("delivery_fee", 0),
                "handoff_summary_ar": updates.get("handoff_summary_ar", "")
            })

    return updates


def route_after_greeting(state: AgentState) -> str:
    """Route after greeting agent - only continue if there's a handoff."""
    current = state.get("current_agent", "greeting")
    if current == "location":
        return "location_node"  # New flow: greeting → location
    elif current == "end":
        return END
    # No handoff - stop and wait for next user input
    return END


def route_after_location(state: AgentState) -> str:
    """Route after location agent - only continue if there's a handoff."""
    current = state.get("current_agent", "location")
    if current == "order":
        return "order_node"  # New flow: location → order
    elif current == "checkout":
        return "checkout_node"  # Backward: returning from checkout after location change
    elif current == "end":
        return END
    # No handoff - stop and wait for next user input
    return END


def route_after_order(state: AgentState) -> str:
    """Route after order agent - only continue if there's a handoff."""
    current = state.get("current_agent", "order")
    if current == "checkout":
        return "checkout_node"  # New flow: order → checkout
    elif current == "location":
        return "location_node"  # Backward: user wants to change delivery/pickup
    elif current == "end":
        return END
    # No handoff - stop and wait for next user input
    return END


def route_after_checkout(state: AgentState) -> str:
    """Route after checkout agent - only continue if there's a handoff."""
    current = state.get("current_agent", "checkout")
    if current == "location":
        return "location_node"  # Backward: user wants to change location/delivery type
    elif current == "order":
        return "order_node"  # Backward: user wants to modify order
    elif current == "end":
        return END
    # No handoff - stop and wait for next user input
    return END


def route_by_current_agent(state: AgentState) -> str:
    """Route to the appropriate agent based on current_agent state (for initial routing)."""
    current = state.get("current_agent", "greeting")

    if current == "end":
        return END
    elif current == "location":
        return "location_node"
    elif current == "order":
        return "order_node"
    elif current == "checkout":
        return "checkout_node"
    else:
        return "greeting_node"


def create_workflow() -> StateGraph:
    """Create the LangGraph multi-agent workflow."""
    # Create the graph with our state schema
    workflow = StateGraph(AgentState)

    # Add agent nodes - each wraps a LangGraph ReAct agent
    workflow.add_node("greeting_node", call_greeting_agent)
    workflow.add_node("location_node", call_location_agent)
    workflow.add_node("order_node", call_order_agent)
    workflow.add_node("checkout_node", call_checkout_agent)

    # Set entry point - route to the current agent based on state
    workflow.add_conditional_edges(
        START,
        route_by_current_agent,
        {
            "greeting_node": "greeting_node",
            "location_node": "location_node",
            "order_node": "order_node",
            "checkout_node": "checkout_node",
            END: END,
        }
    )

    # Add conditional routing from each agent based on handoffs
    # Flow: Greeting → Location → Order → Checkout (matching PDF requirements)
    # Each agent goes to END by default (wait for next user input) unless there's a handoff
    workflow.add_conditional_edges(
        "greeting_node",
        route_after_greeting,
        {
            "location_node": "location_node",  # New flow: greeting → location
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "location_node",
        route_after_location,
        {
            "order_node": "order_node",  # New flow: location → order
            "checkout_node": "checkout_node",  # Backward: return to checkout after location change
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "order_node",
        route_after_order,
        {
            "checkout_node": "checkout_node",  # New flow: order → checkout
            "location_node": "location_node",  # Backward: change delivery/pickup
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "checkout_node",
        route_after_checkout,
        {
            "location_node": "location_node",  # Backward: change location/delivery type
            "order_node": "order_node",  # Backward: modify order
            END: END,
        }
    )

    # Compile the graph
    return workflow.compile()


# Create the compiled graph
graph = create_workflow()
