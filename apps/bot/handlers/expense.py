from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from financial_bot.apps.bot.models import TelegramUser, ExpenseRequest
import os
from django.conf import settings

from financial_bot.apps.bot.handlers.start import START_MENU

# Состояния для ConversationHandler
AMOUNT, JUSTIFICATION, RECEIPT = range(1, 4)


async def new_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания новой заявки"""
    await update.message.reply_text(
        "📤 <b>Новая заявка на возмещение</b>\n\n"
        "Шаг 1 из 3\n"
        "Введите сумму расхода в рублях:",
        parse_mode='HTML'
    )
    return AMOUNT


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение суммы"""
    try:
        amount = float(update.message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError

        context.user_data['amount'] = amount
        await update.message.reply_text(
            "Шаг 2 из 3\n"
            "Введите обоснование расхода:\n"
            "<i>Например: Удлинитель в 305 кабинет</i>",
            parse_mode='HTML'
        )
        return JUSTIFICATION
    except ValueError:
        await update.message.reply_text(
            "Неверный формат суммы!\n"
            "Введите число (например: 1500 или 1500.50):"
        )
        return AMOUNT


async def get_justification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение обоснования"""
    justification = update.message.text
    if len(justification) < 3:
        await update.message.reply_text("Слишком короткое обоснование. Попробуйте еще раз:")
        return JUSTIFICATION

    context.user_data['justification'] = justification
    await update.message.reply_text(
        "Шаг 3 из 3\n"
        "Пришлите фото чека:"
    )
    return RECEIPT


async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение фото чека и сохранение заявки"""
    user = update.effective_user

    try:
        # Получаем фото
        photo_file = await update.message.photo[-1].get_file()

        # Создаем директорию для чеков
        receipts_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
        os.makedirs(receipts_dir, exist_ok=True)

        # Генерируем имя файла
        file_name = f"receipt_{user.id}_{update.message.date.strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = os.path.join(receipts_dir, file_name)

        # Скачиваем файл
        await photo_file.download_to_drive(file_path)

        # Получаем пользователя
        tg_user = TelegramUser.objects.get(telegram_id=user.id)

        # Создаем заявку
        expense = ExpenseRequest.objects.create(
            user=tg_user,
            amount=context.user_data['amount'],
            justification=context.user_data['justification'],
            receipt_photo=f'receipts/{file_name}',
            status='new'
        )

        # Очищаем временные данные
        context.user_data.clear()

        # Отправляем подтверждение
        success_text = (
            f" <b>Заявка #{expense.id} создана!</b>\n\n"
            f" Сумма: {expense.amount} руб.\n"
            f" Обоснование: {expense.justification}\n"
            f" Дата: {expense.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f" Статус:  Новая\n\n"
            f" Финансист рассмотрит вашу заявку в ближайшее время."
        )

        await update.message.reply_text(
            success_text,
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup([['Новая заявка', 'Мои заявки']], resize_keyboard=True)
        )

        # Уведомление для админа (опционально)
        # await notify_admin(expense)

    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        await update.message.reply_text(
            "Произошла ошибка при создании заявки. Попробуйте еще раз.",
            reply_markup=ReplyKeyboardMarkup([['Новая заявка', 'Мои заявки']], resize_keyboard=True)
        )

    return START_MENU