import os
import json
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============ CONFIG ============
BOT_TOKEN = "8847795232:AAE9T_U_8gTHZ5xtuS6IWqJD5LNQjTM78Ts"
STORE_NAME = "ABHIXMODZ STORE"
BOT_USERNAME = "abhixmodzstore_bot"
DB_FILE = "db.json"

# ============ DATABASE ============
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {
        "users": {},
        "products": {},
        "orders": {},
        "payments": {},
        "settings": {
            "maintenance": False,
            "support_url": "https://t.me/Abhixmodzsellerindian",
            "channel_url": "@yourchannel",
            "upi_id": "yourname@upi",
            "upi_name": "ABHIXMODZ STORE",
            "spin_enabled": True,
            "referral_bonus": 10
        }
    }

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_user(db, user):
    uid = str(user.id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": user.first_name,
            "username": user.username or "",
            "balance": 0,
            "reseller": False,
            "banned": False,
            "referral_code": "REF" + uid,
            "referred_by": None,
            "total_spent": 0,
            "join_date": datetime.now().strftime("%Y-%m-%d"),
            "spin_last": None,
            "is_admin": False
        }
        save_db(db)
    return db["users"][uid]

def is_admin(db, user):
    uid = str(user.id)
    if uid not in db["users"]:
        return False
    ukeys = list(db["users"].keys())
    if len(ukeys) > 0 and ukeys[0] == uid:
        return True
    return db["users"][uid].get("is_admin", False)

def is_reseller(db, user):
    uid = str(user.id)
    return uid in db["users"] and db["users"][uid].get("reseller", False)

def is_banned(db, user):
    uid = str(user.id)
    return uid in db["users"] and db["users"][uid].get("banned", False)

# ============ MENUS ============
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Shop", callback_data="menu_shop")],
        [
            InlineKeyboardButton("💎 Add Balance", callback_data="menu_balance"),
            InlineKeyboardButton("📜 History", callback_data="menu_history")
        ],
        [
            InlineKeyboardButton("👤 Profile", callback_data="menu_profile"),
            InlineKeyboardButton("🎁 Referral", callback_data="menu_referral")
        ],
        [
            InlineKeyboardButton("🎰 Lucky Spin", callback_data="menu_spin"),
            InlineKeyboardButton("📢 Share & Earn", callback_data="menu_share")
        ],
        [
            InlineKeyboardButton("📺 How To", callback_data="menu_howto"),
            InlineKeyboardButton("🆘 Support", callback_data="menu_support")
        ]
    ])

def get_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Product", callback_data="admin_addproduct")],
        [
            InlineKeyboardButton("📦 Products", callback_data="admin_products"),
            InlineKeyboardButton("📊 Orders", callback_data="admin_orders")
        ],
        [
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("💰 Payments", callback_data="admin_payments")
        ],
        [
            InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance"),
            InlineKeyboardButton("📈 Stats", callback_data="admin_stats")
        ],
        [InlineKeyboardButton("🏠 User View", callback_data="admin_userview")]
    ])

def get_home_text(db, user):
    u = get_user(db, user)
    role = "👑 Admin" if is_admin(db, user) else ("🔰 Reseller" if is_reseller(db, user) else "👤 User")
    return (
        f"🏪 *{STORE_NAME}*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"👋 Hello, *{user.first_name}*!\n\n"
        f"🔑 Premium digital keys, instant delivery.\n\n"
        f"— 🏪 Wide product catalog\n"
        f"— ⚡ Instant key delivery\n"
        f"— 💳 Multiple payment options\n"
        f"— 🎁 Referrals & Lucky Spin\n"
        f"— 🔒 24/7 admin support\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 Balance: *₹{u['balance']}*\n"
        f"🎖 Role: *{role}*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"_Tap any button below_ 👇"
    )

# ============ START ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.effective_user
    u = get_user(db, user)

    # Referral check
    if context.args:
        arg = context.args[0]
        if arg.startswith("src_"):
            ref_code = "REF" + arg.replace("src_", "")
            if not u["referred_by"]:
                for uid, udata in db["users"].items():
                    if udata["referral_code"] == ref_code and uid != str(user.id):
                        u["referred_by"] = uid
                        db["users"][uid]["balance"] += db["settings"]["referral_bonus"]
                        save_db(db)
                        try:
                            await context.bot.send_message(
                                int(uid),
                                f"🎁 *Referral Bonus!*\n\n👤 {user.first_name} joined!\n💰 ₹{db['settings']['referral_bonus']} added!",
                                parse_mode="Markdown"
                            )
                        except:
                            pass
                        break

    if db["settings"]["maintenance"] and not is_admin(db, user):
        await update.message.reply_text(
            "🔧 *Maintenance Mode*\n\nBot is under maintenance.\nPlease check back later!",
            parse_mode="Markdown"
        )
        return

    if is_banned(db, user):
        await update.message.reply_text("🚫 You are banned! Contact support.")
        return

    menu = get_admin_menu() if is_admin(db, user) else get_main_menu()
    await update.message.reply_text(
        get_home_text(db, user),
        parse_mode="Markdown",
        reply_markup=menu
    )

