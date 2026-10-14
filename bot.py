import logging
import re
import telebot
from telebot import types

# إعداد تسجيل العمليات لمراقبة البوت
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8859832684:AAEiA9Cpa5CfWuqFu_8bKO618l_-UYXa8ps"
ADMIN_CHAT_ID = 2096371045  # حسابك الشخصي لاستقبال طلبات التحكم ومراجعتها

# 📢 رابط قناتك العامة المعتمدة
CHANNEL_LINK = "https://t.me" 

# 💳 حسابات الدفع الخاصة بك لكي تظهر للزبائن تلقائياً
CHAM_CASH_ACCOUNT = "f0a4274089552e1f6c585f0420428a6d"
SYRIATEL_CASH_ACCOUNT = "75163128"

bot = telebot.TeleBot(TOKEN)

# 💾 المخازن المؤقتة (ستعمل في ذاكرة السيرفر بكفاءة)
user_balances = {}  # لحفظ أرصدة الزبائن {user_id: balance}
pending_requests = {} # لحفظ الطلبات المعلقة بانتظار موافقتك
request_counter = 1

# دالة مساعدة لاستخراج الأرقام من رسالة الزبون للتحقق من القيمة
def extract_amount(text):
    numbers = re.findall(r'\d[\d,\.]*', text)
    if numbers:
        clean_num = "".join(numbers).replace(',', '').replace('.', '')
        try: return int(clean_num)
        except ValueError: return 0
    return 0

# ----------------- واجهة المستخدم الأساسية -----------------
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    if user_id not in user_balances:
        user_balances[user_id] = 0 # تعيين رصيد صفر للمستخدم الجديد

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton("💳 طلب شحن رصيد", callback_data="user_charge"), 
                 types.InlineKeyboardButton("💰 طلب سحب رصيد", callback_data="user_withdraw"))
    keyboard.row(types.InlineKeyboardButton("💵 استعراض رصيدي الحالي", callback_data="user_balance_check"))
    keyboard.row(types.InlineKeyboardButton("📝 إنشاء حساب إيشانسي (E-Chancy)", callback_data="user_echancy"))
    keyboard.row(types.InlineKeyboardButton("📢 دخول للقناة العامة", url=CHANNEL_LINK)) 

    welcome_text = (
        "👑 ▬▬▬▬▬ஜ۩۞۩ஜ▬▬▬▬▬ 👑\n"
        "✨ مَرحَبَاً بِكَ فِي بُوتْ **Youssef Robert** ✨\n"
        "🎲 ▬▬▬ 💎 حَظْ سَعِيدْ لِلمُلُوكْ 💎 ▬▬▬ 🎲\n\n"
        "يرجى اختيار الخدمة المطلوبة من القائمة أدناه لتلبية طلبك فوراً:"
    )
    bot.send_message(user_id, welcome_text, reply_markup=keyboard, parse_mode="Markdown")

