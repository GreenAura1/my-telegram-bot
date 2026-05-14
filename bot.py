import telebot
from telebot import types
import sqlite3

TOKEN = "8896763784:AAHm0DwyLyhGCrLXnL2I9cfKmGG7M82DJrE"
ADMIN_ID = 8236822036

bot = telebot.TeleBot(TOKEN)

# ---------------- DB ----------------
conn = sqlite3.connect("orders.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item TEXT,
    status TEXT
)
""")
conn.commit()


# ---------------- PRODUCTS ----------------
products = ["100 грам", "200 грам", "500 грам", "1 кг"]


# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for p in products:
        markup.add(types.KeyboardButton(p))

    bot.send_message(message.chat.id, "🛒 Оберіть товар:", reply_markup=markup)


# ---------------- CREATE ORDER ----------------
@bot.message_handler(func=lambda m: m.text in products)
def create_order(message):

    cur.execute(
        "INSERT INTO orders (user_id, item, status) VALUES (?, ?, ?)",
        (message.from_user.id, message.text, "pending")
    )
    conn.commit()

    order_id = cur.lastrowid

    bot.send_message(
        message.chat.id,
        f"🧾 Замовлення №{order_id}\n\n"
        "💳 Очікує оплату\n\n"
        "Після оплати адміністратор оновить статус."
    )

    # адмін повідомлення
    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton("💰 Оплачено", callback_data=f"paid_{order_id}"),
        types.InlineKeyboardButton("🚚 В дорозі", callback_data=f"ship_{order_id}"),
        types.InlineKeyboardButton("📦 Доставлено", callback_data=f"done_{order_id}")
    )

    bot.send_message(
        ADMIN_ID,
        f"📥 Нове замовлення №{order_id}\nТовар: {message.text}",
        reply_markup=markup
    )


# ---------------- ADMIN STATUS CONTROL ----------------
@bot.callback_query_handler(func=lambda c: True)
def admin_actions(call):

    data = call.data.split("_")
    action = data[0]
    order_id = data[1]

    if action == "paid":
        status = "Оплачено"
    elif action == "ship":
        status = "В дорозі"
    elif action == "done":
        status = "Доставлено"
    else:
        return

    cur.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()

    # отримати user
    cur.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
    user_id = cur.fetchone()[0]

    bot.send_message(
        user_id,
        f"📦 Замовлення №{order_id}\n\n"
        f"📊 Статус: {status}"
    )

    bot.answer_callback_query(call.id, "Оновлено")


# ---------------- ADMIN COMMAND ----------------
@bot.message_handler(commands=['admin'])
def admin(message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()

    text = "📊 Останні замовлення:\n\n"

    for r in rows:
        text += f"#{r[0]} | {r[2]} | {r[3]}\n"

    bot.send_message(message.chat.id, text)


print("Bot running...")
bot.infinity_polling()