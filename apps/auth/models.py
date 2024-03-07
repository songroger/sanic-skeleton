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


class FactoryRecord(AbstractBaseModel, TimestampMixin, UserMixin):
    test_id = fields.UUIDField()
    shelf_sn = fields.CharField(32)
    test_case_category_one = fields.CharField(10)
    test_case_category_two = fields.CharField(10)
    test_case_result = fields.CharField(10)
    test_case_comment = fields.TextField()
    test_case_result_image_path = fields.JSONField()
    test_case_ng_image_path = fields.JSONField()
    is_deleted = fields.IntField()
    test_case_ng_comment = fields.TextField()
    test_case_name = fields.CharField(64)

    def __str__(self):
        return self.test_case_name

    class Meta:
        table = "factory_test_record"


class FactoryTestSum(AbstractBaseModel, TimestampMixin, UserMixin):

    test_id = fields.UUIDField()
    test_strategy = fields.CharField(32)
    shelf_sn = fields.CharField(20)
    shelf_name = fields.CharField(32)
    shelf_type = fields.CharField(32)
    customer_name = fields.CharField(32)
    order_id = fields.CharField(32)
    test_case_result = fields.CharField(10, default="0")
    is_deleted = fields.IntField(default=0)

    def __str__(self):
        return self.test_strategy

    class Meta:
        table = "factory_test_summary"


class FactoryTestCase(AbstractBaseModel, TimestampMixin, UserMixin):

    test_strategy = fields.CharField(32)
    test_case_category_one = fields.CharField(10)
    test_case_category_two = fields.CharField(10)
    test_case_name = fields.CharField(64)
    test_case_des = fields.TextField()
    test_case_image_path = fields.JSONField()
    is_disable = fields.IntField()
    frontend_index = fields.CharField(32)
    is_deleted = fields.IntField()

    def __str__(self):
        return self.test_case_name

    class Meta:
        table = "factory_test_case"


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
