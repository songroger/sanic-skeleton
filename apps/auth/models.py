from tortoise import fields
from core.base_model import AbstractBaseModel, TimestampMixin, UserMixin


class FactoryParm(AbstractBaseModel):
    para_type = fields.CharField(32)
    para_name = fields.CharField(32)
    para_value = fields.CharField(32)
    para_description = fields.CharField(64)

    def __str__(self):
        return self.para_name

    class Meta:
        table = "factory_para_config"


class FactoryUser(AbstractBaseModel):

    create_time = fields.DatetimeField(null=True, auto_now_add=True)
    user_name = fields.CharField(32)
    user_password = fields.CharField(32)
    factory_name = fields.CharField(32)

    def __str__(self):
        return self.user_name

    class Meta:
        table = "factory_user"


class ShelfDeviceConfig(AbstractBaseModel):

    device_model = fields.CharField(128)
    screen_break = fields.IntField()
    shelf_position_count = fields.IntField()
    shelf_board_count = fields.IntField()
    shelf_board_count_a = fields.IntField()
    shelf_board_count_b = fields.IntField()
    floor_config = fields.JSONField()
    floor_count = fields.IntField()
    board_config = fields.JSONField()

    def __str__(self):
        return self.device_model

    class Meta:
        table = "shelf_device_config"
