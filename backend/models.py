from tortoise import fields
from tortoise.models import Model

class Category(Model):
    category_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=150)
    description = fields.TextField(null=True)

    class Meta:
        table = 'categories'

class Product(Model):
    product_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    category = fields.ForeignKeyField('models.Category', related_name='products')
    description = fields.TextField(null=True)
    price_brl = fields.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = fields.IntField()
    status = fields.CharField(max_length=30)
    specs = fields.JSONField(null=True)
    created_at = fields.DateField()

    class Meta:
        table = 'products'

class Promotion(Model):
    promotion_id = fields.IntField(pk=True)
    product = fields.ForeignKeyField('models.Product', related_name='promotions')
    discount_percent = fields.DecimalField(max_digits=5, decimal_places=2)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=False)

    class Meta:
        table = 'promotions'

class Customer(Model):
    customer_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    phone = fields.CharField(max_length=30)
    email = fields.CharField(max_length=255)
    city = fields.CharField(max_length=150)

    class Meta:
        table = 'customers'

class Order(Model):
    order_id = fields.IntField(pk=True)
    customer = fields.ForeignKeyField('models.Customer', related_name='orders')
    order_date = fields.DateField()
    status = fields.CharField(max_length=30)
    total_brl = fields.DecimalField(max_digits=12, decimal_places=2)
    payment_method = fields.CharField(max_length=30)
    tracking_code = fields.CharField(max_length=100, null=True)
    estimated_delivery = fields.DateField(null=True)
    notes = fields.TextField(null=True)

    class Meta:
        table = 'orders'

class OrderItem(Model):
    id = fields.IntField(pk=True)
    order = fields.ForeignKeyField('models.Order', related_name='items')
    product = fields.ForeignKeyField('models.Product', related_name='order_items')
    quantity = fields.IntField()

    class Meta:
        table = 'order_items'
        unique_together = (('order', 'product'),)

class Session(Model):
    id = fields.BigIntField(pk=True)
    customer = fields.ForeignKeyField('models.Customer', related_name='sessions')
    status = fields.CharField(max_length=30, default='active')
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    closed_at = fields.DatetimeField(null=True)

    class Meta:
        table = 'sessions'

class Message(Model):
    id = fields.BigIntField(pk=True)
    session = fields.ForeignKeyField('models.Session', related_name='messages')
    task = fields.ForeignKeyField('models.ProcessingTask', related_name='messages', null=True)
    role = fields.CharField(max_length=20)
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = 'messages'

class ProcessingTask(Model):
    id = fields.BigIntField(pk=True)
    session = fields.ForeignKeyField('models.Session', related_name='tasks')
    status = fields.CharField(max_length=30, default='pending')
    scheduled_at = fields.DatetimeField()
    attempts = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    error = fields.TextField(null=True)

    class Meta:
        table = 'processing_tasks'