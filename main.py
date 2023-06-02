from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ConversationHandler, ContextTypes, filters
from supabase import create_client
from keys import key, SUPABASE_URL, SUPABASE_KEY

def words():
    response = supabase.table("words").select("word").execute()
    word_list = [row["word"] for row in response.data]
    return word_list

# Start function to test if bot is working
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Starting to count...")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.lower()
    word_list = words()
    insert_list = []
    # For loop to check for existence of banned word
    for word in word_list:
        if word in text:
            # Count of instances
            count = text.count(word) if word != "testword" else 0
            values = {"username": update.message.from_user.username, "word": word, "count": count}
            insert_list.append(values)    
            await update.message.reply_text(f"@{update.message.from_user.username} said '{word}' {count} time(s)")
    data = supabase.table("records").insert(insert_list).execute()

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = supabase.table("score").select("username", "total_count").execute() # Changed the "*" to specific columns

    # Try out optimised code, old one commented
    scoreboard = "\n".join(f'@{row["username"]}: {row["total_count"]}' for row in response.data)
    await update.message.reply_text(scoreboard)

INSERT = range(1)

async def addword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word_list = words()
    current_word_list = "\n".join(f'{word}' for word in word_list)
    await update.message.reply_text(f"The current list:\n{current_word_list}\n\nSend the word you would like to add in this format - word1 word2 ...\n/cancel to end")

    return INSERT

async def insertword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word_list = words()
    text = update.message.text
    # Format input to get a list of words
    user_text_list = list(set(text.lower().split()))
    insert_list = []
    for user_text in user_text_list:
        if user_text in word_list:
            await update.message.reply_text(f"{user_text} is already in the list! Remove it and /addword again")
        else:
            insert_list.append({"word": user_text})
    data = supabase.table("words").insert(insert_list).execute()
    word_list = words()
    current_word_list = "\n".join(f'{word}' for word in word_list)
    await update.message.reply_text(f"The current list:\n{current_word_list}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word_list = words()
    current_word_list = "\n".join(f'{word}' for word in word_list)
    await update.message.reply_text(f"The current list:\n{current_word_list}")

    return ConversationHandler.END

if __name__ == "__main__":
    application = Application.builder().token(key).build()

    # Create supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addword", addword)],
        states={ 
            INSERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, insertword)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(conv_handler)

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("score", score))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))

    # Start Bot
    application.run_polling()