# ----------------- معالجة خطوات الزبون واستقبال البيانات -----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("user_"))
def handle_user_clicks(call):
    chat_id = call.message.chat.id
    bot.delete_message(chat_id, call.message.message_id)
    
    if call.data == "user_balance_check":
        current_bal = user_balances.get(chat_id, 0)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="user_back_to_main"))
        bot.send_message(chat_id, f"💰 **يا ملك، رصيدك الحالي المتوفر في البوت هو:**\n\n💵 `{current_bal:,} ل.س`\n\nيمكنك استخدام هذا الرصيد لاحقاً أو طلب سحبه بالكامل للمحفظة.", reply_markup=keyboard, parse_mode="Markdown")

    elif call.data == "user_back_to_main":
        start_command(call.message)

    elif call.data == "user_charge":
        charge_text = (
            f"💳 **طلب شحن رصيد (⚠️ تنبيه: الحد الأدنى 50,000 ل.س)**\n\n"
            f"يرجى التحويل إلى أحد حساباتنا التالية أولاً:\n\n"
            f"📱 **شام كاش:**\n`{CHAM_CASH_ACCOUNT}`\n\n"
            f"📱 **سيرياتيل كاش:**\n`{SYRIATEL_CASH_ACCOUNT}`\n\n"
            f"*(اضغط على الرقم لنسخه تلقائياً)*\n\n"
            f"بعد إتمام التحويل، اكتب هنا: **المبلغ المحوّل + رقم العملية** في رسالة واحدة لتضاف إلى محفظتك في البوت:"
        )
        msg = bot.send_message(chat_id, charge_text, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_charge_input)
        
    elif call.data == "user_withdraw":
        current_bal = user_balances.get(chat_id, 0)
        withdraw_text = (
            f"💰 **طلب سحب رصيد نهائي (⚠️ الحد الأدنى 100,000 ل.س)**\n"
            f"💵 رصيدك الحالي المتاح للسحب: `{current_bal:,} ل.س`\n\n"
            f"الرجاء كتابة تفاصيل السحب (المبلغ المراد سحبه من البوت + رقم محفظتك ونوعها شام/سيرياتيل) في رسالة واحدة:"
        )
        msg = bot.send_message(chat_id, withdraw_text, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_withdraw_input)
        
    elif call.data == "user_echancy":
        msg = bot.send_message(chat_id, "📝 **إنشاء حساب إيشانسي**\n\nالرجاء كتابة الاسم الذي ترغب به باللغة الإنجليزية حصراً:")
        bot.register_next_step_handler(msg, save_and_forward_request, "إنشاء حساب إيشانسي")

def process_charge_input(message):
    amount = extract_amount(message.text)
    if amount > 0 and amount < 50000:
        msg = bot.reply_to(message, "❌ **عذراً يا ملك، لا يمكن تقديم طلب شحن بمبلغ أقل من 50,000 ل.س.**\n\nيرجى إعادة كتابة تفاصيل طلبك بمبلغ صحيح:")
        bot.register_next_step_handler(msg, process_charge_input)
    else:
        save_and_forward_request(message, "شحن رصيد", amount)

def process_withdraw_input(message):
    amount = extract_amount(message.text)
    user_id = message.chat.id
    current_bal = user_balances.get(user_id, 0)
    
    if amount > 0 and amount < 100000:
        msg = bot.reply_to(message, "❌ **عذراً يا ملك، لا يمكن تقديم طلب سحب بمبلغ أقل من 100,000 ل.س.**\n\nيرجى إعادة كتابة تفاصيل السحب بمبلغ صحيح:")
        bot.register_next_step_handler(msg, process_withdraw_input)
    elif amount > current_bal:
        msg = bot.reply_to(message, f"❌ **عذراً يا ملك، رصيدك في البوت غير كافٍ!**\nرصيدك الحالي هو `{current_bal:,} ل.س` وأنت طلبت سحب `{amount:,} ل.س`.\n\nيرجى إدخال مبلغ ضمن حدود رصيدك:")
        bot.register_next_step_handler(msg, process_withdraw_input)
    else:
        save_and_forward_request(message, "سحب رصيد", amount)

