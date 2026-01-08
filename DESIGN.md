# Arabic Restaurant Ordering Agent - Design Document

## 1. Architecture Overview

### 1.1 Agent Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER MESSAGE                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GREETING AGENT                                       │
│  Purpose: Welcome customer, determine intent (order vs complaint)            │
│  Tools: None (pure conversation)                                             │
│  Entry: Start of conversation                                                │
│  Exit: Intent confirmed as "order" or routed to complaint handling           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    Intent = "order" │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LOCATION AGENT                                       │
│  Purpose: Collect & validate delivery address OR confirm pickup              │
│  Tools: check_delivery_district()                                            │
│  Entry: Intent confirmed as order                                            │
│  Exit: Location validated OR pickup confirmed                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
             Location valid/Pickup  │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORDER AGENT                                         │
│  Purpose: Take order items from 100+ item menu                               │
│  Tools: search_menu(), get_item_details(), add_to_order(), get_current_order()│
│  Entry: Location validated or pickup confirmed                               │
│  Exit: User confirms order is complete                                       │
│                                                                              │
│  ◄───── User says "change to delivery/pickup" ─────┐                        │
└─────────────────────────────────────────────────────│────────────────────────┘
                                    │                 │
                  Order complete    │                 │ Backtrack
                                    ▼                 │
┌─────────────────────────────────────────────────────│────────────────────────┐
│                        CHECKOUT AGENT               │                        │
│  Purpose: Summarize order, collect customer info, confirm                    │
│  Tools: calculate_total(), confirm_order()                                   │
│  Entry: Order complete                                                       │
│  Exit: Order confirmed                                                       │
│                                                                              │
│  ◄───── User says "change to delivery/pickup" ─────┘                        │
│  ◄───── User says "add more items" ────────────────► ORDER AGENT            │
└─────────────────────────────────────────────────────────────────────────────┘


BACKTRACK FLOWS (User Changes Mind):
====================================

                    ┌──────────────────────────────────────────────────────┐
                    │ User at ORDER AGENT says:                            │
                    │ "أبي أغير للتوصيل" / "أبي استلام بدال التوصيل"       │
                    │ (Change to delivery / Change to pickup)              │
                    └───────────────────────┬──────────────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────────────┐
                    │              LOCATION AGENT                          │
                    │   • Updates order_type (delivery ↔ pickup)           │
                    │   • Validates new district if delivery               │
                    │   • Removes/adds delivery fee                        │
                    └───────────────────────┬──────────────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────────────┐
                    │              ORDER AGENT (return)                    │
                    │   • Continues taking order with updated location     │
                    └──────────────────────────────────────────────────────┘


                    ┌──────────────────────────────────────────────────────┐
                    │ User at CHECKOUT AGENT says:                         │
                    │ "أبي أغير للتوصيل" / "أبي استلام"                    │
                    │ (Change to delivery / Change to pickup)              │
                    └───────────────────────┬──────────────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────────────┐
                    │              LOCATION AGENT                          │
                    │   • Updates order_type (delivery ↔ pickup)           │
                    │   • Validates new district if delivery               │
                    │   • Sets came_from_checkout = true (state flag)      │
                    └───────────────────────┬──────────────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────────────┐
                    │              CHECKOUT AGENT (return)                 │
                    │   • Recalculates totals with new delivery fee        │
                    │   • Continues checkout process                       │
                    └──────────────────────────────────────────────────────┘


                    ┌──────────────────────────────────────────────────────┐
                    │ User at CHECKOUT AGENT says:                         │
                    │ "أبي أضيف شي ثاني" / "أبي أعدل الطلب"                │
                    │ (Add more items / Modify order)                      │
                    └───────────────────────┬──────────────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────────────┐
                    │              ORDER AGENT                             │
                    │   • User adds/modifies items                         │
                    │   • Sets came_from_checkout = true (state flag)      │
                    └───────────────────────┬──────────────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────────────┐
                    │              CHECKOUT AGENT (return)                 │
                    │   • Shows updated order summary                      │
                    │   • Continues checkout process                       │
                    └──────────────────────────────────────────────────────┘
