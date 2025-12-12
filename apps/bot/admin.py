from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
import base64
from .models import TelegramUser, ExpenseRequest, MoneyRequest


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'telegram_button', 'username', 'full_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('telegram_id', 'username', 'full_name')
    readonly_fields = ('telegram_id', 'username', 'created_at', 'telegram_button_readonly')

    fieldsets = (
        (None, {
            'fields': ('telegram_id', 'username')
        }),
        ('Информация', {
            'fields': ('full_name', 'is_active', 'admin_comment')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )

    def telegram_button(self, obj):
        """Умная кнопка для Telegram"""
        if obj.username:
            # Если есть username - прямая ссылка
            url = f"https://t.me/{obj.username}"
            text = f"@{obj.username}"
            title = "Открыть в Telegram"
        else:
            #
            url = f"tg://search"
            text = f"TG"
            title = ""

        return format_html(
            '<a href="{}" target="_blank" title="{}" style="display: inline-block; padding: 4px 12px; background: #0088cc; color: white; border-radius: 4px; text-decoration: none; font-size: 12px;">'
            '{}'
            '</a>',
            url, title, text
        )

    telegram_button.short_description = "Telegram"

    def telegram_button_readonly(self, obj):
        """Кнопка для поля только для чтения"""
        return self.telegram_button(obj)

    telegram_button_readonly.short_description = "Ссылка на Telegram"

@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at', 'receipt_preview')
    list_filter = ('status', 'created_at')
    search_fields = ('user__telegram_id', 'user__full_name', 'justification')
    readonly_fields = ('created_at', 'updated_at', 'receipt_display')
    actions = ['approve_requests', 'reject_requests']

    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'admin_comment')
        }),
        ('Детали заявки', {
            'fields': ('amount', 'justification')
        }),
        ('Чек', {
            'fields': ('receipt_display',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def receipt_preview(self, obj):
        """Миниатюра чека в списке"""
        if obj.receipt_photo:
            try:
                # Проверяем что это байты, а не строка
                if isinstance(obj.receipt_photo, str):
                    photo_bytes = obj.receipt_photo.encode('utf-8')
                else:
                    photo_bytes = obj.receipt_photo

                b64_data = base64.b64encode(photo_bytes).decode('utf-8')
                return format_html(
                    '<a href="/admin/bot/expenserequest/{}/receipt/" target="_blank" title="Открыть чек">'
                    '<img src="data:{};base64,{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />'
                    '</a>',
                    obj.id, obj.receipt_photo_content_type, b64_data[:500]  # Обрезаем для превью
                )
            except Exception as e:
                return f"Ошибка: {e}"
        return "Нет фото"

    receipt_preview.short_description = "Чек"

    def receipt_display(self, obj):
        """Отображение чека в форме редактирования"""
        if obj.receipt_photo:
            try:
                # Проверяем что это байты, а не строка
                if isinstance(obj.receipt_photo, str):
                    photo_bytes = obj.receipt_photo.encode('utf-8')
                else:
                    photo_bytes = obj.receipt_photo

                b64_data = base64.b64encode(photo_bytes).decode('utf-8')
                return format_html(
                    '<div style="margin-bottom: 20px;">'
                    '<h4>Фотография чека:</h4>'
                    '<img src="data:{};base64,{}" style="max-width: 100%; max-height: 500px; border: 1px solid #ddd; border-radius: 8px;" />'
                    '<p><a href="/admin/bot/expenserequest/{}/receipt/" target="_blank" style="margin-top: 10px; display: inline-block;">'
                    '📎 Открыть в полном размере</a></p>'
                    '<p><small>Размер: {} KB | Тип: {} | Имя: {}</small></p>'
                    '</div>',
                    obj.receipt_photo_content_type, b64_data,
                    obj.id,
                    len(photo_bytes) // 1024,
                    obj.receipt_photo_content_type,
                    obj.receipt_photo_name
                )
            except Exception as e:
                return format_html(
                    '<div style="color: red;">Ошибка отображения фото: {}</div>',
                    e
                )
        return "Фотография чека не загружена"

    receipt_display.short_description = "Предпросмотр чека"

    def get_urls(self):
        """Добавляем endpoint для скачивания чека"""
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/receipt/', self.admin_site.admin_view(self.download_receipt),
                 name='expenserequest_receipt'),
        ]
        return custom_urls + urls

    def download_receipt(self, request, object_id):
        """Endpoint для скачивания чека"""
        try:
            expense = ExpenseRequest.objects.get(id=object_id)

            # Проверяем тип данных
            if isinstance(expense.receipt_photo, str):
                photo_data = expense.receipt_photo.encode('utf-8')
            else:
                photo_data = expense.receipt_photo

            response = HttpResponse(photo_data, content_type=expense.receipt_photo_content_type)
            response['Content-Disposition'] = f'inline; filename="{expense.receipt_photo_name}"'
            return response
        except Exception as e:
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound(f"Ошибка: {e}")

    def approve_requests(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} заявок одобрено.")

    approve_requests.short_description = "Одобрить выбранные заявки"

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} заявок отклонено.")

    reject_requests.short_description = "Отклонить выбранные заявки"


@admin.register(MoneyRequest)
class MoneyRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__telegram_id', 'user__full_name', 'justification')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_requests', 'reject_requests']

    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'admin_comment')
        }),
        ('Детали запроса', {
            'fields': ('amount', 'justification')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


    def approve_money_requests(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} запросов одобрено.")

    approve_money_requests.short_description = "Одобрить выбранные запросы"

    def reject_money_requests(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} запросов отклонено.")

    reject_money_requests.short_description = "Отклонить выбранные запросы"