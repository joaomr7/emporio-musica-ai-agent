from tortoise import migrations
from tortoise.migrations import operations as ops

class Migration(migrations.Migration):
    dependencies = [('models', '0003_product_search_index')]

    initial = False

    operations = [
        ops.RunSQL(
            sql='''
                ALTER TABLE product_search_index
                ALTER COLUMN embedding TYPE VECTOR(1024)
            ''',
            reverse_sql='''
                ALTER TABLE product_search_index
                ALTER COLUMN embedding TYPE VECTOR(384)
            '''
        )
    ]
