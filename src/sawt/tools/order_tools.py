"""Order management tools for the ordering agent."""

from langchain_core.tools import tool

from sawt.logging_config import log_tool_call, log_tool_result
from sawt.tools.menu_tools import get_menu_cache


# Session-based order storage (in production, use database)
_orders: dict[str, list[dict]] = {}


def get_session_order(session_id: str) -> list[dict]:
    """Get order items for a session."""
    return _orders.get(session_id, [])


def set_session_order(session_id: str, items: list[dict]) -> None:
    """Set order items for a session."""
    _orders[session_id] = items


def clear_session_order(session_id: str) -> None:
    """Clear order for a session."""
    _orders.pop(session_id, None)


@tool
def add_to_order(item_id: str, quantity: int = 1, notes: str = "", session_id: str = "default") -> dict:
    """
    Add an item to the current order.

    Args:
        item_id: The menu item ID to add
        quantity: Number of items to add (default: 1)
        notes: Special instructions (e.g., "بدون بصل", "حار زيادة")
        session_id: Session identifier

    Returns:
        Dictionary with:
        - success: bool
        - order_item: The added item details
        - current_total: Updated order subtotal
        - message_ar: Confirmation message in Arabic
    """
    log_tool_call("add_to_order", {"item_id": item_id, "quantity": quantity, "notes": notes})

    menu = get_menu_cache()

    if item_id not in menu:
        result = {
            "success": False,
            "message_ar": f"الصنف غير موجود: {item_id}"
        }
        log_tool_result("add_to_order", result)
        return result

    item = menu[item_id]

    if not item.get("available", True):
        result = {
            "success": False,
            "message_ar": f"للأسف {item['name_ar']} غير متوفر حالياً"
        }
        log_tool_result("add_to_order", result)
        return result

    # Create order item
    order_item = {
        "item_id": item_id,
        "name_ar": item["name_ar"],
        "name_en": item.get("name_en", ""),
        "quantity": quantity,
        "price": item["price"],
        "notes": notes,
        "line_total": item["price"] * quantity
    }

    # Add to session order
    order = get_session_order(session_id)

    # Check if same item already exists (without notes), merge quantities
    existing_idx = None
    for idx, existing in enumerate(order):
        if existing["item_id"] == item_id and existing["notes"] == notes:
            existing_idx = idx
            break

    if existing_idx is not None:
        order[existing_idx]["quantity"] += quantity
        order[existing_idx]["line_total"] = order[existing_idx]["price"] * order[existing_idx]["quantity"]
    else:
        order.append(order_item)

    set_session_order(session_id, order)

    # Calculate total
    subtotal = sum(item["line_total"] for item in order)

    result = {
        "success": True,
        "order_item": order_item,
        "current_total": subtotal,
        "item_count": sum(item["quantity"] for item in order),
        "message_ar": f"تمام! أضفت {quantity}× {item['name_ar']}" + (f" ({notes})" if notes else "") + f". المجموع: {subtotal} ريال"
    }

    log_tool_result("add_to_order", {"success": True, "subtotal": subtotal})
    return result


@tool
def get_current_order(session_id: str = "default") -> dict:
    """
    Get the current order summary.

    Args:
        session_id: Session identifier

    Returns:
        Dictionary with:
        - items: List of order items
        - subtotal: Order subtotal
        - item_count: Total number of items
        - summary_ar: Arabic summary of the order
    """
    log_tool_call("get_current_order", {"session_id": session_id})

    order = get_session_order(session_id)

    if not order:
        result = {
            "items": [],
            "subtotal": 0.0,
            "item_count": 0,
            "summary_ar": "السلة فارغة"
        }
        log_tool_result("get_current_order", result)
        return result

    subtotal = sum(item["line_total"] for item in order)
    item_count = sum(item["quantity"] for item in order)

    # Build Arabic summary
    summary_lines = []
    for item in order:
        line = f"• {item['quantity']}× {item['name_ar']} = {item['line_total']} ريال"
        if item.get("notes"):
            line += f" ({item['notes']})"
        summary_lines.append(line)

    summary_ar = "\n".join(summary_lines) + f"\n\nالمجموع: {subtotal} ريال"

    result = {
        "items": order,
        "subtotal": subtotal,
        "item_count": item_count,
        "summary_ar": summary_ar
    }

    log_tool_result("get_current_order", {"item_count": item_count, "subtotal": subtotal})
    return result


@tool
def update_order_item(item_id: str, quantity: int | None = None, notes: str | None = None, session_id: str = "default") -> dict:
    """
    Update an existing item in the order.

    Args:
        item_id: The menu item ID to update
        quantity: New quantity (None to keep current)
        notes: New notes (None to keep current)
        session_id: Session identifier

    Returns:
        Dictionary with success status and updated order info
    """
    log_tool_call("update_order_item", {"item_id": item_id, "quantity": quantity, "notes": notes})

    order = get_session_order(session_id)

    # Find the item
    item_idx = None
    for idx, item in enumerate(order):
        if item["item_id"] == item_id:
            item_idx = idx
            break

    if item_idx is None:
        result = {
            "success": False,
            "message_ar": "الصنف مو موجود في السلة"
        }
        log_tool_result("update_order_item", result)
        return result

    # Update the item
    if quantity is not None:
        if quantity <= 0:
            # Remove item
            removed = order.pop(item_idx)
            set_session_order(session_id, order)
            result = {
                "success": True,
                "action": "removed",
                "message_ar": f"شلت {removed['name_ar']} من السلة"
            }
        else:
            order[item_idx]["quantity"] = quantity
            order[item_idx]["line_total"] = order[item_idx]["price"] * quantity
            set_session_order(session_id, order)
            result = {
                "success": True,
                "action": "updated",
                "message_ar": f"تمام، صارت {quantity}× {order[item_idx]['name_ar']}"
            }

    if notes is not None:
        order[item_idx]["notes"] = notes
        set_session_order(session_id, order)
        result = {
            "success": True,
            "action": "updated",
            "message_ar": f"تمام، حدثت الملاحظات"
        }

    log_tool_result("update_order_item", result)
    return result


@tool
def remove_from_order(item_id: str, session_id: str = "default") -> dict:
    """
    Remove an item from the order.

    Args:
        item_id: The menu item ID to remove
        session_id: Session identifier

    Returns:
        Dictionary with success status
    """
    log_tool_call("remove_from_order", {"item_id": item_id})

    order = get_session_order(session_id)

    # Find and remove the item
    new_order = [item for item in order if item["item_id"] != item_id]

    if len(new_order) == len(order):
        result = {
            "success": False,
            "message_ar": "الصنف مو موجود في السلة"
        }
    else:
        set_session_order(session_id, new_order)
        subtotal = sum(item["line_total"] for item in new_order)
        result = {
            "success": True,
            "new_subtotal": subtotal,
            "message_ar": "تم حذف الصنف من السلة"
        }

    log_tool_result("remove_from_order", result)
    return result
