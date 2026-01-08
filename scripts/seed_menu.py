"""Seed script for menu items and modifiers - 100+ items."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sawt.db.connection import init_db, close_db, get_transaction


# ============================================================================
# MENU ITEMS - 100+ items across categories
# ============================================================================

MENU_ITEMS = [
    # ========================================================================
    # MAIN DISHES - BURGERS (15 items)
    # ========================================================================
    {
        "name_ar": "برجر لحم كلاسيك",
        "name_en": "Classic Beef Burger",
        "description_ar": "برجر لحم بقري طازج مع خس وطماطم وبصل ومايونيز",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 28.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر دجاج مقرمش",
        "name_en": "Crispy Chicken Burger",
        "description_ar": "صدر دجاج مقرمش مع صوص خاص وخس",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 25.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر دبل تشيز",
        "name_en": "Double Cheese Burger",
        "description_ar": "قطعتين لحم مع جبنة شيدر مزدوجة",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 38.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر حار",
        "name_en": "Spicy Burger",
        "description_ar": "برجر لحم مع صوص حار وهالبينو",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 30.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر مشروم",
        "name_en": "Mushroom Burger",
        "description_ar": "برجر لحم مع مشروم مقلي وصوص كريمي",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 32.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر باربيكيو",
        "name_en": "BBQ Burger",
        "description_ar": "برجر لحم مع صوص باربيكيو وبصل مكرمل",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 33.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر بيكون",
        "name_en": "Bacon Burger",
        "description_ar": "برجر لحم مع شرائح بيكون مقرمشة وجبنة",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 35.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر تريبل",
        "name_en": "Triple Burger",
        "description_ar": "ثلاث قطع لحم مع جبنة وصوص خاص",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 45.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر دجاج حار",
        "name_en": "Spicy Chicken Burger",
        "description_ar": "صدر دجاج مقرمش مع صوص حار ومخلل",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 27.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر واجيو",
        "name_en": "Wagyu Burger",
        "description_ar": "برجر لحم واجيو فاخر مع جبنة جودا",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 55.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر أنجوس",
        "name_en": "Angus Burger",
        "description_ar": "برجر لحم أنجوس مع خضار طازجة",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 42.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر سمك",
        "name_en": "Fish Burger",
        "description_ar": "فيليه سمك مقرمش مع صوص ترتار",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 28.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر جمبري",
        "name_en": "Shrimp Burger",
        "description_ar": "جمبري مقرمش مع صوص كوكتيل",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 35.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر نباتي",
        "name_en": "Veggie Burger",
        "description_ar": "برجر خضار مع فطر وجبنة",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 24.00,
        "is_combo": False,
    },
    {
        "name_ar": "برجر فلافل",
        "name_en": "Falafel Burger",
        "description_ar": "أقراص فلافل مقرمشة مع طحينة وخضار",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 22.00,
        "is_combo": False,
    },

    # ========================================================================
    # MAIN DISHES - SANDWICHES & WRAPS (10 items)
    # ========================================================================
    {
        "name_ar": "شاورما لحم",
        "name_en": "Beef Shawarma",
        "description_ar": "شاورما لحم بتتبيلة خاصة مع طحينة وبقدونس",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "شاورما دجاج",
        "name_en": "Chicken Shawarma",
        "description_ar": "شاورما دجاج مع ثوم ومخلل",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "ساندويش كلوب",
        "name_en": "Club Sandwich",
        "description_ar": "خبز توست مع دجاج وبيكون وبيض ومايونيز",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 30.00,
        "is_combo": False,
    },
    {
        "name_ar": "راب دجاج",
        "name_en": "Chicken Wrap",
        "description_ar": "خبز تورتيلا مع دجاج مشوي وخضار",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 22.00,
        "is_combo": False,
    },
    {
        "name_ar": "راب فلافل",
        "name_en": "Falafel Wrap",
        "description_ar": "خبز تورتيلا مع فلافل وخضار وطحينة",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "ساندويش ستيك",
        "name_en": "Steak Sandwich",
        "description_ar": "شرائح ستيك مع جبنة وفطر وصوص",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 38.00,
        "is_combo": False,
    },
    {
        "name_ar": "ساندويش تونة",
        "name_en": "Tuna Sandwich",
        "description_ar": "تونة طازجة مع مايونيز وخضار",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 20.00,
        "is_combo": False,
    },
    {
        "name_ar": "فيلي تشيز ستيك",
        "name_en": "Philly Cheesesteak",
        "description_ar": "لحم مشوي مع جبنة مذابة وفلفل وبصل",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 35.00,
        "is_combo": False,
    },
    {
        "name_ar": "هوت دوج كلاسيك",
        "name_en": "Classic Hot Dog",
        "description_ar": "سجق مع خردل وكاتشب",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "هوت دوج تشيز",
        "name_en": "Cheese Hot Dog",
        "description_ar": "سجق مع جبنة مذابة وبصل مقلي",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 18.00,
        "is_combo": False,
    },

    # ========================================================================
    # MAIN DISHES - RICE & GRILLED (10 items)
    # ========================================================================
    {
        "name_ar": "كبسة دجاج",
        "name_en": "Chicken Kabsa",
        "description_ar": "أرز كبسة مع دجاج متبل ومكسرات",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 35.00,
        "is_combo": False,
    },
    {
        "name_ar": "كبسة لحم",
        "name_en": "Lamb Kabsa",
        "description_ar": "أرز كبسة مع لحم ضأن طري ومكسرات",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 45.00,
        "is_combo": False,
    },
    {
        "name_ar": "مندي دجاج",
        "name_en": "Chicken Mandi",
        "description_ar": "دجاج مدخن مع أرز مندي وصوص حار",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 38.00,
        "is_combo": False,
    },
    {
        "name_ar": "مندي لحم",
        "name_en": "Lamb Mandi",
        "description_ar": "لحم ضأن مدخن مع أرز مندي",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 55.00,
        "is_combo": False,
    },
    {
        "name_ar": "مشاوي مشكلة",
        "name_en": "Mixed Grill",
        "description_ar": "تشكيلة مشاوي مع كباب وشيش طاووق وريش",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 65.00,
        "is_combo": False,
    },
    {
        "name_ar": "شيش طاووق",
        "name_en": "Shish Tawook",
        "description_ar": "أسياخ دجاج مشوية مع صوص ثوم",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 32.00,
        "is_combo": False,
    },
    {
        "name_ar": "كباب لحم",
        "name_en": "Lamb Kebab",
        "description_ar": "أسياخ كباب لحم مع بصل وطماطم مشوية",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 38.00,
        "is_combo": False,
    },
    {
        "name_ar": "ستيك تندرلوين",
        "name_en": "Tenderloin Steak",
        "description_ar": "قطعة ستيك تندرلوين مع صوص فطر",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 75.00,
        "is_combo": False,
    },
    {
        "name_ar": "ريش غنم",
        "name_en": "Lamb Chops",
        "description_ar": "ريش غنم مشوية مع أعشاب",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 65.00,
        "is_combo": False,
    },
    {
        "name_ar": "صيادية سمك",
        "name_en": "Fish Sayadieh",
        "description_ar": "سمك مع أرز بالبصل المحمر",
        "category_ar": "الأطباق الرئيسية",
        "category_en": "Main Dishes",
        "price": 48.00,
        "is_combo": False,
    },

    # ========================================================================
    # APPETIZERS & STARTERS (20 items)
    # ========================================================================
    {
        "name_ar": "حمص",
        "name_en": "Hummus",
        "description_ar": "حمص مهروس مع طحينة وزيت زيتون",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "متبل",
        "name_en": "Mutabbal",
        "description_ar": "باذنجان مشوي مع طحينة وثوم",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 14.00,
        "is_combo": False,
    },
    {
        "name_ar": "تبولة",
        "name_en": "Tabbouleh",
        "description_ar": "سلطة بقدونس مع برغل وطماطم وليمون",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "فتوش",
        "name_en": "Fattoush",
        "description_ar": "سلطة خضار مع خبز محمص ودبس الرمان",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 16.00,
        "is_combo": False,
    },
    {
        "name_ar": "فلافل",
        "name_en": "Falafel",
        "description_ar": "أقراص فلافل مقلية مقرمشة",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "سمبوسة لحم",
        "name_en": "Meat Samosa",
        "description_ar": "سمبوسة محشية لحم مفروم",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "سمبوسة جبن",
        "name_en": "Cheese Samosa",
        "description_ar": "سمبوسة محشية جبنة",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "سمبوسة خضار",
        "name_en": "Vegetable Samosa",
        "description_ar": "سمبوسة محشية خضار متبلة",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 10.00,
        "is_combo": False,
    },
    {
        "name_ar": "كبة مقلية",
        "name_en": "Fried Kibbeh",
        "description_ar": "كبة برغل محشية لحم مقلية",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "ورق عنب",
        "name_en": "Stuffed Grape Leaves",
        "description_ar": "ورق عنب محشي أرز",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 16.00,
        "is_combo": False,
    },
    {
        "name_ar": "لبنة",
        "name_en": "Labneh",
        "description_ar": "لبنة كريمية مع زيت زيتون ونعناع",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 10.00,
        "is_combo": False,
    },
    {
        "name_ar": "سلطة يونانية",
        "name_en": "Greek Salad",
        "description_ar": "خيار وطماطم وفيتا وزيتون",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "سلطة سيزر",
        "name_en": "Caesar Salad",
        "description_ar": "خس روماني مع صوص سيزر وخبز محمص",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 20.00,
        "is_combo": False,
    },
    {
        "name_ar": "سلطة سيزر بالدجاج",
        "name_en": "Chicken Caesar Salad",
        "description_ar": "سلطة سيزر مع صدر دجاج مشوي",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 28.00,
        "is_combo": False,
    },
    {
        "name_ar": "شوربة عدس",
        "name_en": "Lentil Soup",
        "description_ar": "شوربة عدس كريمية مع ليمون",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "شوربة دجاج",
        "name_en": "Chicken Soup",
        "description_ar": "شوربة دجاج مع خضار ونودلز",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 14.00,
        "is_combo": False,
    },
    {
        "name_ar": "شوربة طماطم",
        "name_en": "Tomato Soup",
        "description_ar": "شوربة طماطم كريمية مع ريحان",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "أجنحة دجاج حارة",
        "name_en": "Spicy Chicken Wings",
        "description_ar": "أجنحة دجاج مقلية بصوص حار",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 25.00,
        "is_combo": False,
    },
    {
        "name_ar": "أجنحة باربيكيو",
        "name_en": "BBQ Wings",
        "description_ar": "أجنحة دجاج بصوص باربيكيو",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 25.00,
        "is_combo": False,
    },
    {
        "name_ar": "موزاريلا ستيكس",
        "name_en": "Mozzarella Sticks",
        "description_ar": "أصابع جبنة موزاريلا مقلية",
        "category_ar": "المقبلات",
        "category_en": "Appetizers",
        "price": 18.00,
        "is_combo": False,
    },

    # ========================================================================
    # BEVERAGES - COLD DRINKS (12 items)
    # ========================================================================
    {
        "name_ar": "بيبسي",
        "name_en": "Pepsi",
        "description_ar": "مشروب غازي بارد",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 5.00,
        "is_combo": False,
    },
    {
        "name_ar": "سفن أب",
        "name_en": "7UP",
        "description_ar": "مشروب غازي بارد",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 5.00,
        "is_combo": False,
    },
    {
        "name_ar": "ميرندا",
        "name_en": "Mirinda",
        "description_ar": "مشروب غازي برتقال بارد",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 5.00,
        "is_combo": False,
    },
    {
        "name_ar": "كوكا كولا",
        "name_en": "Coca Cola",
        "description_ar": "مشروب غازي بارد",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 5.00,
        "is_combo": False,
    },
    {
        "name_ar": "فانتا",
        "name_en": "Fanta",
        "description_ar": "مشروب غازي برتقال بارد",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 5.00,
        "is_combo": False,
    },
    {
        "name_ar": "ماء",
        "name_en": "Water",
        "description_ar": "ماء معبأ",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 3.00,
        "is_combo": False,
    },
    {
        "name_ar": "ماء فوار",
        "name_en": "Sparkling Water",
        "description_ar": "ماء فوار معبأ",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 5.00,
        "is_combo": False,
    },
    {
        "name_ar": "شاي مثلج",
        "name_en": "Iced Tea",
        "description_ar": "شاي بارد بنكهة الليمون أو الخوخ",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 8.00,
        "is_combo": False,
    },
    {
        "name_ar": "ليمونادة",
        "name_en": "Lemonade",
        "description_ar": "عصير ليمون طازج مثلج",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 10.00,
        "is_combo": False,
    },
    {
        "name_ar": "موهيتو",
        "name_en": "Mojito",
        "description_ar": "موهيتو منعش بالنعناع والليمون",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "ريد بول",
        "name_en": "Red Bull",
        "description_ar": "مشروب طاقة",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "كودريد",
        "name_en": "Code Red",
        "description_ar": "مشروب طاقة",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 8.00,
        "is_combo": False,
    },

    # ========================================================================
    # BEVERAGES - FRESH JUICES & SMOOTHIES (12 items)
    # ========================================================================
    {
        "name_ar": "عصير برتقال",
        "name_en": "Orange Juice",
        "description_ar": "عصير برتقال طازج",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 10.00,
        "is_combo": False,
    },
    {
        "name_ar": "عصير تفاح",
        "name_en": "Apple Juice",
        "description_ar": "عصير تفاح طازج",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 10.00,
        "is_combo": False,
    },
    {
        "name_ar": "عصير مانجو",
        "name_en": "Mango Juice",
        "description_ar": "عصير مانجو طازج كثيف",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "عصير فراولة",
        "name_en": "Strawberry Juice",
        "description_ar": "عصير فراولة طازج",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "عصير رمان",
        "name_en": "Pomegranate Juice",
        "description_ar": "عصير رمان طبيعي",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 14.00,
        "is_combo": False,
    },
    {
        "name_ar": "عصير كوكتيل",
        "name_en": "Mixed Fruit Cocktail",
        "description_ar": "خليط فواكه طازجة",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "سموثي موز",
        "name_en": "Banana Smoothie",
        "description_ar": "سموثي موز مع حليب وعسل",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "سموثي توت",
        "name_en": "Berry Smoothie",
        "description_ar": "خليط توت مع زبادي",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "سموثي أفوكادو",
        "name_en": "Avocado Smoothie",
        "description_ar": "أفوكادو مع حليب وعسل",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "ميلك شيك فانيلا",
        "name_en": "Vanilla Milkshake",
        "description_ar": "ميلك شيك فانيلا كريمي",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 16.00,
        "is_combo": False,
    },
    {
        "name_ar": "ميلك شيك شوكولاتة",
        "name_en": "Chocolate Milkshake",
        "description_ar": "ميلك شيك شوكولاتة غني",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 16.00,
        "is_combo": False,
    },
    {
        "name_ar": "ميلك شيك أوريو",
        "name_en": "Oreo Milkshake",
        "description_ar": "ميلك شيك بسكويت أوريو",
        "category_ar": "المشروبات",
        "category_en": "Beverages",
        "price": 18.00,
        "is_combo": False,
    },

    # ========================================================================
    # DESSERTS (18 items)
    # ========================================================================
    {
        "name_ar": "آيس كريم فانيلا",
        "name_en": "Vanilla Ice Cream",
        "description_ar": "سكوب آيس كريم فانيلا",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 8.00,
        "is_combo": False,
    },
    {
        "name_ar": "آيس كريم شوكولاتة",
        "name_en": "Chocolate Ice Cream",
        "description_ar": "سكوب آيس كريم شوكولاتة",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 8.00,
        "is_combo": False,
    },
    {
        "name_ar": "آيس كريم فراولة",
        "name_en": "Strawberry Ice Cream",
        "description_ar": "سكوب آيس كريم فراولة",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 8.00,
        "is_combo": False,
    },
    {
        "name_ar": "سنداي شوكولاتة",
        "name_en": "Chocolate Sundae",
        "description_ar": "آيس كريم مع صوص شوكولاتة وكريمة",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "براوني بالشوكولاتة",
        "name_en": "Chocolate Brownie",
        "description_ar": "براوني شوكولاتة دافئ مع آيس كريم",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "تشيز كيك",
        "name_en": "Cheesecake",
        "description_ar": "قطعة تشيز كيك كريمية",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 20.00,
        "is_combo": False,
    },
    {
        "name_ar": "تشيز كيك توت",
        "name_en": "Berry Cheesecake",
        "description_ar": "تشيز كيك مع صوص التوت",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 22.00,
        "is_combo": False,
    },
    {
        "name_ar": "كيكة الشوكولاتة",
        "name_en": "Chocolate Cake",
        "description_ar": "قطعة كيك شوكولاتة غنية",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "تيراميسو",
        "name_en": "Tiramisu",
        "description_ar": "تيراميسو إيطالي كلاسيكي",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 22.00,
        "is_combo": False,
    },
    {
        "name_ar": "كريم بروليه",
        "name_en": "Creme Brulee",
        "description_ar": "كريم بروليه فرنسي",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 20.00,
        "is_combo": False,
    },
    {
        "name_ar": "بان كيك",
        "name_en": "Pancakes",
        "description_ar": "بان كيك مع شراب القيقب والفواكه",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 22.00,
        "is_combo": False,
    },
    {
        "name_ar": "وافل بلجيكي",
        "name_en": "Belgian Waffle",
        "description_ar": "وافل مقرمش مع كريمة وفواكه",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 25.00,
        "is_combo": False,
    },
    {
        "name_ar": "كنافة",
        "name_en": "Kunafa",
        "description_ar": "كنافة عربية بالجبن والقطر",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 25.00,
        "is_combo": False,
    },
    {
        "name_ar": "بقلاوة",
        "name_en": "Baklava",
        "description_ar": "بقلاوة بالفستق والعسل",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "أم علي",
        "name_en": "Um Ali",
        "description_ar": "أم علي دافئة مع المكسرات والزبيب",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 20.00,
        "is_combo": False,
    },
    {
        "name_ar": "لقيمات",
        "name_en": "Luqaimat",
        "description_ar": "لقيمات مقلية مع دبس التمر",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "بسبوسة",
        "name_en": "Basbousa",
        "description_ar": "بسبوسة بالسميد والقطر",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "موس شوكولاتة",
        "name_en": "Chocolate Mousse",
        "description_ar": "موس شوكولاتة خفيف",
        "category_ar": "الحلويات",
        "category_en": "Desserts",
        "price": 16.00,
        "is_combo": False,
    },

    # ========================================================================
    # SIDES (16 items)
    # ========================================================================
    {
        "name_ar": "بطاطس مقلية",
        "name_en": "French Fries",
        "description_ar": "بطاطس مقلية مقرمشة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 10.00,
        "is_combo": False,
    },
    {
        "name_ar": "بطاطس بالجبن",
        "name_en": "Cheese Fries",
        "description_ar": "بطاطس مقلية مع صوص الجبن",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 15.00,
        "is_combo": False,
    },
    {
        "name_ar": "بطاطس ودجز",
        "name_en": "Potato Wedges",
        "description_ar": "شرائح بطاطس كبيرة مقرمشة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "بطاطس حلوة",
        "name_en": "Sweet Potato Fries",
        "description_ar": "بطاطس حلوة مقلية",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 14.00,
        "is_combo": False,
    },
    {
        "name_ar": "حلقات البصل",
        "name_en": "Onion Rings",
        "description_ar": "حلقات بصل مقرمشة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "ناجتس دجاج",
        "name_en": "Chicken Nuggets",
        "description_ar": "6 قطع ناجتس دجاج مقرمشة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "ناجتس دجاج حار",
        "name_en": "Spicy Chicken Nuggets",
        "description_ar": "6 قطع ناجتس دجاج حارة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 18.00,
        "is_combo": False,
    },
    {
        "name_ar": "تشيكن تندرز",
        "name_en": "Chicken Tenders",
        "description_ar": "4 قطع صدر دجاج مقرمشة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 22.00,
        "is_combo": False,
    },
    {
        "name_ar": "ذرة مشوية",
        "name_en": "Grilled Corn",
        "description_ar": "كوز ذرة مشوي مع زبدة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 8.00,
        "is_combo": False,
    },
    {
        "name_ar": "كول سلو",
        "name_en": "Coleslaw",
        "description_ar": "سلطة ملفوف كريمية",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 8.00,
        "is_combo": False,
    },
    {
        "name_ar": "سلطة جانبية",
        "name_en": "Side Salad",
        "description_ar": "سلطة خضراء مشكلة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 10.00,
        "is_combo": False,
    },
    {
        "name_ar": "أرز أبيض",
        "name_en": "White Rice",
        "description_ar": "أرز أبيض مطبوخ",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 8.00,
        "is_combo": False,
    },
    {
        "name_ar": "أرز بالزعفران",
        "name_en": "Saffron Rice",
        "description_ar": "أرز بالزعفران والمكسرات",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "خبز ثوم",
        "name_en": "Garlic Bread",
        "description_ar": "خبز محمص بالثوم والزبدة",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 10.00,
        "is_combo": False,
    },
    {
        "name_ar": "خبز بالجبن",
        "name_en": "Cheese Bread",
        "description_ar": "خبز محمص بالجبن الذائب",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 12.00,
        "is_combo": False,
    },
    {
        "name_ar": "ماك أند تشيز",
        "name_en": "Mac and Cheese",
        "description_ar": "معكرونة بصوص الجبن الكريمي",
        "category_ar": "الجانبيات",
        "category_en": "Sides",
        "price": 15.00,
        "is_combo": False,
    },
]


# Modifier groups
MODIFIER_GROUPS = [
    {
        "name_ar": "الحجم",
        "name_en": "Size",
        "selection_type": "single",
        "min_selections": 0,
        "max_selections": 1,
        "is_required": False,
        "modifiers": [
            {"name_ar": "صغير", "name_en": "Small", "price_adjustment": -3.00},
            {"name_ar": "وسط", "name_en": "Medium", "price_adjustment": 0.00},
            {"name_ar": "كبير", "name_en": "Large", "price_adjustment": 5.00},
        ],
    },
    {
        "name_ar": "إضافات",
        "name_en": "Add-ons",
        "selection_type": "multiple",
        "min_selections": 0,
        "max_selections": 5,
        "is_required": False,
        "modifiers": [
            {"name_ar": "جبنة إضافية", "name_en": "Extra Cheese", "price_adjustment": 3.00},
            {"name_ar": "بيض", "name_en": "Egg", "price_adjustment": 4.00},
            {"name_ar": "لحم إضافي", "name_en": "Extra Patty", "price_adjustment": 8.00},
            {"name_ar": "بيكون", "name_en": "Bacon", "price_adjustment": 5.00},
            {"name_ar": "مشروم", "name_en": "Mushroom", "price_adjustment": 3.00},
            {"name_ar": "أفوكادو", "name_en": "Avocado", "price_adjustment": 5.00},
            {"name_ar": "هالبينو", "name_en": "Jalapeno", "price_adjustment": 2.00},
        ],
    },
    {
        "name_ar": "درجة الحرارة",
        "name_en": "Spice Level",
        "selection_type": "single",
        "min_selections": 0,
        "max_selections": 1,
        "is_required": False,
        "modifiers": [
            {"name_ar": "بدون حار", "name_en": "No Spice", "price_adjustment": 0.00},
            {"name_ar": "حار خفيف", "name_en": "Mild", "price_adjustment": 0.00},
            {"name_ar": "حار", "name_en": "Hot", "price_adjustment": 0.00},
            {"name_ar": "حار جداً", "name_en": "Extra Hot", "price_adjustment": 0.00},
        ],
    },
    {
        "name_ar": "الصوصات",
        "name_en": "Sauces",
        "selection_type": "multiple",
        "min_selections": 0,
        "max_selections": 3,
        "is_required": False,
        "modifiers": [
            {"name_ar": "كاتشب", "name_en": "Ketchup", "price_adjustment": 0.00},
            {"name_ar": "مايونيز", "name_en": "Mayo", "price_adjustment": 0.00},
            {"name_ar": "صوص باربيكيو", "name_en": "BBQ Sauce", "price_adjustment": 1.00},
            {"name_ar": "صوص رانش", "name_en": "Ranch", "price_adjustment": 1.00},
            {"name_ar": "صوص ثوم", "name_en": "Garlic Sauce", "price_adjustment": 1.00},
            {"name_ar": "صوص حار", "name_en": "Hot Sauce", "price_adjustment": 0.00},
        ],
    },
    {
        "name_ar": "المشروب",
        "name_en": "Drink Choice",
        "selection_type": "single",
        "min_selections": 0,
        "max_selections": 1,
        "is_required": False,
        "modifiers": [
            {"name_ar": "بيبسي", "name_en": "Pepsi", "price_adjustment": 0.00},
            {"name_ar": "سفن أب", "name_en": "7UP", "price_adjustment": 0.00},
            {"name_ar": "ميرندا", "name_en": "Mirinda", "price_adjustment": 0.00},
            {"name_ar": "ماء", "name_en": "Water", "price_adjustment": -2.00},
        ],
    },
]


async def seed_menu():
    """Seed the menu items and modifiers."""
    print(f"Seeding {len(MENU_ITEMS)} menu items...")

    await init_db()

    try:
        async with get_transaction() as conn:
            # Clear existing data
            await conn.execute("DELETE FROM item_modifier_groups")
            await conn.execute("DELETE FROM modifiers")
            await conn.execute("DELETE FROM modifier_groups")
            await conn.execute("DELETE FROM order_item_modifiers")
            await conn.execute("DELETE FROM order_items")
            await conn.execute("DELETE FROM menu_items")

            # Insert menu items
            menu_item_ids = []
            categories = {}
            for item in MENU_ITEMS:
                row = await conn.fetchrow(
                    """
                    INSERT INTO menu_items (name_ar, name_en, description_ar, category_ar, category_en, price, is_combo)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    """,
                    item["name_ar"],
                    item["name_en"],
                    item["description_ar"],
                    item["category_ar"],
                    item["category_en"],
                    item["price"],
                    item["is_combo"],
                )
                menu_item_ids.append(row["id"])
                cat = item["category_ar"]
                categories[cat] = categories.get(cat, 0) + 1

            print("\nItems by category:")
            for cat, count in categories.items():
                # Use repr() to avoid Unicode encoding issues on Windows console
                print(f"  Category: {count} items")

            # Insert modifier groups and modifiers
            modifier_group_ids = {}
            for group in MODIFIER_GROUPS:
                row = await conn.fetchrow(
                    """
                    INSERT INTO modifier_groups (name_ar, name_en, selection_type, min_selections, max_selections, is_required)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    group["name_ar"],
                    group["name_en"],
                    group["selection_type"],
                    group["min_selections"],
                    group["max_selections"],
                    group["is_required"],
                )
                group_id = row["id"]
                modifier_group_ids[group["name_en"]] = group_id

                # Insert modifiers
                for mod in group["modifiers"]:
                    await conn.execute(
                        """
                        INSERT INTO modifiers (group_id, name_ar, name_en, price_adjustment)
                        VALUES ($1, $2, $3, $4)
                        """,
                        group_id,
                        mod["name_ar"],
                        mod["name_en"],
                        mod["price_adjustment"],
                    )

            print(f"\nCreated {len(MODIFIER_GROUPS)} modifier groups")

            # Link items to modifier groups based on category
            main_dish_groups = ["Size", "Add-ons", "Spice Level", "Sauces"]
            side_groups = ["Size", "Sauces"]
            beverage_groups = ["Size"]

            for item_idx, item in enumerate(MENU_ITEMS):
                item_id = menu_item_ids[item_idx]
                cat = item["category_ar"]

                if cat == "الأطباق الرئيسية":
                    groups = main_dish_groups
                elif cat == "الجانبيات":
                    groups = side_groups
                elif cat == "المشروبات":
                    groups = beverage_groups
                else:
                    groups = []

                for group_name in groups:
                    if group_name in modifier_group_ids:
                        await conn.execute(
                            """
                            INSERT INTO item_modifier_groups (menu_item_id, modifier_group_id)
                            VALUES ($1, $2)
                            """,
                            item_id,
                            modifier_group_ids[group_name],
                        )

        print(f"\nSuccessfully seeded {len(MENU_ITEMS)} menu items and {len(MODIFIER_GROUPS)} modifier groups.")

    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(seed_menu())