# ============ MESSAGE HANDLER ============
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.effective_user
    txt = update.message.text
    uid = str(user.id)

    if db["settings"]["maintenance"] and not is_admin(db, user):
        await update.message.reply_text("🔧 Maintenance mode. Please wait!")
        return

    if is_banned(db, user):
        await update.message.reply_text("🚫 Banned!")
        return

    state = context.user_data.get("state", "")

    if state == "add_pname":
        context.user_data["pname"] = txt
        context.user_data["state"] = "add_pdesc"
        await update.message.reply_text("📝 Description enter karo:")

    elif state == "add_pdesc":
        context.user_data["pdesc"] = txt
        context.user_data["state"] = "add_pdays"
        await update.message.reply_text("⏰ Kitne days ka product? (number):")

    elif state == "add_pdays":
        if not txt.isdigit():
            await update.message.reply_text("❌ Sirf number!")
            return
        context.user_data["pdays"] = int(txt)
        context.user_data["state"] = "add_uprice"
        await update.message.reply_text("💰 User price ₹:")

    elif state == "add_uprice":
        try:
            context.user_data["uprice"] = float(txt)
            context.user_data["state"] = "add_rprice"
            await update.message.reply_text("👑 Reseller price ₹:")
        except:
            await update.message.reply_text("❌ Sirf number!")

    elif state == "add_rprice":
        try:
            context.user_data["rprice"] = float(txt)
            context.user_data["state"] = "add_pstock"
            await update.message.reply_text("📦 Stock kitna hai?:")
        except:
            await update.message.reply_text("❌ Sirf number!")

    elif state == "add_pstock":
        if not txt.isdigit():
            await update.message.reply_text("❌ Sirf number!")
            return
        context.user_data["pstock"] = int(txt)
        context.user_data["state"] = "add_pkey"
        await update.message.reply_text("🔑 Product key/link enter karo:")

    elif state == "add_pkey":
        context.user_data["pkey"] = txt
        context.user_data["state"] = "add_pvideo"
        await update.message.reply_text("📺 Setup video URL enter karo:\n(Skip ke liye 'skip' likho):")

    elif state == "add_pvideo":
        video = "" if txt == "skip" else txt
        pid = str(int(datetime.now().timestamp() * 1000))
        db["products"][pid] = {
            "name": context.user_data["pname"],
            "description": context.user_data["pdesc"],
            "days": context.user_data["pdays"],
            "user_price": context.user_data["uprice"],
            "reseller_price": context.user_data["rprice"],
            "stock": context.user_data["pstock"],
            "key": context.user_data["pkey"],
            "video_url": video,
            "active": True,
            "sold": 0,
            "created": datetime.now().strftime("%Y-%m-%d")
        }
        save_db(db)
        context.user_data["state"] = ""
        await update.message.reply_text(
            f"✅ *Product Added!*\n\n"
            f"🛍 *{context.user_data['pname']}*\n"
            f"⏰ {context.user_data['pdays']} Days\n"
            f"👤 User: ₹{context.user_data['uprice']}\n"
            f"👑 Reseller: ₹{context.user_data['rprice']}\n"
            f"📦 Stock: {context.user_data['pstock']}",
            parse_mode="Markdown",
            reply_markup=get_admin_menu()
        )

    elif state == "broadcast_msg":
        count = 0
        for uid2 in db["users"]:
            try:
                await context.bot.send_message(
                    int(uid2),
                    f"📣 *{STORE_NAME} - Broadcast*\n\n{txt}",
                    parse_mode="Markdown"
                )
                count += 1
            except:
                pass
        context.user_data["state"] = ""
        await update.message.reply_text(f"✅ {count} users ko message bheja!")

    elif state == "add_money_amt":
        try:
            amt = float(txt)
            tid = context.user_data.get("amuid")
            if not tid or tid not in db["users"]:
                await update.message.reply_text("❌ Invalid!")
                return
            db["users"][tid]["balance"] += amt
            save_db(db)
            context.user_data["state"] = ""
            await update.message.reply_text(f"✅ ₹{amt} added!")
            await context.bot.send_message(
                int(tid),
                f"💰 *Balance Added!*\n\n₹{amt} added by admin!",
                parse_mode="Markdown"
            )
        except:
            await update.message.reply_text("❌ Invalid amount!")

    elif state == "set_upi":
        db["settings"]["upi_id"] = txt
        save_db(db)
        context.user_data["state"] = ""
        await update.message.reply_text(f"✅ UPI ID: {txt}")

    elif state == "set_upi_name":
        db["settings"]["upi_name"] = txt
        save_db(db)
        context.user_data["state"] = ""
        await update.message.reply_text(f"✅ UPI Name: {txt}")

    elif state == "set_support":
        db["settings"]["support_url"] = txt
        save_db(db)
        context.user_data["state"] = ""
        await update.message.reply_text(f"✅ Support URL: {txt}")

    elif state == "set_channel":
        db["settings"]["channel_url"] = txt
        save_db(db)
        context.user_data["state"] = ""
        await update.message.reply_text(f"✅ Channel: {txt}")

    elif state == "set_ref_bonus":
        try:
            bonus = float(txt)
            db["settings"]["referral_bonus"] = bonus
            save_db(db)
            context.user_data["state"] = ""
            await update.message.reply_text(f"✅ Referral bonus: ₹{bonus}")
        except:
            await update.message.reply_text("❌ Invalid!")

    elif state == "custom_topup":
        try:
            amt = float(txt)
            if amt < 1:
                await update.message.reply_text("❌ Minimum ₹1!")
                return
            context.user_data["state"] = ""
            await submit_payment(update, context, db, amt)
        except:
            await update.message.reply_text("❌ Invalid amount!")

    elif state == "edit_stock":
        pid = context.user_data.get("editpid")
        if not txt.isdigit() or not pid or pid not in db["products"]:
            await update.message.reply_text("❌ Invalid!")
            return
        db["products"][pid]["stock"] = int(txt)
        save_db(db)
        context.user_data["state"] = ""
        await update.message.reply_text(f"✅ Stock updated: {txt}")

    elif state == "edit_uprice":
        pid = context.user_data.get("editpid")
        try:
            db["products"][pid]["user_price"] = float(txt)
            save_db(db)
            context.user_data["state"] = ""
            await update.message.reply_text(f"✅ User price: ₹{txt}")
        except:
            await update.message.reply_text("❌ Invalid!")

    elif state == "edit_rprice":
        pid = context.user_data.get("editpid")
        try:
            db["products"][pid]["reseller_price"] = float(txt)
            save_db(db)
            context.user_data["state"] = ""
            await update.message.reply_text(f"✅ Reseller price: ₹{txt}")
        except:
            await update.message.reply_text("❌ Invalid!")

    elif state == "edit_key":
        pid = context.user_data.get("editpid")
        if not pid or pid not in db["products"]:
            await update.message.reply_text("❌ Not found!")
            return
        db["products"][pid]["key"] = txt
        save_db(db)
        context.user_data["state"] = ""
        await update.message.reply_text("✅ Key updated!")

    else:
        menu = get_admin_menu() if is_admin(db, user) else get_main_menu()
        await update.message.reply_text(
            get_home_text(db, user),
            parse_mode="Markdown",
            reply_markup=menu
        )