```

### 1.2 Handoff Triggers

| From Agent | To Agent | Trigger Condition | State Flags |
|------------|----------|-------------------|-------------|
| Greeting | Location | User confirms intent to place order `[HANDOFF:location]` | - |
| Greeting | End | User indicates complaint (routes to human support) | - |
| Location | Order | District validated OR pickup confirmed `[HANDOFF:order]` | - |
| Location | Checkout | Returning from backtrack with `came_from_checkout=true` | Reset flag |
| Order | Checkout | User says "خلاص", "بس كذا", "تمام" `[HANDOFF:checkout]` | - |
| Order | Location | User wants to change delivery/pickup `[HANDOFF:location]` | `came_from_order=true` |
| Order | Order | User adds/modifies items (stays in state) | - |
| Checkout | Order | User wants to add/modify items `[HANDOFF:order]` | `came_from_checkout=true` |
| Checkout | Location | User wants to change delivery/pickup `[HANDOFF:location]` | `came_from_checkout=true` |
| Checkout | End | User confirms order `[HANDOFF:end]` | `order_confirmed=true` |

#### State Flags for Backtrack Routing

| Flag | Purpose | Set By | Used By |
|------|---------|--------|---------|
| `came_from_checkout` | Track if user came from checkout (to return there) | Order Agent, Checkout Agent | Location Agent routing |
| `came_from_order` | Track if user came from order (to return there) | Order Agent | Location Agent routing |

**Smart Routing Logic in Location Agent:**
```python
# When Location Agent completes:
if came_from_checkout:
    return to Checkout  # Skip Order, go back to Checkout
elif came_from_order:
    return to Order     # Go back to Order to continue ordering
else:
    return to Order     # Normal flow: first time through
