import logging
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

# Define component weights
weights = {
    "Lecture": 1.0,   # 100%
    "Tutorial": 0.25,  # 25%
    "Practical": 0.50, # 50%
    "Skilling": 0.25   # 25%
}

# Function to start or reset attendance
async def start_attendance(update: Update, context: CallbackContext) -> int:
    context.user_data["attendance_data"] = {}  # Reset attendance data
    context.user_data["started"] = True  # Track that the user started attendance

    reply_keyboard = [[comp] for comp in components]
    await update.message.reply_text(
        "Select a component to enter attendance (or type 'Done' when finished):",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_COMPONENT

# Function to handle component selection
async def get_component(update: Update, context: CallbackContext) -> int:
    component = update.message.text

    if component == "Done":
        return await calculate_final_attendance(update, context)  # Proceed to final calculation

    if component not in weights:
        await update.message.reply_text("Invalid component. Please select from the list.")
        return SELECT_COMPONENT

    context.user_data["current_component"] = component
    await update.message.reply_text(f"Enter attendance percentage for {component} (e.g., 75)")
    return GET_ATTENDANCE

# Function to store attendance and allow reselection
async def get_attendance(update: Update, context: CallbackContext) -> int:
    try:
        percentage = float(update.message.text)
        component = context.user_data["current_component"]
        context.user_data["attendance_data"][component] = percentage

        reply_keyboard = [[comp] for comp in components]
        await update.message.reply_text(
            "Select another component to update attendance (or type 'Done' to finish):",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return SELECT_COMPONENT

    except ValueError:
        await update.message.reply_text("Invalid input! Enter a number (e.g., 75).")
        return GET_ATTENDANCE

# Function to calculate overall weighted attendance
async def calculate_final_attendance(update: Update, context: CallbackContext) -> int:
    attendance_data = context.user_data.get("attendance_data", {})

    if not attendance_data:
        await update.message.reply_text("No attendance data provided.")
        return SELECT_COMPONENT  # Allow user to restart without typing /attendance

    total_weighted_attendance = 0
    total_weight = 0
    component_analysis = []

    for component, percentage in attendance_data.items():
        weight = weights.get(component, 0)  # Get weight, default to 0 if component is invalid
        total_weighted_attendance += percentage * weight
        total_weight += weight
        component_analysis.append(f"{component}: {percentage:.2f}%")

    if total_weight == 0:
        await update.message.reply_text("Invalid data, weights sum to zero.")
        return SELECT_COMPONENT  # Allow user to restart

    final_percentage = total_weighted_attendance / total_weight

    # Formatting result
    analysis_text = "\n".join(component_analysis)
    final_result = f"📊 **Attendance Report**\n\n{analysis_text}\n\n"
    final_result += f"📈 **Final Weighted Attendance: {final_percentage:.2f}%**\n"

    if final_percentage < 85:
        final_result += "❌ **Below 85%! Attendance is low.**"
    else:
        final_result += "✅ **Attendance is above 85%!**"

    await update.message.reply_text(final_result)

    # Reset attendance data to allow immediate reuse without needing /attendance again
    context.user_data["attendance_data"] = {}

    # Let user select components again without typing /attendance
    reply_keyboard = [[comp] for comp in components]
    await update.message.reply_text(
        "You can check attendance again by selecting a component:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

    return SELECT_COMPONENT

# Cancel function
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Attendance calculation canceled.")
    return ConversationHandler.END

# Start bot
async def main():
    BOT_TOKEN = "7544916414:AAHK5HEa_uTKD0OIop5k79U_vYqaIOEyJ1k"

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

    # Ensure the bot keeps running even after a restart
    while True:
        try:
            await app.run_polling()
        except Exception as e:
            logging.error(f"Error: {e}")
            await asyncio.sleep(5)  # Wait and retry if an error occurs

# Run bot in Google Colab
await main()