# ============ PAYMENT ============
async def submit_payment(update, context, db, amt):
    user = update.effective_user
    uid = str(user.id)
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    pay_id = str(int(datetime.now().timestamp() * 1000))

    db["payments"][pay_id] = {
        "user_id": uid,
        "amount": amt,
        "status": "pending",
        "date": date
    }
    save_db(db)

    await update.message.reply_text(
        f"💳 *Payment Request Submitted!*\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 Amount: *₹{amt}*\n"
        f"🏦 UPI ID: `{db['settings']['upi_id']}`\n"
        f"👤 Name: *{db['settings']['upi_name']}*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"1️⃣ Pay ₹{amt} on above UPI\n"
        f"2️⃣ Take screenshot\n"
        f"3️⃣ Admin verify karke balance add karega\n\n"
        f"⏳ Usually 5-10 minutes",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Back to Home", callback_data="back_home")
        ]])
    )

    admin_id = list(db["users"].keys())[0]
    try:
        await context.bot.send_message(
            int(admin_id),
            f"🔔 *New Payment Request!*\n\n"
            f"👤 User: `{uid}` ({user.first_name})\n"
            f"💰 Amount: ₹{amt}\n"
            f"📅 {date}\n"
            f"🆔 Pay ID: {pay_id}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{pay_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{pay_id}")
            ]])
        )
    except:
        pass