```

### 1.3 Data/Context Transfer Between Agents

#### Greeting → Location
```json
{
  "customer_name": "أحمد",          // If provided early
  "intent": "delivery_order",
  "summary_ar": "العميل يريد طلب توصيل"
}
```

#### Location → Order
```json
{
  "customer_name": "أحمد",
  "district": "حي النرجس",
  "delivery_fee": 15.0,
  "estimated_time": "30-45 دقيقة",
  "summary_ar": "العميل من حي النرجس، رسوم التوصيل 15 ريال"
}
```
**NOT transferred**: Full address validation logs, coverage check internals

#### Order → Checkout
```json
{
  "customer_name": "أحمد",
  "district": "حي النرجس",
  "delivery_fee": 15.0,
  "order_items": [
    {"id": "burger_001", "name_ar": "برجر لحم", "qty": 2, "price": 28.0}
  ],
  "subtotal": 56.0,
  "summary_ar": "طلب 2 برجر لحم من حي النرجس"
}
```
**NOT transferred**: Menu search results, item browsing history

---

## 2. Context Management Strategy

### 2.1 Message Roles

| Content Type | Role | Reasoning |
|--------------|------|-----------|
| Agent personality & rules | `system` | Core behavior that shouldn't be overridden |
| Agent procedures/instructions | `system` | Ensures consistent following of workflow |
| Menu data | **NOT in prompt** | Retrieved via tools from Vector DB |
| Menu search results | `function` (tool result) | Short-lived, only when needed |
| Conversation history | `user`/`assistant` | Natural conversation flow |
| Handoff summary | `system` | Gives agent context without full history |
| Current order state | `system` (injected) | Agent needs to know cart contents |

### 2.2 Context Budget Analysis

**Token Estimates:**
- System instructions per agent: ~300-500 tokens
- Conversation history (6 messages): ~400-600 tokens
- Handoff summary: ~100-150 tokens
- Current order state: ~50-200 tokens
- **Total per turn: ~850-1,450 tokens**

**Menu Handling (Critical Decision):**
- 100 items × ~50 tokens/item = **5,000 tokens** if loaded entirely
- This would cause:
  - High TTFT (Time to First Token)
  - Expensive API calls
  - Context pollution

**Our Strategy: Vector Search Only**
- Menu stored in Pinecone (vector database)
- Agent calls `search_menu(query)` tool
- Returns only 5-10 relevant items (~200-400 tokens)
- Never load full menu into context

### 2.3 Handoff Context Design

#### What MUST Transfer
- `session_id` - Session continuity
- `customer_name` - If collected
- `intent` - Order vs complaint
- `district` / `delivery_fee` - After location validation
- `order_items` - Current cart
- `summary_ar` - Compact Arabic summary

#### What SHOULD Transfer
- `customer_phone` - If provided early
- `special_requests` - Dietary restrictions, preferences
- `estimated_time` - Delivery ETA

#### What Should NOT Transfer
- Previous agent's system prompt
- Full conversation history (summarize instead)
- Tool call logs and intermediate results
- Menu search results from previous turns
- Internal validation details

### 2.4 History Handling

When Agent B receives handoff from Agent A:

| Question | Answer |
|----------|--------|
| Does B see A's full conversation? | **No** - Only receives summary |
| Does B see A's system prompt? | **No** - Each agent has own prompt |
| How do you summarize? | LLM generates 1-2 sentence Arabic summary |
| Max history transferred | Last 4 messages + summary |

**Why not transfer entire chat?**
1. **Token bloat**: 20 messages × 50 tokens = 1,000 wasted tokens
2. **Confusion**: Agent B might reference Agent A's behavior
3. **Privacy**: Customer doesn't expect full history passed around
4. **Latency**: More tokens = slower TTFT

---

## 3. LLM Selection

### 3.1 Model Choice: OpenRouter → GPT-5-mini

**Why GPT-5-mini:**

| Criteria | GPT-5-mini | Notes |
|----------|------------|-------|
| Arabic capabilities | ✅✅ Excellent | Superior Gulf dialect understanding |
| Function calling | ✅✅ Native support | Reliable structured output, improved over 4o-mini |
| Latency | ✅ Fast | ~400-600ms TTFT |
| Cost | ✅ Very low | Free tier available via OpenRouter |
| Context window | 128K | More than enough |
| Reasoning | ✅✅ Improved | Better multi-step task handling |

### 3.2 Model Comparison

| Model | Arabic Quality | Tool Calling | Latency | Cost (per 1M tokens) | Verdict |
|-------|---------------|--------------|---------|---------------------|---------|
| **GPT-5-mini** | ✅✅ Excellent | ✅✅ Native | ~500ms | Free tier | **Selected** - Best balance |
| GPT-4o-mini | ✅ Good | ✅ Native | ~500ms | $0.15 input | Previous gen, still capable |
| GPT-4o | ✅✅ Excellent | ✅✅ Native | ~800ms | $2.50 input | Overkill for ordering tasks |
| Claude 3.5 Sonnet | ✅✅ Excellent | ✅✅ Native | ~600ms | $3.00 input | Great but expensive |
| Claude 3 Haiku | ✅ Good | ✅ Native | ~300ms | $0.25 input | Fastest, decent Arabic |
| Gemini 1.5 Flash | ✅ Good | ✅ Native | ~400ms | $0.075 input | Cheapest, good alternative |
| Gemini 1.5 Pro | ✅✅ Excellent | ✅✅ Native | ~700ms | $1.25 input | Great Arabic, higher cost |
| Llama 3.2 | ⚠️ Fair | ⚠️ Limited | ~300ms | Free (self-host) | Weaker Arabic dialect support |
| Mistral Large | ✅ Good | ✅ Native | ~500ms | $2.00 input | Good but pricier |

### 3.3 Why GPT-5-mini Over Alternatives

1. **Arabic Dialect Handling**: GPT-5-mini shows improved understanding of Saudi/Gulf Arabic colloquialisms ("أبي", "وش عندكم", "خلاص") compared to previous models.

2. **Cost Efficiency**: Free tier on OpenRouter makes it ideal for development and demo purposes without budget constraints.

3. **Tool Reliability**: Native function calling with high accuracy for our 10 MCP tools (menu search, cart operations, checkout).

4. **Response Quality**: Maintains conversational tone in Saudi dialect while accurately executing tool calls.

**Trade-offs Accepted:**
- Slightly slower than Claude 3 Haiku (~500ms vs ~300ms)
- Less powerful than GPT-4o for complex reasoning (not needed for ordering)
- Requires OpenRouter API wrapper (minimal overhead)

### 3.4 Arabic-Specific Considerations

- Use **Saudi dialect** (Gulf Arabic) for natural conversation
- Support **Arabic numerals** (٠-٩) in input
- Store all data with **English numerals** internally
- Model handles **right-to-left** text natively

---

## 4. Edge Case Handling

### 4.1 User Changes Mind Mid-Order (Backtrack Routing)

**Scenario 1**: At Order Agent - "بدل التوصيل، أبي استلام" (Actually, pickup instead)

**Handling**:
1. Order Agent detects intent change via LLM
2. Sets `came_from_order=true` state flag
3. Triggers handoff to Location Agent `[HANDOFF:location]`
4. Location Agent confirms pickup, removes delivery fee
5. Location Agent sees `came_from_order=true`, routes back to Order Agent
6. User continues ordering

**Scenario 2**: At Checkout Agent - "أبي أغير للتوصيل" (I want delivery instead)

**Handling**:
1. Checkout Agent detects intent change
2. Sets `came_from_checkout=true` state flag
3. Triggers handoff to Location Agent `[HANDOFF:location]`
4. Location Agent collects district, validates coverage, sets delivery fee
5. Location Agent sees `came_from_checkout=true`, routes back to Checkout
6. Checkout recalculates totals with new delivery fee

**Scenario 3**: At Checkout Agent - "أبي أضيف شي" (I want to add something)

**Handling**:
1. Checkout Agent sets `came_from_checkout=true`
2. Triggers handoff to Order Agent `[HANDOFF:order]`
3. User adds items
4. Order Agent routes back to Checkout
5. Checkout shows updated summary

```python
# State flags ensure smart routing
state["came_from_checkout"] = True  # or came_from_order
# Location Agent checks flags to determine return destination
```

### 4.2 Item Not on Menu

**Scenario**: "عندكم بيتزا؟" (Do you have pizza?)

**Handling**:
1. `search_menu("بيتزا")` returns empty or low-score results
2. Agent responds: "للأسف ما عندنا بيتزا، لكن عندنا [similar items]. تبي تشوفهم؟"
3. Suggests alternatives from same/similar category
4. Never adds non-existent items to cart

### 4.3 Modify Previous Order Item

**Scenario**: "خلّها 3 بدال 2" (Make it 3 instead of 2)

**Handling**:
1. Agent calls `get_current_order()` to see cart
2. Identifies most recent or referenced item
3. Calls `update_order_item(item_id, quantity=3)`
4. Confirms: "تمام، صارت 3 برجر لحم بدال 2"

```python
# Tool: update_order_item
def update_order_item(item_id: str, quantity: int = None, notes: str = None):
    """Update quantity or notes for existing order item"""