# ----------------- حفظ الطلب وإرساله للأدمن للموافقة/الرفض -----------------
def save_and_forward_request(message, request_type, amount=0):
    global request_counter
    req_id = request_counter
    request_counter += 1
    
    user_info = message.from_user
    user_details = f"👤 الاسم: {user_info.first_name}\n🆔 الأيدي: `{user_info.id}`\n🔗 اليوزر: @{user_info.username if user_info.username else 'لا يوجد'}"
    
    pending_requests[req_id] = {
        "user_id": message.chat.id,
        "user_name": user_info.first_name,
        "type": request_type,
        "amount": amount,
        "details": message.text
    }
    
    bot.send_message(message.chat.id, "✅ تم إرسال طلبك بنجاح إلى الإدارة. يرجى انتظار المراجعة والموافقة...")
    
    admin_keyboard = types.InlineKeyboardMarkup()
    admin_keyboard.row(
        types.InlineKeyboardButton("✅ موافقة", callback_data=f"adm_accept_{req_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"adm_reject_{req_id}")
    )
    
    admin_msg = (
        f"🔔 **وصلك طلب جديد رقم #{req_id}**\n\n"
        f"🛠️ **نوع الطلب:** {request_type}\n"
        f"💰 **المبلغ المستهدف:** {amount:,} ل.س\n\n"
        f"📋 **معلومات الزبون:**\n{user_details}\n\n"
        f"📝 **التفاصيل المرسلة:**\n`{message.text}`"
    )
    bot.send_message(ADMIN_CHAT_ID, admin_msg, reply_markup=admin_keyboard, parse_mode="Markdown")

# ----------------- معالجة أزرار الأدمن (الموافقة والرفض) -----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def handle_admin_decision(call):
    data_parts = call.data.split("_")
    action = data_parts[1]
    req_id = int(data_parts[2])
    
    if req_id not in pending_requests:
        bot.answer_callback_query(call.id, "⚠️ هذا الطلب تم معالجته مسبقاً.")
        bot.delete_message(ADMIN_CHAT_ID, call.message.message_id)
        return
    
    req_data = pending_requests[req_id]
    user_id = req_data["user_id"]
    req_type = req_data["type"]
    amount = req_data["amount"]
    
    if action == "accept":
        if req_type == "إنشاء حساب إيشانسي":
            bot.edit_message_text(f"🔄 **جاري معالجة الحساب للطلب #{req_id}...**\n\nأرسل الآن بيانات الحساب المجهز هنا مباشرة، وسيتولى البوت تسليمها فوراً للزبون:", ADMIN_CHAT_ID, call.message.message_id)
            bot.register_next_step_handler(call.message, send_account_details_to_user, req_id)
            return
        
        elif req_type == "شحن رصيد":
            user_balances[user_id] = user_balances.get(user_id, 0) + amount
            new_bal = user_balances[user_id]
            bot.edit_message_text(f"✅ **تم قبول طلب الشحن #{req_id} بمبلغ {amount:,} ل.س**\n💰 رصيد الزبون الجديد في البوت: {new_bal:,} ل.س", ADMIN_CHAT_ID, call.message.message_id)
            bot.send_message(user_id, f"🎉 **أهلاً يا ملك، تمت الموافقة على دفعتك بنجاح!**\n➕ تم إضافة `{amount:,} ل.س` إلى محفظتك الداخلية.\n💵 رصيدك الحالي الآن: `{new_bal:,} ل.س`.")
            
        elif req_type == "سحب رصيد":
            user_balances[user_id] = user_balances.get(user_id, 0) - amount
            new_bal = user_balances[user_id]
            bot.edit_message_text(f"✅ **تم قبول طلب السحب #{req_id} بمبلغ {amount:,} ل.س**\n💰 المتبقي في رصيده: {new_bal:,} ل.س\n\n⚠️ *الآن قم بالتحويل اليدوي لمحفظته الخارجية المذكورة في الطلب.*", ADMIN_CHAT_ID, call.message.message_id)
            bot.send_message(user_id, f"🎉 **تمت الموافقة على طلب السحب الخاص بك يا ملك!**\n➖ تم خصم `{amount:,} ل.س` من رصيدك في البوت وجاري تحويلها لمحفظتك الخارجية فوراً.")
            
        del pending_requests[req_id]
            
    elif action == "reject":
        bot.edit_message_text(f"❌ **الطلب #{req_id} ({req_type}) تم رفضـه!**", ADMIN_CHAT_ID, call.message.message_id)
        bot.send_message(user_id, f"⚠️ **نعتذر منك يا ملك، تم رفض طلبك الخاص بـ ({req_type}) من قبل الإدارة. يرجى مراجعة التفاصيل والمحاولة مجدداً.**")
        del pending_requests[req_id]
    
    bot.answer_callback_query(call.id, "تم التحديث.")

def send_account_details_to_user(message, req_id):
    if req_id not in pending_requests: return
    req_data = pending_requests[req_id]
    user_id = req_data["user_id"]

  
