from tortoise import fields
from core.base_model import AbstractBaseModel, TimestampMixin, UserMixin


class Supplier(AbstractBaseModel):
    """
    供应商管理
    """
    company_code = fields.CharField(32, description="公司代码")
    company_name = fields.CharField(128, description="公司名称")
    short_name = fields.CharField(32, description="简称")
    area = fields.TextField(description="国家/地区")
    address = fields.TextField()
    is_forbidden = fields.IntField(default=0)
    legal_person = fields.CharField(128, description="法人")
    contract_person = fields.CharField(32, description="联系人")
    contract_phone = fields.CharField(32, description="联系电话")
    is_disable = fields.IntField(default=0)
    identity = fields.IntField(description='0供应商;1客户')

    def __str__(self):
        return self.short_name

    def to_dict(self):
        return dict(self)

    async def create_or_update(self, args):
        if args.get("id"):
            sid = args.pop("id")
            supplier = await Supplier.filter(id=sid).update(**args)

        else:
            supplier = await Supplier.create(**args)

        return supplier

    async def disable_or_not(self, args):
        if args.get("id"):
            _ = await Supplier.filter(id=args.get("id")).update(is_forbidden=args.get("is_forbidden"))
        return

    class Meta:
        table = "company_base_info"


class Material(AbstractBaseModel):
    """
    物料主数据
    """
    part_num = fields.CharField(32)
    mate_model = fields.CharField(32, description="物料型号")
    mate_desc = fields.CharField(64, description="物料描述")
    spec_size = fields.CharField(64, description="规格尺寸")
    spec_weight = fields.CharField(16, description="规格重量")
    spec_min_qty = fields.CharField(16, description="最小包装数")
    spec_max_qty = fields.CharField(16, description="整箱包装数")
    mate_type = fields.CharField(16, description="物料类型")
    purchase_type = fields.CharField(16, description="采购类型")
    purchase_cycle = fields.CharField(16, description="采购周期")
    safety_stock = fields.CharField(16, description="安全库存")
    safety_lower = fields.CharField(16, description="安全水位")
    is_forbidden = fields.IntField(default=0)

    def __str__(self):
        return self.part_num

    def to_dict(self):
        return dict(self)

    async def create_or_update(self, args):
        if args.get("id"):
            mid = args.pop("id")
            mate = await Material.filter(id=mid).update(**args)
        else:
            mate = await Material.create(**args)

        return mate

    async def disable_or_not(self, args):
        if args.get("id"):
            _ = await Material.filter(id=args.get("id")).update(is_forbidden=args.get("is_forbidden"))
        return

    class Meta:
        table = "material_base_info"


class BOM(AbstractBaseModel, TimestampMixin, UserMixin):
    """
    BOM:料号+版本保持唯一
    """
    part_num = fields.CharField(64)
    product_version = fields.CharField(16)
    mate_model = fields.CharField(32)
    mate_desc = fields.CharField(128)
    mate_type = fields.CharField(32)

    def __str__(self):
        return self.part_num

    def to_dict(self):
        return dict(self)

    class Meta:
        table = "bom_info_primary"


class BOMDetail(AbstractBaseModel):
    """
    BOM详情
    """
    primary_inner_id = fields.IntField()
    serial_num = fields.CharField(32)
    tier_flag = fields.CharField(16)
    part_num = fields.CharField(64)
    mate_model = fields.CharField(32)
    mate_desc = fields.CharField(128)
    mate_type = fields.CharField(32)
    unit_num = fields.CharField(16)
    unit_name = fields.CharField(16)

    def __str__(self):
        return self.part_num

    def to_dict(self):
        return dict(self)

    class Meta:
        table = "bom_info_detail"


class PoList(AbstractBaseModel, TimestampMixin, UserMixin):
    """
    采购单
    """
    po_code = fields.CharField(32, description='采购单号', unique=True)
    supplier_code = fields.CharField(32)
    supplier_name = fields.CharField(32)
    delivery_time = fields.DatetimeField(null=True)
    commit_time = fields.DatetimeField(null=True)
    is_disable = fields.IntField(default=0)

    def __str__(self):
        return self.po_code

    def to_dict(self):
        return {
            "id": self.id,
            "po_code": self.po_code,
            "supplier_code": self.supplier_code,
            "supplier_name": self.supplier_name,
            "delivery_time": self.delivery_time.strftime("%Y-%m-%d"),
            "commit_time": self.commit_time.strftime("%Y-%m-%d")
        }

    class Meta:
        table = "po_info_primary"


