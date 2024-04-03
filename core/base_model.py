from tortoise import Model, fields


class AbstractBaseModel(Model):
    id = fields.IntField(pk=True)

    class Meta:
        abstract = True


class TimestampMixin():
    created_time = fields.DatetimeField(null=True, auto_now_add=True)
    updated_time = fields.DatetimeField(null=True, auto_now=True)


class UserMixin():
    created_by = fields.CharField(32, null=True)
    updated_by = fields.CharField(32, null=True)
