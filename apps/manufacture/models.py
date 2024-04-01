from tortoise import fields
from core.base_model import AbstractBaseModel, TimestampMixin, UserMixin


class Supplier(AbstractBaseModel):
    sp_code = fields.CharField(16)
    name = fields.CharField(32)
    short_name = fields.CharField(32)
    country = fields.CharField(16)
    province = fields.CharField(16)
    city = fields.CharField(16)

    def __str__(self):
        return self.name

    class Meta:
        table = "factory_supplier"
