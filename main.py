import logging
import nest_asyncio
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
)

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Define states
SELECT_COMPONENT, GET_ATTENDANCE = range(2)

# Components list
components = ["Lecture", "Skilling", "Practical", "Tutorial", "Done"]

# Start attendance process
async def start_attendance(update: Update, context: CallbackContext) -> int:
    context.user_data["attendance_data"] = {}
    reply_keyboard = [[comp] for comp in components]
    
    await update.message.reply_text(
        "Select a component (or type 'Done' when finished):",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_COMPONENT

# Get component and ask for attendance percentage
async def get_component(update: Update, context: CallbackContext) -> int:
    component = update.message.text

    if component == "Done":
        return await calculate_final_attendance(update, context)

    context.user_data["current_component"] = component
    await update.message.reply_text(f"Enter attendance percentage for {component} (e.g., 75)")
    return GET_ATTENDANCE

# Store attendance and ask for the next component
async def get_attendance(update: Update, context: CallbackContext) -> int:
    try:
        percentage = float(update.message.text)
        component = context.user_data["current_component"]
        context.user_data["attendance_data"][component] = percentage

        reply_keyboard = [[comp] for comp in components]
        await update.message.reply_text(
            "Select another component (or type 'Done' to finish):",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return SELECT_COMPONENT

    except ValueError:
        await update.message.reply_text("Invalid input! Enter a number (e.g., 75).")
        return GET_ATTENDANCE

# Calculate and display overall attendance percentage
async def calculate_final_attendance(update: Update, context: CallbackContext) -> int:
    attendance_data = context.user_data.get("attendance_data", {})

    if not attendance_data:
        await update.message.reply_text("No attendance data provided.")
        return ConversationHandler.END

    total_percentage = sum(attendance_data.values()) / len(attendance_data)

    if total_percentage >= 85:
        await update.message.reply_text(f"✅ Final Attendance: {total_percentage:.2f}%")
    else:
        await update.message.reply_text(f"❌ Final Attendance is below 85% ({total_percentage:.2f}%).")

    return ConversationHandler.END

# Cancel function
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Attendance calculation canceled.")
    return ConversationHandler.END

# Start bot
async def main():
    BOT_TOKEN = "7544916414:AAER4wo7zVUJXbIqrGTiGvS5Bf5S8M_-Dds"

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("attendance", start_attendance)],
        states={
            SELECT_COMPONENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_component)],
            GET_ATTENDANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_attendance)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)

    print("✅ Bot is running...")
    await app.run_polling()

# ✅ FIX FOR COLAB: Prevent event loop error
nest_asyncio.apply()

# ✅ Run bot in Google Colab
await main()
