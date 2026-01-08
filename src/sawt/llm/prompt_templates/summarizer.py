"""Summarizer agent prompt template."""

SUMMARIZER_SYSTEM_PROMPT = """أنت كاتب ملخصات في مطعم سعودي.

## مهمتك:
اكتب ملخص مختصر ومفيد للمحادثة بالعربي يشمل:
- نية العميل (طلب/شكوى/استفسار)
- نوع الطلب (توصيل/استلام)
- العنوان (إن وجد)
- الأصناف المطلوبة
- أي تفضيلات أو ملاحظات

## المحادثة:
{conversation}

## قواعد:
- اكتب بشكل مختصر ومنظم
- لا تضف معلومات غير موجودة
- ركز على المعلومات المهمة فقط
- استخدم نقاط للوضوح

## صيغة الرد:
اكتب الملخص مباشرة بدون JSON"""


CONFIRMATION_MESSAGE_TEMPLATE = """✅ تم تأكيد طلبك!

📋 رقم الطلب: {order_number}

{order_summary}

📍 العنوان: {address}
👤 الاسم: {customer_name}
📱 الجوال: {customer_phone}

💰 الدفع عند الاستلام

شكراً لك! سيصلك الطلب خلال 30-45 دقيقة تقريباً."""


def get_summarizer_prompt(conversation: str) -> str:
    """Get the summarizer system prompt with conversation."""
    return SUMMARIZER_SYSTEM_PROMPT.format(conversation=conversation)


def get_confirmation_message(
    order_number: str,
    order_summary: str,
    address: str,
    customer_name: str,
    customer_phone: str,
) -> str:
    """Get the order confirmation message."""
    return CONFIRMATION_MESSAGE_TEMPLATE.format(
        order_number=order_number,
        order_summary=order_summary,
        address=address if address else "استلام من الفرع",
        customer_name=customer_name,
        customer_phone=customer_phone,
    )
