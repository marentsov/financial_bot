from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.models import TelegramUser, ExpenseRequest
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

from .start import START_MENU

# Состояния для ConversationHandler
AMOUNT, JUSTIFICATION, RECEIPT = range(1, 4)


async def new_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания новой заявки"""
    await update.message.reply_text(
        "<b>Новая заявка на возмещение</b>\n\n"
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

        # Скачиваем фото в память
        photo_bytes = await photo_file.download_as_bytearray()

        # Определяем тип файла
        file_extension = photo_file.file_path.split('.')[-1].lower() if photo_file.file_path else 'jpg'
        content_type = f'image/{file_extension}' if file_extension in ['jpg', 'jpeg', 'png', 'gif'] else 'image/jpeg'

        # Генерируем имя файла
        file_name = f"receipt_{user.id}_{update.message.date.strftime('%Y%m%d_%H%M%S')}.{file_extension}"

        # Получаем пользователя
        tg_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user.id)

        # Создаем заявку с фото в БД
        expense = await sync_to_async(ExpenseRequest.objects.create)(
            user=tg_user,
            amount=context.user_data['amount'],
            justification=context.user_data['justification'],
            receipt_photo=bytes(photo_bytes),  # Сохраняем как bytes
            receipt_photo_name=file_name,
            receipt_photo_content_type=content_type,
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
            f"Статус:  Новая\n\n"
            f"Финансист рассмотрит вашу заявку в ближайшее время."
        )

        await update.message.reply_text(
            success_text,
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup([['Новая заявка', 'Мои заявки']], resize_keyboard=True)
        )

        logger.info(f"Создана новая заявка #{expense.id} от пользователя {user.id}")

    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        await update.message.reply_text(
            " Произошла ошибка при создании заявки. Попробуйте еще раз.",
            reply_markup=ReplyKeyboardMarkup([['Новая заявка', 'Мои заявки']], resize_keyboard=True)
        )

    return START_MENU