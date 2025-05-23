from django.contrib import admin
from .models import Product, UserQuestion, ProductCategory, ProductSubcategory, \
    CartItem, Order, OrderItem


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'active')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(ProductSubcategory)
class ProductSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order', 'active')
    list_filter = ('active', 'category')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subcategory', 'price', 'active')
    list_filter = ('active', 'category', 'subcategory')
    search_fields = ('name', 'description')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'product', 'quantity', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user_id', 'product__name')


@admin.register(UserQuestion)
class UserQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'question', 'is_answered', 'created_at')
    search_fields = ('user_id', 'question')
    list_filter = ('is_answered', 'created_at')

    def save_model(self, request, obj, form, change):
        # Если есть ответ, автоматически устанавливаем флаг is_answered
        if obj.answer and obj.answer.strip():
            obj.is_answered = True
        super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'total_amount', 'created_at', 'is_completed']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['name', 'phone', 'address']
    readonly_fields = ['user_id', 'name', 'phone', 'address', 'total_amount', 'created_at']
    inlines = [OrderItemInline]
