from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0001_initial')]

    initial = False

    operations = [
        ops.CreateModel(
            name='Session',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('customer', fields.ForeignKeyField('models.Customer', source_field='customer_id', db_constraint=True, to_field='customer_id', related_name='sessions', on_delete=OnDelete.CASCADE)),
                ('status', fields.CharField(default='active', max_length=30)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
                ('closed_at', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
            ],
            options={'table': 'sessions', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='ProcessingTask',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('session', fields.ForeignKeyField('models.Session', source_field='session_id', db_constraint=True, to_field='id', related_name='tasks', on_delete=OnDelete.CASCADE)),
                ('status', fields.CharField(default='pending', max_length=30)),
                ('scheduled_at', fields.DatetimeField(auto_now=False, auto_now_add=False)),
                ('attempts', fields.IntField(default=0)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('started_at', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('completed_at', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('error', fields.TextField(null=True, unique=False)),
            ],
            options={'table': 'processing_tasks', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Message',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('session', fields.ForeignKeyField('models.Session', source_field='session_id', db_constraint=True, to_field='id', related_name='messages', on_delete=OnDelete.CASCADE)),
                ('task', fields.ForeignKeyField('models.ProcessingTask', source_field='task_id', null=True, db_constraint=True, to_field='id', related_name='messages', on_delete=OnDelete.CASCADE)),
                ('role', fields.CharField(max_length=20)),
                ('content', fields.TextField(unique=False)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'messages', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
    ]
