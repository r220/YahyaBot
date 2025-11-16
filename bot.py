from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json
from dotenv import load_dotenv
from os import getenv

load_dotenv()
TOKEN = getenv('TOKEN')
JSON = 'data.json'
PAGE_SIZE = 10  # number of channels per page
RETURN_BACK = "RETURN BACK"
ADD = "ADD"
DEL = "DELETE"
file = ''
request_add_word = ''   # 0: none, 1: allowed, 2: blocked
input_state = None     # waiting input from user on replyMarkupButton
KEYBOARDS = {
    'category': {
        'msg': "choose Category:",
        'keyboard': InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Users ⚙️", callback_data="users"),
                InlineKeyboardButton("Words 📝", callback_data="words")
            ],
        ])
    },
    'users': {
        'msg': "👥 Manage Users:",
        'keyboard': InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ACCEPTED", callback_data="allowed_users"),
                InlineKeyboardButton("BLOCKED", callback_data="blocked_users"),
            ],
            [InlineKeyboardButton(RETURN_BACK, callback_data="category")]
        ]),
    },

    'words': {
        'msg': "💬 Manage Words:",
        'keyboard': InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ACCEPTED", callback_data="allowed_words"),
                InlineKeyboardButton("BLOCKED", callback_data="blocked_words"),
            ],
            [InlineKeyboardButton(RETURN_BACK, callback_data="category")]
        ]),
    },

    'allowed_users': {
        'msg': "✅ Allowed Users - Add or Remove:",
        'keyboard': InlineKeyboardMarkup([
            [
                InlineKeyboardButton(ADD, callback_data="add-allowed_users"),
                InlineKeyboardButton(DEL, callback_data="del-allowed_users"),
            ],
            [InlineKeyboardButton(RETURN_BACK, callback_data="users")]
        ]),
    },

    'blocked_users': {
        'msg': "🚫 Blocked Users - Add or Remove:",
        'keyboard': InlineKeyboardMarkup([
            [
                InlineKeyboardButton(ADD, callback_data="add-blocked_users"),
                InlineKeyboardButton(DEL, callback_data="del-blocked_users"),
            ],
            [InlineKeyboardButton(RETURN_BACK, callback_data="users")]
        ]),
    },

    'allowed_words': {
        'msg': "✅ Allowed Words – Add or Remove:",
        'keyboard': InlineKeyboardMarkup([
            [
                InlineKeyboardButton(ADD, callback_data="add-allowed_words"),
                InlineKeyboardButton(DEL, callback_data="del-allowed_words"),
            ],
            [InlineKeyboardButton(RETURN_BACK, callback_data="words")]
        ]),
    },

    'blocked_words': {
        'msg': "🚫 Blocked Words - Add or Remove:",
        'keyboard': InlineKeyboardMarkup([
            [
                InlineKeyboardButton(ADD, callback_data="add-blocked_words"),
                InlineKeyboardButton(DEL, callback_data="del-blocked_words"),
            ],
            [InlineKeyboardButton(RETURN_BACK, callback_data="words")]
        ]),
    },
    "add-allowed_users": {
        'msg': "select user to allow forward messages:",
        'list': "remained_users",
        'prev': 'allowed_users'
        },
    "del-allowed_users": {
        'msg': "select user to remove access:",
        'list': "allowed_users",
        'prev': 'allowed_users'
        },
    "add-blocked_users": {
        'msg': "select user to block forward messages:",
        'list': "remained_users",
        'prev': 'blocked_users'
        },
    "del-blocked_users": {
        'msg': "select blocked user to remove block:",
        'list': "blocked_users",
        'prev': 'blocked_users'
        },
    # add-allowed_words "reply with a message that containes the word:"
    "del-allowed_words": {
        'msg': "select allowed word that will be removed:",
        'list': 'allowed_words',
        'prev': 'allowed_words'

        },
    # add-blocked_words "reply with a message that containes the word:"
    "del-blocked_words": {
        'msg': "select word:",
        'list': "blocked_words",
        'prev': 'blocked_words'
    }
}
file_lists = {
    "remained_users": [],
    "allowed_users": [],
    "blocked_users": [],
    "allowed_words": [],
    "blocked_words": []
}
# -------------------------------------------------------------------
def load_json():
    global file
    with open(JSON, "r") as f:
        file = json.load(f)
        # print(file)
        file_lists["remained_users"] = file["users"]["remained"]
        file_lists['allowed_users'] = file['users']['allowed']
        file_lists["blocked_users"] = file["users"]["blocked"]
        file_lists['allowed_words'] = file['words']['allowed']
        file_lists["blocked_words"] = file["words"]["blocked"]
        # return file
# -------------------------------------------------------------------
def get_dict_from_id(dicts, id):
    # id = int(id)
    # print(f'id: {id}','dicts: ', dicts)
    for d in dicts:
        if d.get("id") == id:
            return d
