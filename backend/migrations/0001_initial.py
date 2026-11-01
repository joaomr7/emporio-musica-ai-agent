from tortoise import migrations
from tortoise.migrations import operations as ops
import functools
from json import dumps, loads
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Category',
            fields=[
                ('category_id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('name', fields.CharField(max_length=150)),
                ('description', fields.TextField(null=True, unique=False)),
            ],
            options={'table': 'categories', 'app': 'models', 'pk_attr': 'category_id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Customer',
            fields=[
                ('customer_id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('name', fields.CharField(max_length=255)),
                ('phone', fields.CharField(max_length=30)),
                ('email', fields.CharField(max_length=255)),
                ('city', fields.CharField(max_length=150)),
            ],
            options={'table': 'customers', 'app': 'models', 'pk_attr': 'customer_id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Order',
            fields=[
                ('order_id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('customer', fields.ForeignKeyField('models.Customer', source_field='customer_id', db_constraint=True, to_field='customer_id', related_name='orders', on_delete=OnDelete.CASCADE)),
                ('order_date', fields.DateField()),
                ('status', fields.CharField(max_length=30)),
                ('total_brl', fields.DecimalField(max_digits=12, decimal_places=2)),
                ('payment_method', fields.CharField(max_length=30)),
                ('tracking_code', fields.CharField(null=True, max_length=100)),
                ('estimated_delivery', fields.DateField(null=True)),
                ('notes', fields.TextField(null=True, unique=False)),
            ],
            options={'table': 'orders', 'app': 'models', 'pk_attr': 'order_id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Product',
            fields=[
                ('product_id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('name', fields.CharField(max_length=255)),
                ('category', fields.ForeignKeyField('models.Category', source_field='category_id', db_constraint=True, to_field='category_id', related_name='products', on_delete=OnDelete.CASCADE)),
                ('description', fields.TextField(null=True, unique=False)),
                ('price_brl', fields.DecimalField(max_digits=12, decimal_places=2)),
                ('stock_quantity', fields.IntField()),
                ('status', fields.CharField(max_length=30)),
                ('specs', fields.JSONField(null=True, encoder=functools.partial(dumps, separators=(',', ':')), decoder=loads)),
                ('created_at', fields.DateField()),
            ],
            options={'table': 'products', 'app': 'models', 'pk_attr': 'product_id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='OrderItem',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('order', fields.ForeignKeyField('models.Order', source_field='order_id', db_constraint=True, to_field='order_id', related_name='items', on_delete=OnDelete.CASCADE)),
                ('product', fields.ForeignKeyField('models.Product', source_field='product_id', db_constraint=True, to_field='product_id', related_name='order_items', on_delete=OnDelete.CASCADE)),
                ('quantity', fields.IntField()),
            ],
            options={'table': 'order_items', 'app': 'models', 'unique_together': (('order', 'product'),), 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Promotion',
            fields=[
                ('promotion_id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('product', fields.ForeignKeyField('models.Product', source_field='product_id', db_constraint=True, to_field='product_id', related_name='promotions', on_delete=OnDelete.CASCADE)),
                ('discount_percent', fields.DecimalField(max_digits=5, decimal_places=2)),
                ('description', fields.TextField(null=True, unique=False)),
                ('is_active', fields.BooleanField(default=False)),
            ],
            options={'table': 'promotions', 'app': 'models', 'pk_attr': 'promotion_id'},
            bases=['Model'],
        ),
    ]
