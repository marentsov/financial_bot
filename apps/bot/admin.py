from django.contrib import admin
from .models import TelegramUser, ExpenseRequest


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'full_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('telegram_id', 'username', 'full_name')
    readonly_fields = ('telegram_id', 'username', 'created_at')

    fieldsets = (
        (None, {
            'fields': ('telegram_id', 'username')
        }),
        ('Информация', {
            'fields': ('full_name', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )


@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__telegram_id', 'user__full_name', 'justification')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_requests', 'reject_requests']

    fieldsets = (
        (None, {
            'fields': ('user', 'status')
        }),
        ('Детали заявки', {
            'fields': ('amount', 'justification', 'receipt_photo', 'admin_comment')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def approve_requests(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} заявок одобрено.")

    approve_requests.short_description = "Одобрить выбранные заявки"

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} заявок отклонено.")

    reject_requests.short_description = "Отклонить выбранные заявки"