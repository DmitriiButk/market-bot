from django.db import models


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория товаров"
        verbose_name_plural = "Категории товаров"
        ordering = ['order', 'name']


class ProductSubcategory(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField(max_length=100, verbose_name="Название подкатегории")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    class Meta:
        verbose_name = "Подкатегория товаров"
        verbose_name_plural = "Подкатегории товаров"
        ordering = ['category', 'order', 'name']


class Product(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, verbose_name="Категория")
    subcategory = models.ForeignKey(ProductSubcategory, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="Подкатегория")
    name = models.CharField(max_length=255, verbose_name="Название товара")
    description = models.TextField(verbose_name="Описание товара")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Изображение")
    active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['category', 'subcategory', 'order', 'name']


class CartItem(models.Model):
    user_id = models.BigIntegerField(verbose_name="ID пользователя")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.user_id} - {self.product.name} ({self.quantity})"

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        unique_together = ('user_id', 'product')


class UserQuestion(models.Model):
    user_id = models.PositiveBigIntegerField()
    question = models.TextField()
    answer = models.TextField(blank=True, null=True)
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Вопрос от {self.user_id}: {self.question[:50]}{'...' if len(self.question) > 50 else ''}"

    class Meta:
        verbose_name = "Вопрос пользователя"
        verbose_name_plural = "Вопросы пользователей"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_answered'], name='question_answered_idx'),
            models.Index(fields=['user_id'], name='question_user_idx'),
        ]


class Order(models.Model):
    user_id = models.BigIntegerField(verbose_name="ID пользователя")
    name = models.CharField(max_length=255, verbose_name="Имя клиента")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.TextField(verbose_name="Адрес доставки")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма заказа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнен")

    payment_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID платежа")
    payment_url = models.URLField(max_length=512, blank=True, null=True, verbose_name="URL для оплаты")
    payment_status = models.CharField(max_length=50, default="pending", verbose_name="Статус платежа")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ {self.id} от {self.created_at.strftime('%d.%m.%Y %H:%M')}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказах"

    def __str__(self):
        return f"{self.product.name} ({self.quantity} шт.)"

    @property
    def total_price(self):
        return self.price * self.quantity
