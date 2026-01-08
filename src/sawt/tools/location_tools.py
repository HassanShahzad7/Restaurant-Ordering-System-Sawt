"""Location-related tools for the ordering agent."""

from typing import Literal

from langchain_core.tools import tool

from sawt.logging_config import log_tool_call, log_tool_result


# Store order type (in production, this would be in session state)
_order_type_store: dict[str, dict] = {}


def get_order_type_info(session_id: str = "default") -> dict:
    """Get stored order type info for a session."""
    return _order_type_store.get(session_id, {"order_type": "delivery", "district": "", "delivery_fee": 0.0})


def clear_order_type_info(session_id: str = "default") -> None:
    """Clear order type info for a session."""
    _order_type_store.pop(session_id, None)


# Covered districts with delivery info
COVERED_DISTRICTS = {
    "حي النرجس": {"delivery_fee": 15.0, "estimated_time": "30-45 دقيقة"},
    "النرجس": {"delivery_fee": 15.0, "estimated_time": "30-45 دقيقة"},
    "حي الياسمين": {"delivery_fee": 15.0, "estimated_time": "30-45 دقيقة"},
    "الياسمين": {"delivery_fee": 15.0, "estimated_time": "30-45 دقيقة"},
    "حي الملقا": {"delivery_fee": 15.0, "estimated_time": "35-50 دقيقة"},
    "الملقا": {"delivery_fee": 15.0, "estimated_time": "35-50 دقيقة"},
    "حي الصحافة": {"delivery_fee": 12.0, "estimated_time": "25-40 دقيقة"},
    "الصحافة": {"delivery_fee": 12.0, "estimated_time": "25-40 دقيقة"},
    "حي العقيق": {"delivery_fee": 15.0, "estimated_time": "30-45 دقيقة"},
    "العقيق": {"delivery_fee": 15.0, "estimated_time": "30-45 دقيقة"},
    "حي الورود": {"delivery_fee": 10.0, "estimated_time": "20-35 دقيقة"},
    "الورود": {"delivery_fee": 10.0, "estimated_time": "20-35 دقيقة"},
    "حي الروضة": {"delivery_fee": 12.0, "estimated_time": "25-40 دقيقة"},
    "الروضة": {"delivery_fee": 12.0, "estimated_time": "25-40 دقيقة"},
    "حي الربوة": {"delivery_fee": 12.0, "estimated_time": "25-40 دقيقة"},
    "الربوة": {"delivery_fee": 12.0, "estimated_time": "25-40 دقيقة"},
    "حي السليمانية": {"delivery_fee": 10.0, "estimated_time": "20-30 دقيقة"},
    "السليمانية": {"delivery_fee": 10.0, "estimated_time": "20-30 دقيقة"},
    "حي العليا": {"delivery_fee": 10.0, "estimated_time": "15-25 دقيقة"},
    "العليا": {"delivery_fee": 10.0, "estimated_time": "15-25 دقيقة"},
    "حي النخيل": {"delivery_fee": 15.0, "estimated_time": "30-45 دقيقة"},
    "النخيل": {"delivery_fee": 15.0, "estimated_time": "30-45 دقيقة"},
    "حي الغدير": {"delivery_fee": 15.0, "estimated_time": "35-50 دقيقة"},
    "الغدير": {"delivery_fee": 15.0, "estimated_time": "35-50 دقيقة"},
    "حي القيروان": {"delivery_fee": 18.0, "estimated_time": "40-55 دقيقة"},
    "القيروان": {"delivery_fee": 18.0, "estimated_time": "40-55 دقيقة"},
    "حي الرمال": {"delivery_fee": 18.0, "estimated_time": "40-55 دقيقة"},
    "الرمال": {"delivery_fee": 18.0, "estimated_time": "40-55 دقيقة"},
}


@tool
def check_delivery_district(district: str) -> dict:
    """
    Check if a district is covered for delivery and get delivery details.

    Args:
        district: The district/neighborhood name in Arabic (e.g., "حي النرجس")

    Returns:
        Dictionary with:
        - covered: bool - Whether delivery is available
        - delivery_fee: float - Delivery fee in SAR (0 if not covered)
        - estimated_time: str - Estimated delivery time (empty if not covered)
        - message_ar: str - Arabic message for the customer
    """
    log_tool_call("check_delivery_district", {"district": district})

    # Normalize the district name
    district_clean = district.strip()

    # Check if covered
    if district_clean in COVERED_DISTRICTS:
        info = COVERED_DISTRICTS[district_clean]
        result = {
            "covered": True,
            "delivery_fee": info["delivery_fee"],
            "estimated_time": info["estimated_time"],
            "message_ar": f"تمام! نوصل لـ{district_clean}. رسوم التوصيل {info['delivery_fee']} ريال، والوقت المتوقع {info['estimated_time']}."
        }
    else:
        # Check for partial matches
        suggestions = [d for d in COVERED_DISTRICTS.keys() if district_clean in d or d in district_clean]
        if suggestions:
            result = {
                "covered": False,
                "delivery_fee": 0.0,
                "estimated_time": "",
                "message_ar": f"ما لقيت '{district_clean}'. هل تقصد: {', '.join(suggestions[:3])}؟",
                "suggestions": suggestions[:3]
            }
        else:
            result = {
                "covered": False,
                "delivery_fee": 0.0,
                "estimated_time": "",
                "message_ar": f"للأسف ما نغطي منطقة '{district_clean}' حالياً. تبي تستلم من الفرع أو تختار منطقة ثانية؟"
            }

    log_tool_result("check_delivery_district", result)
    return result


@tool
def set_order_type(
    order_type: str,
    district: str = "",
    delivery_fee: float = 0.0,
    session_id: str = "default"
) -> dict:
    """
    Set the order type based on customer choice.

    IMPORTANT: Call this tool when:
    - Customer chooses pickup/takeaway/استلام → set order_type="pickup"
    - Customer chooses delivery/توصيل and location is confirmed → set order_type="delivery" with district and fee

    Args:
        order_type: Either "delivery" (توصيل) or "pickup" (استلام من الفرع)
        district: District name if delivery (empty for pickup)
        delivery_fee: Delivery fee if delivery (0 for pickup)
        session_id: Session identifier

    Returns:
        Confirmation of the order type setting
    """
    log_tool_call("set_order_type", {
        "order_type": order_type,
        "district": district,
        "delivery_fee": delivery_fee
    })

    # Normalize order type
    order_type_normalized = "pickup" if order_type.lower() in ["pickup", "استلام", "takeaway", "take away"] else "delivery"

    # Store the order type info
    _order_type_store[session_id] = {
        "order_type": order_type_normalized,
        "district": district if order_type_normalized == "delivery" else "استلام من الفرع - حي العليا",
        "delivery_fee": delivery_fee if order_type_normalized == "delivery" else 0.0,
    }

    if order_type_normalized == "pickup":
        result = {
            "success": True,
            "order_type": "pickup",
            "district": "استلام من الفرع - حي العليا",
            "delivery_fee": 0.0,
            "message_ar": "تمام، الطلب للاستلام من الفرع في حي العليا. لا توجد رسوم توصيل."
        }
    else:
        result = {
            "success": True,
            "order_type": "delivery",
            "district": district,
            "delivery_fee": delivery_fee,
            "message_ar": f"تمام، الطلب للتوصيل إلى {district}. رسوم التوصيل {delivery_fee} ريال."
        }

    log_tool_result("set_order_type", result)
    return result