```

### 4.4 Uncovered Delivery Location

**Scenario**: "أنا في الدرعية القديمة" (I'm in old Diriyah)

**Handling**:
1. `check_delivery_district("الدرعية القديمة")` returns `covered=false`
2. Agent responds: "للأسف ما نوصل للدرعية القديمة حالياً. تقدر تستلم من فرعنا أو تختار منطقة ثانية؟"
3. Offers:
   - Pickup option
   - List of nearby covered areas
4. Does NOT proceed to Order Agent until resolved

---

## 5. Technical Architecture

### 5.1 Framework Choice: LangGraph

**Why LangGraph:**
1. **State Machine Native**: Perfect for Greeting → Location → Order → Checkout flow
2. **Flexible LLM**: Works with OpenRouter via LangChain
3. **Tool Integration**: First-class function calling support
4. **Handoff Control**: Explicit edge definitions between agents
5. **Persistence**: Built-in state checkpointing

### 5.2 Storage Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │     │    Pinecone     │
│  (Source of     │     │  (Semantic      │
│   Truth)        │     │   Search)       │
├─────────────────┤     ├─────────────────┤
│ • Menu items    │────▶│ • Menu vectors  │
│ • Orders        │     │ • Category      │
│ • Sessions      │     │   metadata      │
│ • Coverage      │     │ • Price filters │
│ • Promo codes   │     └─────────────────┘
└─────────────────┘
         │
         ▼
   Authoritative data
   for transactions
```

