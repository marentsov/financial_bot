from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.models import TelegramUser, MoneyRequest
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

from .start import START_MENU

# Состояния для ConversationHandler
AMOUNT, JUSTIFICATION = range(1, 3)

async def new_request_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания новой заявки"""
    await update.message.reply_text(
        "<b>Новый запрос денежных средств</b>\n\n"
        "Шаг 1 из 2\n"
        "Введите необходимую сумму в рублях:",
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
            "Шаг 2 из 2\n"
            "Введите обоснование запроса:\n"
            "<i>Например: необходимо заправить машину</i>",
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
    """Получение обоснования и сохранение заявки"""
    user = update.effective_user
    try:
        justification = update.message.text
        if len(justification) < 3:
            await update.message.reply_text("Слишком короткое обоснование. Попробуйте еще раз:")
            return JUSTIFICATION

        # Получаем пользователя
        tg_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user.id)

        request = await sync_to_async(MoneyRequest.objects.create)(
            user=tg_user,
            amount=context.user_data['amount'],
            justification=justification,
            status='new'
        )

        # Очищаем временные данные
        context.user_data.clear()

        # Отправляем подтверждение
        success_text = (
            f" <b>Запрос #{request.id} создан!</b>\n\n"
            f" Сумма: {request.amount} руб.\n"
            f" Обоснование: {request.justification}\n"
            f" Дата: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Статус:  Новый\n\n"
            f"Финансист рассмотрит ваш запрос в ближайшее время."
        )

        await update.message.reply_text(
            success_text,
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup([['Новая заявка', 'Мои заявки', 'Новый запрос', 'Мои запросы']], resize_keyboard=True)
        )

        logger.info(f"Создан новый запрос #{request.id} от пользователя {user.id}")

    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        await update.message.reply_text(
            " Произошла ошибка при создании запроса. Попробуйте еще раз.",
            reply_markup=ReplyKeyboardMarkup([['Новая заявка', 'Мои заявки', 'Новый запрос', 'Мои запросы']], resize_keyboard=True)
        )

    return START_MENU