# ============ CALLBACK HANDLER ============
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db = load_db()
    user = update.effective_user
    uid = str(user.id)
    u = get_user(db, user)

    if db["settings"]["maintenance"] and not is_admin(db, user) and data != "back_home":
        await query.answer("🔧 Maintenance mode!", show_alert=True)
        return

    # ======= HOME =======
    if data == "back_home":
        menu = get_admin_menu() if is_admin(db, user) else get_main_menu()
        await query.edit_message_text(
            get_home_text(db, user),
            parse_mode="Markdown",
            reply_markup=menu
        )

    # ======= SHOP =======
    elif data == "menu_shop":
        active = {k: v for k, v in db["products"].items() if v["active"] and v["stock"] > 0}
        if not active:
            await query.edit_message_text(
                "🛒 *Shop*\n\n❌ No products available!\n\nCheck back later.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Back", callback_data="back_home")
                ]])
            )
            return
        buttons = []
        for pid, p in active.items():
            price = p["reseller_price"] if is_reseller(db, user) else p["user_price"]
            buttons.append([InlineKeyboardButton(
                f"🔑 {p['name']} - {p['days']}d - ₹{price}",
                callback_data=f"product_{pid}"
            )])
        buttons.append([InlineKeyboardButton("🏠 Back", callback_data="back_home")])
        await query.edit_message_text(
            f"🛒 *{STORE_NAME}*\n━━━━━━━━━━━━━━━━\n\n_Pick a product:_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("product_"):
        pid = data.split("_", 1)[1]
        p = db["products"].get(pid)
        if not p:
            await query.answer("❌ Not found!", show_alert=True)
            return
        price = p["reseller_price"] if is_reseller(db, user) else p["user_price"]
        tag = "👑 Reseller" if is_reseller(db, user) else "👤 User"
        await query.edit_message_text(
            f"🛍 *{p['name']}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📝 {p['description']}\n\n"
            f"⏰ Duration: *{p['days']} Days*\n"
            f"💰 {tag} Price: *₹{price}*\n"
            f"📦 Stock: *{p['stock']}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 Your Balance: *₹{u['balance']}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✅ Buy Now - ₹{price}", callback_data=f"buy_{pid}")],
                [InlineKeyboardButton("◀️ Back to Shop", callback_data="menu_shop")],
                [InlineKeyboardButton("🏠 Home", callback_data="back_home")]
            ])
        )

    elif data.startswith("buy_"):
        pid = data.split("_", 1)[1]
        p = db["products"].get(pid)
        if not p or not p["active"]:
            await query.answer("❌ Not available!", show_alert=True)
            return
        if p["stock"] <= 0:
            await query.answer("❌ Out of stock!", show_alert=True)
            return
        price = p["reseller_price"] if is_reseller(db, user) else p["user_price"]
        if u["balance"] < price:
            await query.edit_message_text(
                f"❌ *Insufficient Balance!*\n\n"
                f"💰 Your Balance: *₹{u['balance']}*\n"
                f"💸 Required: *₹{price}*\n"
                f"📉 Short: *₹{price - u['balance']}*\n\n"
                f"Please add balance first!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Add Balance", callback_data="menu_balance")],
                    [InlineKeyboardButton("🏠 Home", callback_data="back_home")]
                ])
            )
            return

        expiry = (datetime.now() + timedelta(days=p["days"])).strftime("%Y-%m-%d")
        oid = "ORD" + hex(int(datetime.now().timestamp() * 1000))[2:].upper()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        db["users"][uid]["balance"] -= price
        db["users"][uid]["total_spent"] += price
        db["products"][pid]["stock"] -= 1
        db["products"][pid]["sold"] += 1
        db["orders"][oid] = {
            "user_id": uid,
            "product_id": pid,
            "product_name": p["name"],
            "price": price,
            "days": p["days"],
            "expiry": expiry,
            "key": p["key"],
            "video_url": p.get("video_url", ""),
            "date": date
        }
        save_db(db)

        delivery_buttons = []
        if p.get("video_url"):
            delivery_buttons.append([InlineKeyboardButton("📺 Setup Video", url=p["video_url"])])
        delivery_buttons.append([InlineKeyboardButton("🆘 Support", url=db["settings"]["support_url"])])
        delivery_buttons.append([InlineKeyboardButton("🏠 Back to Home", callback_data="back_home")])

        await query.edit_message_text(
            f"✅ *Purchase Successful!*\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"🛍 Product: *{p['name']}*\n"
            f"💰 Price: *₹{price}*\n"
            f"⏰ Duration: *{p['days']} Days*\n"
            f"📅 Expiry: *{expiry}*\n"
            f"🆔 Order: `{oid}`\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔑 *Your Key/Link:*\n\n"
            f"`{p['key']}`\n\n"
            f"━━━━━━━━━━━━━━━━",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(delivery_buttons)
        )

        admin_id = list(db["users"].keys())[0]
        try:
            await context.bot.send_message(
                int(admin_id),
                f"🛒 *New Order!*\n\n"
                f"👤 {user.first_name} (`{uid}`)\n"
                f"🛍 {p['name']}\n"
                f"💰 ₹{price}\n"
                f"🆔 {oid}",
                parse_mode="Markdown"
            )
        except:
            pass

    # ======= BALANCE =======
    elif data == "menu_balance":
        await query.edit_message_text(
            f"💎 *Add Balance*\n━━━━━━━━━━━━━━━━\n\n💰 Current: *₹{u['balance']}*\n\n_Select amount:_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💎 ₹50", callback_data="topup_50"),
                    InlineKeyboardButton("💎 ₹100", callback_data="topup_100")
                ],
                [
                    InlineKeyboardButton("💎 ₹200", callback_data="topup_200"),
                    InlineKeyboardButton("💎 ₹500", callback_data="topup_500")
                ],
                [
                    InlineKeyboardButton("💎 ₹1000", callback_data="topup_1000"),
                    InlineKeyboardButton("✏️ Custom", callback_data="topup_custom")
                ],
                [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
            ])
        )

    elif data.startswith("topup_"):
        amt_str = data.split("_")[1]
        if amt_str == "custom":
            context.user_data["state"] = "custom_topup"
            await query.edit_message_text(
                "✏️ *Custom Amount*\n\nEnter amount in ₹:\n_(Minimum ₹10)_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Back", callback_data="back_home")
                ]])
            )
            return
        amt = float(amt_str)
        await query.edit_message_text(
            f"💳 *Payment Request Submitted!*\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 Amount: *₹{amt}*\n"
            f"🏦 UPI ID: `{db['settings']['upi_id']}`\n"
            f"👤 Name: *{db['settings']['upi_name']}*\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"1️⃣ Pay ₹{amt} on above UPI\n"
            f"2️⃣ Screenshot lo\n"
            f"3️⃣ Admin verify karke balance add karega\n\n"
            f"⏳ Usually 5-10 minutes",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_home")
            ]])
        )
        pay_id = str(int(datetime.now().timestamp() * 1000))
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        db["payments"][pay_id] = {"user_id": uid, "amount": amt, "status": "pending", "date": date}
        save_db(db)
        admin_id = list(db["users"].keys())[0]
        try:
            await context.bot.send_message(
                int(admin_id),
                f"🔔 *New Payment!*\n\n👤 {user.first_name} (`{uid}`)\n💰 ₹{amt}\n📅 {date}\n🆔 {pay_id}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{pay_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{pay_id}")
                ]])
            )
        except:
            pass

    # ======= PROFILE =======
    elif data == "menu_profile":
        orders_count = sum(1 for o in db["orders"].values() if o["user_id"] == uid)
        role = "👑 Admin" if is_admin(db, user) else ("🔰 Reseller" if is_reseller(db, user) else "👤 User")
        await query.edit_message_text(
            f"👤 *Profile*\n━━━━━━━━━━━━━━━━\n\n"
            f"👤 Name: *{user.first_name}*\n"
            f"🆔 ID: `{uid}`\n"
            f"📛 Username: @{user.username or 'N/A'}\n"
            f"🎖 Role: *{role}*\n"
            f"💰 Balance: *₹{u['balance']}*\n"
            f"🛒 Total Orders: *{orders_count}*\n"
            f"💸 Total Spent: *₹{u['total_spent']}*\n"
            f"📅 Joined: *{u['join_date']}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🎁 Referral Code: `{u['referral_code']}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back", callback_data="back_home")
            ]])
        )

    # ======= HISTORY =======
    elif data == "menu_history":
        my_orders = [o for o in db["orders"].values() if o["user_id"] == uid]
        if not my_orders:
            await query.edit_message_text(
                "📜 *Order History*\n\n❌ No orders yet!\n\nBuy something from shop 🛒",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 Shop", callback_data="menu_shop")],
                    [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
                ])
            )
            return
        text = f"📜 *Order History*\n━━━━━━━━━━━━━━━━\n\n💸 Total: *₹{u['total_spent']}*\n\n"
        for o in my_orders[-5:]:
            text += f"🛍 {o['product_name']}\n💰 ₹{o['price']} | ⏰ {o['days']}d\n📅 {o['date']}\n\n"
        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back", callback_data="back_home")
            ]])
        )

    # ======= REFERRAL =======
    elif data == "menu_referral":
        ref_link = f"https://t.me/{BOT_USERNAME}?start=src_{uid}"
        ref_count = sum(1 for u2 in db["users"].values() if u2.get("referred_by") == uid)
        await query.edit_message_text(
            f"🎁 *Referral Program*\n━━━━━━━━━━━━━━━━\n\n"
            f"💰 Bonus per referral: *₹{db['settings']['referral_bonus']}*\n"
            f"👥 Your referrals: *{ref_count}*\n"
            f"💵 Total earned: *₹{ref_count * db['settings']['referral_bonus']}*\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔗 Your referral link:\n`{ref_link}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={ref_link}")],
                [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
            ])
        )

    # ======= SPIN =======
    elif data == "menu_spin":
        today = datetime.now().strftime("%Y-%m-%d")
        last_spin = u.get("spin_last", "")
        if last_spin and last_spin[:10] == today:
            await query.edit_message_text(
                "🎰 *Lucky Spin*\n\n❌ Already spun today!\n\n⏰ Come back tomorrow!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Back", callback_data="back_home")
                ]])
            )
            return
        await query.edit_message_text(
            "🎰 *Lucky Spin*\n\nSpin once per day!\n\nPrizes: ₹5 to ₹50!\n\n🎲 Tap to spin!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎰 SPIN NOW!", callback_data="do_spin")],
                [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
            ])
        )

    elif data == "do_spin":
        prizes = [5, 5, 5, 10, 10, 10, 20, 20, 50]
        prize = random.choice(prizes)
        db["users"][uid]["balance"] += prize
        db["users"][uid]["spin_last"] = datetime.now().isoformat()
        save_db(db)
        await query.edit_message_text(
            f"🎰 *Lucky Spin Result!*\n\n🎊 Congratulations!\n\n💰 You won: *₹{prize}*\n\nCome back tomorrow!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Shop Now", callback_data="menu_shop")],
                [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
            ])
        )

    # ======= SHARE =======
    elif data == "menu_share":
        share_link = f"https://t.me/{BOT_USERNAME}?start=src_share"
        await query.edit_message_text(
            f"📢 *Share & Earn*\n━━━━━━━━━━━━━━━━\n\n"
            f"🎁 Share karo aur earn karo!\n\n"
            f"_Each friend = ₹{db['settings']['referral_bonus']} bonus!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Now", url=f"https://t.me/share/url?url={share_link}")],
                [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
            ])
        )

    # ======= HOW TO =======
    elif data == "menu_howto":
        await query.edit_message_text(
            "📺 *HOW TO USE*\n━━━━━━━━━━━━━━━━\n\n👇 Tap any guide:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📺 How To Use (Hindi)", url="https://youtube.com")],
                [InlineKeyboardButton("📺 How To Buy Key", url="https://youtube.com")],
                [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
            ])
        )

    # ======= SUPPORT =======
    elif data == "menu_support":
        await query.edit_message_text(
            f"🆘 *Support*\n━━━━━━━━━━━━━━━━\n\n"
            f"Hum help kar sakte hain:\n"
            f"— 🔑 Orders & keys\n"
            f"— 💳 Payments\n"
            f"— 📦 Products\n\n"
            f"⏰ Reply: few hours",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Contact Support", url=db["settings"]["support_url"])],
                [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
            ])
        )

    # ======= PAYMENTS =======
    elif data.startswith("approve_"):
        pay_id = data.split("_", 1)[1]
        pay = db["payments"].get(pay_id)
        if not pay:
            await query.answer("Not found!", show_alert=True)
            return
        db["users"][pay["user_id"]]["balance"] += pay["amount"]
        db["payments"][pay_id]["status"] = "approved"
        save_db(db)
        await query.edit_message_text(
            f"✅ *Approved!*\n💰 ₹{pay['amount']} added!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back", callback_data="back_home")
            ]])
        )
        try:
            await context.bot.send_message(
                int(pay["user_id"]),
                f"✅ *Payment Approved!*\n\n💰 ₹{pay['amount']} added!\n\n🛒 Shop now!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🛒 Shop", callback_data="menu_shop")
                ]])
            )
        except:
            pass

    elif data.startswith("reject_"):
        pay_id = data.split("_", 1)[1]
        pay = db["payments"].get(pay_id)
        if not pay:
            await query.answer("Not found!", show_alert=True)
            return
        db["payments"][pay_id]["status"] = "rejected"
        save_db(db)
        await query.edit_message_text(
            "❌ *Rejected!*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back", callback_data="back_home")
            ]])
        )
        try:
            await context.bot.send_message(
                int(pay["user_id"]),
                f"❌ *Payment Rejected!*\n\n💰 ₹{pay['amount']}\n\n🆘 Support se contact karo.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🆘 Support", url=db["settings"]["support_url"])
                ]])
            )
        except:
            pass

    # ======= ADMIN =======
    elif data == "admin_userview":
        menu = get_main_menu()
        await query.edit_message_text(
            get_home_text(db, user), parse_mode="Markdown", reply_markup=menu
        )

    elif data == "admin_addproduct":
        context.user_data["state"] = "add_pname"
        await query.edit_message_text(
            "➕ *Add New Product*\n\n📝 Product name enter karo:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="back_home")
            ]])
        )

    elif data == "admin_products":
        if not db["products"]:
            await query.edit_message_text(
                "❌ No products!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Back", callback_data="back_home")
                ]])
            )
            return
        buttons = []
        for pid, p in db["products"].items():
            status = "✅" if p["active"] else "❌"
            buttons.append([InlineKeyboardButton(
                f"{status} {p['name']} | Stock:{p['stock']}",
                callback_data=f"prodmgr_{pid}"
            )])
        buttons.append([InlineKeyboardButton("🏠 Back", callback_data="back_home")])
        await query.edit_message_text(
            "📦 *Products List*\n\n_Tap to manage:_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("prodmgr_"):
        pid = data.split("_", 1)[1]
        p = db["products"].get(pid)
        if not p:
            await query.answer("Not found!", show_alert=True)
            return
        await query.edit_message_text(
            f"📦 *{p['name']}*\n━━━━━━━━━━━━━━━━\n"
            f"⏰ Days: {p['days']}\n"
            f"👤 User: ₹{p['user_price']}\n"
            f"👑 Reseller: ₹{p['reseller_price']}\n"
            f"📦 Stock: {p['stock']}\n"
            f"✅ Sold: {p['sold']}\n"
            f"📊 Status: {'Active ✅' if p['active'] else 'Inactive ❌'}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📦 Edit Stock", callback_data=f"editstock_{pid}"),
                    InlineKeyboardButton("💰 Edit Price", callback_data=f"editprice_{pid}")
                ],
                [
                    InlineKeyboardButton("🔑 Edit Key", callback_data=f"editkey_{pid}"),
                    InlineKeyboardButton("❌ Deactivate" if p["active"] else "✅ Activate", callback_data=f"toggleprod_{pid}")
                ],
                [InlineKeyboardButton("🗑 Delete", callback_data=f"delprod_{pid}")],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_products")]
            ])
        )

    elif data.startswith("editstock_"):
        pid = data.split("_", 1)[1]
        context.user_data["editpid"] = pid
        context.user_data["state"] = "edit_stock"
        await query.edit_message_text(
            "📦 New stock amount:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_products")
            ]])
        )

    elif data.startswith("editprice_"):
        pid = data.split("_", 1)[1]
        context.user_data["editpid"] = pid
        await query.edit_message_text(
            "💰 *Edit Price*\n\nSelect:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 User Price", callback_data=f"edituprice_{pid}")],
                [InlineKeyboardButton("👑 Reseller Price", callback_data=f"editrprice_{pid}")],
                [InlineKeyboardButton("◀️ Back", callback_data=f"prodmgr_{pid}")]
            ])
        )

    elif data.startswith("edituprice_"):
        pid = data.split("_", 1)[1]
        context.user_data["editpid"] = pid
        context.user_data["state"] = "edit_uprice"
        await query.edit_message_text(
            "💰 New user price ₹:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data=f"prodmgr_{pid}")
            ]])
        )

    elif data.startswith("editrprice_"):
        pid = data.split("_", 1)[1]
        context.user_data["editpid"] = pid
        context.user_data["state"] = "edit_rprice"
        await query.edit_message_text(
            "👑 New reseller price ₹:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data=f"prodmgr_{pid}")
            ]])
        )

    elif data.startswith("editkey_"):
        pid = data.split("_", 1)[1]
        context.user_data["editpid"] = pid
        context.user_data["state"] = "edit_key"
        await query.edit_message_text(
            "🔑 New key/link:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data=f"prodmgr_{pid}")
            ]])
        )

    elif data.startswith("toggleprod_"):
        pid = data.split("_", 1)[1]
        if pid not in db["products"]:
            await query.answer("Not found!", show_alert=True)
            return
        db["products"][pid]["active"] = not db["products"][pid]["active"]
        save_db(db)
        status = "✅ Activated!" if db["products"][pid]["active"] else "❌ Deactivated!"
        await query.answer(status, show_alert=True)
        await query.edit_message_text(
            status,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data="admin_products")
            ]])
        )

    elif data.startswith("delprod_"):
        pid = data.split("_", 1)[1]
        db["products"].pop(pid, None)
        save_db(db)
        await query.edit_message_text(
            "🗑 Product deleted!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data="admin_products")
            ]])
        )

    elif data == "admin_orders":
        if not db["orders"]:
            await query.edit_message_text(
                "❌ No orders!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Back", callback_data="back_home")
                ]])
            )
            return
        text = "📊 *All Orders*\n━━━━━━━━━━━━━━━━\n\n"
        for oid, o in list(db["orders"].items())[-10:]:
            text += f"🛍 {o['product_name']} | ₹{o['price']}\n👤 {o['user_id']}\n📅 {o['date']}\n\n"
        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back", callback_data="back_home")
            ]])
        )

    elif data == "admin_users":
        buttons = []
        for tid, tu in db["users"].items():
            role_icon = "👑" if tu.get("is_admin") else ("🔰" if tu.get("reseller") else "👤")
            buttons.append([InlineKeyboardButton(
                f"{role_icon} {tu['name']} | ₹{tu['balance']}",
                callback_data=f"usermgr_{tid}"
            )])
        buttons.append([InlineKeyboardButton("🏠 Back", callback_data="back_home")])
        await query.edit_message_text(
            f"👥 *Users ({len(db['users'])})*\n\n_Tap to manage:_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("usermgr_"):
        tid = data.split("_", 1)[1]
        tu = db["users"].get(tid)
        if not tu:
            await query.answer("Not found!", show_alert=True)
            return
        role = "👑 Admin" if tu.get("is_admin") else ("🔰 Reseller" if tu.get("reseller") else "👤 User")
        status = "🚫 Banned" if tu.get("banned") else "✅ Active"
        await query.edit_message_text(
            f"👤 *{tu['name']}*\n━━━━━━━━━━━━━━━━\n"
            f"🆔 `{tid}`\n"
            f"💰 Balance: ₹{tu['balance']}\n"
            f"🎖 Role: {role}\n"
            f"📊 Status: {status}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Add Money", callback_data=f"uadd_{tid}"),
                    InlineKeyboardButton("🚫 Ban" if not tu.get("banned") else "✅ Unban", callback_data=f"uban_{tid}")
                ],
                [
                    InlineKeyboardButton("🔰 Make Reseller" if not tu.get("reseller") else "👤 Remove Reseller", callback_data=f"ureseller_{tid}"),
                    InlineKeyboardButton("👑 Make Admin" if not tu.get("is_admin") else "👤 Remove Admin", callback_data=f"uadmin_{tid}")
                ],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_users")]
            ])
        )

    elif data.startswith("uadd_"):
        tid = data.split("_", 1)[1]
        context.user_data["amuid"] = tid
        context.user_data["state"] = "add_money_amt"
        await query.edit_message_text(
            f"💰 Amount enter karo ₹ for {tid}:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data=f"usermgr_{tid}")
            ]])
        )

    elif data.startswith("uban_"):
        tid = data.split("_", 1)[1]
        if tid not in db["users"]:
            await query.answer("Not found!", show_alert=True)
            return
        db["users"][tid]["banned"] = not db["users"][tid].get("banned", False)
        save_db(db)
        status = "🚫 Banned!" if db["users"][tid]["banned"] else "✅ Unbanned!"
        await query.answer(status, show_alert=True)
        await query.edit_message_text(
            status,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data=f"usermgr_{tid}")
            ]])
        )

    elif data.startswith("ureseller_"):
        tid = data.split("_", 1)[1]
        if tid not in db["users"]:
            await query.answer("Not found!", show_alert=True)
            return
        db["users"][tid]["reseller"] = not db["users"][tid].get("reseller", False)
        save_db(db)
        status = "🔰 Reseller!" if db["users"][tid]["reseller"] else "👤 Normal!"
        await query.answer(status, show_alert=True)
        await query.edit_message_text(
            status,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data=f"usermgr_{tid}")
            ]])
        )

    elif data.startswith("uadmin_"):
        tid = data.split("_", 1)[1]
        if tid not in db["users"]:
            await query.answer("Not found!", show_alert=True)
            return
        db["users"][tid]["is_admin"] = not db["users"][tid].get("is_admin", False)
        save_db(db)
        status = "👑 Admin!" if db["users"][tid]["is_admin"] else "👤 Normal!"
        await query.answer(status, show_alert=True)
        await query.edit_message_text(
            status,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data=f"usermgr_{tid}")
            ]])
        )

    elif data == "admin_payments":
        pending = {k: v for k, v in db["payments"].items() if v["status"] == "pending"}
        if not pending:
            await query.edit_message_text(
                "✅ No pending payments!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Back", callback_data="back_home")
                ]])
            )
            return
        for pay_id, pay in pending.items():
            await context.bot.send_message(
                user.id,
                f"💳 *Payment*\n👤 {pay['user_id']}\n💰 ₹{pay['amount']}\n📅 {pay['date']}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{pay_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{pay_id}")
                ]])
            )

    elif data == "admin_broadcast":
        context.user_data["state"] = "broadcast_msg"
        await query.edit_message_text(
            "📣 *Broadcast*\n\nMessage enter karo:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="back_home")
            ]])
        )

    elif data == "admin_settings":
        await query.edit_message_text(
            f"⚙️ *Settings*\n━━━━━━━━━━━━━━━━\n\n"
            f"🏦 UPI: `{db['settings']['upi_id']}`\n"
            f"👤 UPI Name: {db['settings']['upi_name']}\n"
            f"🆘 Support: {db['settings']['support_url']}\n"
            f"🎁 Referral Bonus: ₹{db['settings']['referral_bonus']}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏦 UPI ID", callback_data="setg_upi")],
                [InlineKeyboardButton("👤 UPI Name", callback_data="setg_upi_name")],
                [InlineKeyboardButton("🆘 Support URL", callback_data="setg_support")],
                [InlineKeyboardButton("📢 Channel", callback_data="setg_channel")],
                [InlineKeyboardButton("🎁 Referral Bonus", callback_data="setg_refbonus")],
                [InlineKeyboardButton("🏠 Back", callback_data="back_home")]
            ])
        )

    elif data == "setg_upi":
        context.user_data["state"] = "set_upi"
        await query.edit_message_text(
            "🏦 UPI ID enter karo:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")
            ]])
        )

    elif data == "setg_upi_name":
        context.user_data["state"] = "set_upi_name"
        await query.edit_message_text(
            "👤 UPI Name enter karo:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")
            ]])
        )

    elif data == "setg_support":
        context.user_data["state"] = "set_support"
        await query.edit_message_text(
            "🆘 Support URL enter karo:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")
            ]])
        )

    elif data == "setg_channel":
        context.user_data["state"] = "set_channel"
        await query.edit_message_text(
            "📢 Channel enter karo:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")
            ]])
        )

    elif data == "setg_refbonus":
        context.user_data["state"] = "set_ref_bonus"
        await query.edit_message_text(
            "🎁 Referral bonus ₹ enter karo:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")
            ]])
        )

    elif data == "admin_maintenance":
        db["settings"]["maintenance"] = not db["settings"]["maintenance"]
        save_db(db)
        status = "ON 🔴" if db["settings"]["maintenance"] else "OFF 🟢"
        await query.edit_message_text(
            f"🔧 *Maintenance Mode: {status}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back", callback_data="back_home")
            ]])
        )

    elif data == "admin_stats":
        total_revenue = sum(o["price"] for o in db["orders"].values())
        pending = sum(1 for p in db["payments"].values() if p["status"] == "pending")
        await query.edit_message_text(
            f"📈 *Store Statistics*\n━━━━━━━━━━━━━━━━\n\n"
            f"👥 Total Users: *{len(db['users'])}*\n"
            f"🛒 Total Orders: *{len(db['orders'])}*\n"
            f"💰 Total Revenue: *₹{total_revenue}*\n"
            f"📦 Total Products: *{len(db['products'])}*\n"
            f"💳 Pending Payments: *{pending}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Back", callback_data="back_home")
            ]])
        )

# ============ MAIN ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("✅ Bot chalu ho gaya!")
    app.run_polling()

if __name__ == "__main__":
    main()
