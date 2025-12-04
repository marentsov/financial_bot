import os
import asyncio
from django.conf import settings
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from .handlers import start, expense


class ExpenseBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None

    async def init(self):
        """Инициализация бота"""
        self.application = Application.builder().token(self.token).build()

        # Обработчики
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start.start_command)],
            states={
                start.START_MENU: [
                    MessageHandler(filters.Regex('^(Новая заявка)$'), expense.new_expense_start),
                    MessageHandler(filters.Regex('^(Мои заявки)$'), start.my_requests),
                ],
                expense.AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, expense.get_amount),
                ],
                expense.JUSTIFICATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, expense.get_justification),
                ],
                expense.RECEIPT: [
                    MessageHandler(filters.PHOTO, expense.get_receipt),
                ],
            },
            fallbacks=[CommandHandler('cancel', start.cancel)],
        )

        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("help", start.help_command))

        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)

        print("Бот инициализирован!")

    async def error_handler(self, update: object, context):
        """Обработчик ошибок"""
        logger = context.bot.logger
        logger.error(f"Exception while handling an update: {context.error}")

    def run(self):
        """Запуск бота"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.init())
            loop.create_task(self.application.run_polling(allowed_updates=[]))
        else:
            loop.run_until_complete(self.init())
            self.application.run_polling()


bot = ExpenseBot()