# -------------------------------------------------------------------
async def choice_selected(choice: str, query):
    # print(choice)
    global file
    # data = 'add:allowed_users--00000'
    # ------------------------
    command = choice[:3] # 'add'
    split = choice[4:].split('-') # ['allowed_users', '00000'] / ['allowed_users', '', '00000']
    category = split[0].split('_') # ['allowed', 'users']
    c_list = category[0] # 'allowed'
    c_name = category[1] # 'users'
    data = ''
    # ------------------------
    msg = '' # msg sent to user in the end
    # ------------------------
    match c_name:
        case 'users':
            if len(split) == 3:
                data = '-'.join(split[1:]) # '00000' / "-00000"
            match command:
                case 'add':
                    # del from remained + add to c_list
                    temp = get_dict_from_id(file[c_name]['remained'], data)
                    if temp:
                        file[c_name]['remained'].remove(temp)
                        file[c_name][c_list].append(temp)
                        msg = f'✅ user "{temp['name']}" added successfully !'
                case 'del':
                    # add to remained - then del
                    temp = get_dict_from_id(file[c_name][c_list], data)
                    print('temps: ', temp)
                    if temp:
                        file[c_name][c_list].remove(temp)
                        file[c_name]['remained'].append(temp)
                        msg = f'✅ user "{temp['name']}" removed successfully !'                    

        case 'words':
            data = ''.join(split[1:]) # '00000'
            match command:
                case 'add':
                    if data not in file[c_name][c_list]:
                        file[c_name][c_list].append(data)
                        msg = f'✅ word "{data}" added successfully !'
                case 'del':
                    if data in file[c_name][c_list]:
                        file[c_name][c_list].remove(data)
                        msg = f'✅ word "{data}" removed successfully !'
    
    if (msg):            
        with open(JSON, "w") as f:
            json.dump(file, f, indent = 4)
        load_json()
        # await query.edit_message_text(msg, )
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(RETURN_BACK, callback_data=f'{split[0]}')]])
        await query.edit_message_text(msg, reply_markup=reply_markup)

    else:
        await query.edit_message_text(f"❌ Request Failed..\nif you think that the problem is from bot, don't hesitate contacting dv.Reem ^_* !")
        
# -------------------------------------------------------------------  
# ===== Helper: build channel menu with pagination =====
def build_keyboard(data: str, page: int):
    # data = 'add-allowed_users'
    global file
    cmd = data.split('-')[0]
    block = KEYBOARDS[data]
    list = file_lists[block['list']]
    prev = block['prev']
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    cmdList = data.replace('-', ':')
    buttons = []
    
    if (data.endswith('users')):
        buttons = [
            [InlineKeyboardButton(text=str(user.get("name")), callback_data=f"{cmdList}-{user['id']}")]
            for user in list[start:end]
        ]
    elif (data.endswith('words')):
        buttons = [[InlineKeyboardButton(name, callback_data=f"{cmdList}-{name}")] for i, name in enumerate(list[start:end], start)]

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page-1}_{data}"))
    if end < len(list):
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}_{data}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(RETURN_BACK, callback_data=prev)])
    
    return InlineKeyboardMarkup(buttons)

async def edit_message_text(data: str, query, page = 0):
    msg = KEYBOARDS[data]["msg"]
    keyboard = ''
    if 'list' in KEYBOARDS[data]:
        keyboard = build_keyboard(data, page)
    else: 
        keyboard = KEYBOARDS[data]["keyboard"]
    await query.edit_message_text(msg, reply_markup=keyboard)
        
# ===== Handle all button presses =====
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # --------------------------------------------
    # START
    # --------------------------------------------
    
    # page (next - prev)
    if data.startswith("page_"):
        split = data.split("_")
        page = int(split[1])
        data = '_'.join(split[2:])
        reply_markup = build_keyboard(data, page)
        await query.edit_message_text(f"Select (page {page+1}):", reply_markup=reply_markup)
    # choice selected
    elif ':' in data.split('_')[0]:
        await choice_selected(data, query)
    # other choices
    elif data in ['add-allowed_words', 'add-blocked_words']:
        global request_add_word
        request_add_word = 'allowed' if ('allowed' in data) else 'blocked'
        reply_markup = ReplyKeyboardMarkup(keyboard = [["Start input"]], resize_keyboard=True)
        await query.message.reply_text("Tap the button below 👇", reply_markup=reply_markup)
    else:
        await edit_message_text(data, query)
    
async def add_word_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global input_state, request_add_word
    text = update.message.text
    print(text)
    # -----------------------------
    if text == "Start input":
        # user pressed the ReplyKeyboardButton
        input_state = "awaiting_input"
        await update.message.reply_text("Now send your word:")
    else:
        # check if the user was supposed to send a reply
        if input_state == "awaiting_input":
            input_state = None
            # save text to file
            if request_add_word:
                file['words'][request_add_word].append(text)
                with open(JSON, "w") as f:
                    json.dump(file, f, indent = 4)
                load_json()
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(RETURN_BACK, callback_data=f'{request_add_word}_words')]])
                await update.message.reply_text("✅ word is saved.", reply_markup=reply_markup)
        else:
            await update.message.reply_text("🤖 send '/start' to use bot...")
    

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = KEYBOARDS["category"]["keyboard"]
    await update.message.reply_text(KEYBOARDS["category"]["msg"], reply_markup=reply_markup)

# ===== Main =====
def main():
    load_json()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", show_category))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_word_event))
    
    print("Bot is running...")
    # print('kk is ', file)
    app.run_polling()

if __name__ == "__main__":
    main()