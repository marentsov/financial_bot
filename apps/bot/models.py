from django.db import models


class TelegramUser(models.Model):
    """модель пользователя в тг"""
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name="Имя пользователя")
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Полное имя")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    admin_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий финансиста")

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"

    def __str__(self):
        if self.full_name:
            return f"{self.full_name} (@{self.username})" if self.username else self.full_name
        return f"ID: {self.telegram_id}"


class ExpenseRequest(models.Model):
    """модель заявки на возмещение расходов"""
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('approved', 'Одобрена'),
        ('paid', 'Выплачена'),
        ('rejected', 'Отклонена'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    justification = models.TextField(verbose_name="Обоснование")
    receipt_photo = models.BinaryField(verbose_name="Фото чека")
    receipt_photo_name = models.CharField(max_length=255, verbose_name="Имя файла")
    receipt_photo_content_type = models.CharField(max_length=100, default='image/jpeg', verbose_name="Тип файла")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    admin_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий финансиста")

    class Meta:
        verbose_name = "Заявка на возмещение"
        verbose_name_plural = "Заявки на возмещение"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка #{self.id} от {self.user} - {self.amount} руб."


class MoneyRequest(models.Model):
    """модель запросов денежных средств"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('approved', 'Одобрен'),
        ('paid', 'Выплачен'),
        ('rejected', 'Отклонен'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    justification = models.TextField(verbose_name="Обоснование")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    admin_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий финансиста")

    class Meta:
        verbose_name = "Запрос денежных средств"
        verbose_name_plural = "Запросы денежных средств"
        ordering = ['-created_at']

    def __str__(self):
        return f"Запрос #{self.id} от {self.user} - {self.amount} руб."