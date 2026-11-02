from tortoise.fields import Field

class VectorField(Field[str]):
    SQL_TYPE = 'VECTOR(1024)'
    field_type = str