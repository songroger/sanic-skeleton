import json
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


class SisUserGroup(AbstractBaseModel):

    group_name = fields.CharField(32)
    group_power = fields.CharField(32)

    def __str__(self):
        return self.group_name

    def to_dict(self):
        return {
            "id": self.id,
            "group_name": self.group_name,
            "group_power": self.group_power
        }

    class Meta:
        table = "sis_user_group"


class SisUser(AbstractBaseModel, TimestampMixin):

    user_group = fields.ForeignKeyField('models.SisUserGroup', 'groups')
    user_name = fields.CharField(32)
    user_password = fields.CharField(32)
    menu_id = fields.TextField(null=True, description="菜单权限")

    def __str__(self):
        return self.user_name

    def _parse_menu_id(self, m):
        return m.strip("[]").split(',') if m else []

    def to_dict(self):
        return {
            "id": self.id,
            "user_group": self.user_group.to_dict(),
            "user_name": self.user_name,
            "menu_id": self._parse_menu_id(self.menu_id),
            "create_time": self.created_time.strftime("%Y-%m-%d %X")
        }

    async def create_or_update(self, args):
        if args.get("id"):
            sid = args.pop("id")
            user = await SisUser.filter(id=sid).update(**args)

        else:
            user = await SisUser.create(**args)

        return user

    async def delete(self, args):
        if args.get("id"):
            _ = await Supplier.filter(id=args.get("id")).update(is_forbidden=args.get("is_forbidden"))
        return

    class Meta:
        table = "sis_user"