**Why Both?**
- **PostgreSQL**: ACID transactions, price accuracy, order persistence
- **Pinecone**: "What burgers do you have?" → semantic search
- Menu indexed to Pinecone on insert/update
- All reads for ordering go through Pinecone first
- PostgreSQL validates final order (prices, availability)

### 5.3 Logging Format

```
[2025-01-08 14:23:01] AGENT: greeting
[2025-01-08 14:23:01] USER: السلام عليكم
[2025-01-08 14:23:02] ASSISTANT: هلا والله! أهلاً وسهلاً. تبي تطلب؟
[2025-01-08 14:23:05] USER: أيوه، أبي طلب توصيل
[2025-01-08 14:23:06] HANDOFF: greeting → location
[2025-01-08 14:23:06] CONTEXT: {intent: "delivery_order", tokens: 156}
[2025-01-08 14:23:06] MEMORY: {customer_intent: "delivery_order"}
[2025-01-08 14:23:10] USER: أنا في حي النرجس
[2025-01-08 14:23:10] TOOL_CALL: check_delivery_district({"district": "حي النرجس"})
[2025-01-08 14:23:11] TOOL_RESULT: {covered: true, delivery_fee: 15, estimated_time: "30-45 min"}
[2025-01-08 14:23:12] HANDOFF: location → order
[2025-01-08 14:23:12] CONTEXT: {district: "حي النرجس", delivery_fee: 15, tokens: 203}
[2025-01-08 14:23:15] USER: وش عندكم برجر؟
[2025-01-08 14:23:15] TOOL_CALL: search_menu({"query": "برجر", "category": null})
[2025-01-08 14:23:16] TOOL_RESULT: [5 items returned, 187 tokens]
```

---

## 6. Token Budget Summary

| Component | Tokens | Notes |
|-----------|--------|-------|
| System prompt | 400 | Agent instructions |
| Handoff context | 150 | Summary + state |
| Conversation (4 msgs) | 300 | Recent history |
| Tool results | 200 | Search results |
| **Total per turn** | **~1,050** | Well under limits |
| Menu (if loaded) | 5,000+ | ❌ Never do this |

**TTFT Impact:**
- With vector search: ~500-800ms
- With full menu: ~2-3 seconds
- **We choose vector search** for responsive UX

---

## 7. Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent Framework | LangGraph | State machine + LLM flexibility |
| LLM | GPT-5-mini via OpenRouter | Best Arabic dialect + tools + free tier |
| Menu Storage | Pinecone + PostgreSQL | Semantic search + ACID |
| Menu in Context | Never full, always search | TTFT + tokens |
| History Transfer | Summary only (4 msgs max) | Clean handoffs |
| Message Roles | System for instructions, never menu | Predictable behavior |
| Backtrack Routing | State flags (`came_from_checkout`, `came_from_order`) | Smart return routing |
