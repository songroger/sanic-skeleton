from tortoise import fields
from core.base_model import AbstractBaseModel



class MachineTestSummary(AbstractBaseModel):
    """
    整机测试结果主表
    """
    record_test_id = fields.CharField(max_length=36, description="测试ID")
    record_shelf_sn = fields.CharField(36, description="设备SN")
    record_test_strategy = fields.CharField(36, description="测试方案名称")
    record_created_by = fields.CharField(36, description="测试流程创建人")
    record_created_time = fields.CharField(36, description="测试流程创建时间")
    record_customer_code = fields.CharField(36, description="客户")
    record_purchase_code = fields.CharField(36, description="采购单号")
    record_result = fields.IntField(description="测试结果")
    record_deleted = fields.IntField(description="软删除")

    def __str__(self):
        return self.record_test_id

    def to_dict(self):
        return dict(self)
    
    class Meta:
        table = "machine_test_summary"


class MachineTestRecord(AbstractBaseModel):
    """
    整机测试记录详情表
    """
    record_created_by = fields.CharField(36, description="测试人")
    record_created_time = fields.CharField(36, description="测试时间")
    record_test_id = fields.CharField(36, description="测试ID")
    record_detail_id = fields.IntField(description="测试结果详情ID")
    record_item_name = fields.CharField(36, description="测试项名称")
    record_result = fields.CharField(36, description="测试结果")
    record_deleted = fields.IntField(description="软删除")
    record_pass_comment = fields.TextField(description="测试OK记录", null=True)
    record_pass_comment_img = fields.TextField(description="测试OK图片记录", null=True)
    record_ng_comment = fields.TextField(description="测试NG记录", null=True)
    record_ng_comment_img = fields.TextField(description="测试NG图片记录", null=True)

    def __str__(self):
        return self.id

    def to_dict(self):
        return dict(self)
    
    class Meta:
        table = "machine_test_record"


class PCBATestSummary(AbstractBaseModel):
    """
    PCBA测试结果主表
    """
    record_test_id = fields.CharField(max_length=36, description="测试ID")
    record_sn = fields.CharField(36, description="设备SN")
    record_created_by = fields.CharField(36, description="测试流程创建人")
    record_created_time = fields.CharField(36, description="测试流程创建时间")
    record_purchase_code = fields.CharField(36, description="采购单号")
    record_result = fields.IntField(description="测试结果")
    record_deleted = fields.IntField(description="软删除", default=0)

    def __str__(self):
        return self.record_test_id

    def to_dict(self):
        return dict(self)
    
    class Meta:
        table = "pcba_test_summary"


class PCBATestRecord(AbstractBaseModel):
    """
    整机测试记录详情表
    """
    record_created_by = fields.CharField(36, description="测试人")
    record_created_time = fields.CharField(36, description="测试时间")
    record_test_id = fields.CharField(36, description="测试ID")
    record_detail_id = fields.IntField(description="测试结果详情ID")
    record_item_name = fields.CharField(36, description="测试项名称")
    record_deleted = fields.IntField(description="软删除")
    record_result = fields.CharField(36, description="测试结果")
    record_result_comment = fields.TextField(description="测试结果备注", null=True)

    def __str__(self):
        return self.id

    def to_dict(self):
        return dict(self)
    
    class Meta:
        table = "pcba_test_record"

