from tortoise import migrations
from tortoise.migrations import operations as ops
from backend.search.fields import VectorField
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0002_add_session_models')]

    initial = False

    operations = [
        ops.CreateModel(
            name='ProductSearchIndex',
            fields=[
                ('product', fields.OneToOneField('models.Product', source_field='product_id', primary_key=True, db_index=True, db_constraint=True, to_field='product_id', related_name='search_index', on_delete=OnDelete.CASCADE)),
                ('search_text', fields.TextField(unique=False)),
                ('embedding', VectorField(generated=False, null=False, unique=False)),
                ('content_hash', fields.CharField(max_length=64)),
                ('model_version', fields.CharField(max_length=128)),
                ('indexed_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'product_search_index', 'app': 'models', 'pk_attr': 'product_id'},
            bases=['Model'],
        ),
    ]