class PoDetail(AbstractBaseModel):
    primary_inner_id = fields.IntField()
    serial_num = fields.CharField(32)
    part_num = fields.CharField(32)
    unit_price = fields.DecimalField(max_digits=11, decimal_places=2, description='单价')
    qty = fields.IntField(description='数量')
    total_price = fields.DecimalField(max_digits=11, decimal_places=2, description='总价')

    def __str__(self):
        return self.part_num

    def to_dict(self):
        return {
            "id": self.id,
            "primary_inner_id": self.primary_inner_id,
            "part_num": self.part_num,
            "unit_price": float(self.unit_price),
            "qty": self.qty,
            "total_price": float(self.total_price)
        }

    class Meta:
        table = "po_info_detail"


class Order(AbstractBaseModel, TimestampMixin, UserMixin):
    """
    销售单
    """
    sales_order_code = fields.CharField(32, unique=True, description='销售单号')
    contract_code = fields.CharField(32, description='合同编号')
    customer_code = fields.CharField(32, description='客户代码')
    customer_name = fields.CharField(32, description='客户名称')
    finally_customer_code = fields.CharField(32)
    finally_customer_name = fields.CharField(32)
    state = fields.SmallIntField(default=0, description='状态:0新建,1出货进行中,2完结')
    delivery_time = fields.DatetimeField(null=True, description='交货时间')
    commit_time = fields.DatetimeField(null=True, description='提交时间')
    is_disable = fields.IntField(default=0)

    def __str__(self):
        return self.sales_order_code

    def to_dict(self):
        return {
            "id": self.id,
            "sales_order_code": self.sales_order_code,
            "contract_code": self.contract_code,
            "customer_code": self.customer_code,
            "delivery_time": self.delivery_time.strftime("%Y-%m-%d"),
            "commit_time": self.commit_time.strftime("%Y-%m-%d")
        }

    class Meta:
        table = "sales_order_primary"


class OrderDetail(AbstractBaseModel):
    primary_inner = fields.ForeignKeyField('models.Order', 'details')
    serial_num = fields.CharField(32)
    part_num = fields.CharField(32)
    mate_model = fields.CharField(32)
    mate_desc = fields.CharField(128)
    qty = fields.IntField()
    unit_name = fields.CharField(16, description='单位')
    remark = fields.TextField(description="备注")

    def __str__(self):
        return self.primary_inner_id

    def to_dict(self):
        return dict(self)

    class Meta:
        table = "sales_order_detail"


class DeliveryOrder(AbstractBaseModel, TimestampMixin, UserMixin):
    """
    出货单
    """
    delivery_order_code = fields.CharField(64, description='出货单号', unique=True)
    customer_name = fields.CharField(32, description='客户')
    sales_order_code = fields.CharField(64, description='销售订单号')
    driver_name = fields.CharField(32, description='司机')
    car_number = fields.CharField(32, description='车牌')
    tel = fields.CharField(32)

    def __str__(self):
        return self.delivery_order_code

    def to_dict(self):
        return dict(self)

    async def create_or_update(self, args):
        if args.get("id"):
            sid = args.pop("id")
            order = await DeliveryOrder.filter(id=sid).update(**args)

        else:
            order = await DeliveryOrder.create(**args)

        return order
    
    class Meta:
        table = "delivery_order_primary"


class DeliverayOrderDetail(AbstractBaseModel):
    primary_inner = fields.ForeignKeyField('models.DeliveryOrder', 'details')
    shelf_sn = fields.CharField(32)
    part_num = fields.CharField(32)
    mate_model = fields.CharField(32)
    mate_desc = fields.CharField(128)
    qty = fields.IntField()

    def __str__(self):
        return self.part_num

    class Meta:
        table = "delivery_order_detail"
