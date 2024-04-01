from tortoise import fields
from core.base_model import AbstractBaseModel, TimestampMixin, UserMixin


class Supplier(AbstractBaseModel):
    """
    供应商管理
    """
    company_code = fields.CharField(32, description="公司代码")
    company_name = fields.CharField(128, description="公司名称")
    short_name = fields.CharField(32, description="简称")
    country = fields.CharField(32, description="国家")
    province = fields.CharField(16, description="省份")
    city = fields.CharField(16, description="城市")
    address = fields.TextField()
    is_forbidden = fields.IntField(default=0)
    legal_person = fields.CharField(128, description="法人")
    contract_person = fields.CharField(32, description="联系人")
    contract_phone = fields.CharField(32, description="联系电话")
    is_disable = fields.IntField(default=0)
    is_supplier = fields.IntField(default=0)

    def __str__(self):
        return self.short_name

    def to_dict(self):
        return dict(self)

    async def create_or_update(self, args):
        if args.get("id"):
            supplier = await Supplier.filter(id=args.get("id")).update(
                company_code=args.get("company_code"),
                company_name=args.get("company_name"),
                short_name=args.get("short_name"),
                country=args.get("country"),
                province=args.get("province"),
                city=args.get("city"),
                address=args.get("address"),
                legal_person=args.get("legal_person"),
                contract_person=args.get("contract_person"),
                contract_phone=args.get("contract_phone")
                )
        else:
            supplier = await Supplier.create(
                company_code=args.get("company_code"),
                company_name=args.get("company_name"),
                short_name=args.get("short_name"),
                country=args.get("country"),
                province=args.get("province"),
                city=args.get("city"),
                address=args.get("address"),
                legal_person=args.get("legal_person"),
                contract_person=args.get("contract_person"),
                contract_phone=args.get("contract_phone")
            )

        return supplier

    async def disable_or_not(self, args):
        if args.get("id"):
            supplier = await Supplier.filter(id=args.get("id")).update(is_forbidden=args.get("is_forbidden"))
        return

    class Meta:
        table = "company_base_info"


class Material(AbstractBaseModel):
    """
    物料主数据
    """
    part_num = fields.CharField(32)
    mate_model = fields.CharField(32)
    mate_desc = fields.CharField(64)
    spec_size = fields.CharField(64)
    spec_weight = fields.CharField(16)
    spec_min_qty = fields.CharField(16)
    spec_max_qty = fields.CharField(16)
    mate_type = fields.CharField(16)
    purchase_type = fields.CharField(16)
    purchase_cycle = fields.CharField(16)
    safety_stock = fields.CharField(16)
    safety_lower = fields.CharField(16)
    is_forbidden = fields.IntField(default=0)

    def __str__(self):
        return self.part_num

    def to_dict(self):
        return dict(self)

    async def create_or_update(self, args):
        if args.get("id"):
            mate = await Material.filter(id=args.get("id")).update(
                part_num=args.get("part_num"),
                mate_model=args.get("mate_model"),
                mate_desc=args.get("mate_desc"),
                spec_size=args.get("spec_size"),
                spec_weight=args.get("spec_weight"),
                spec_min_qty=args.get("spec_min_qty"),
                spec_max_qty=args.get("spec_max_qty"),
                mate_type=args.get("mate_type"),
                purchase_type=args.get("purchase_type"),
                purchase_cycle=args.get("purchase_cycle"),
                safety_stock=args.get("safety_stock"),
                safety_lower=args.get("safety_lower")
                )
        else:
            mate = await Material.create(
                part_num=args.get("part_num"),
                mate_model=args.get("mate_model"),
                mate_desc=args.get("mate_desc"),
                spec_size=args.get("spec_size"),
                spec_weight=args.get("spec_weight"),
                spec_min_qty=args.get("spec_min_qty"),
                spec_max_qty=args.get("spec_max_qty"),
                mate_type=args.get("mate_type"),
                purchase_type=args.get("purchase_type"),
                purchase_cycle=args.get("purchase_cycle"),
                safety_stock=args.get("safety_stock"),
                safety_lower=args.get("safety_lower")
            )

        return mate

    async def disable_or_not(self, args):
        if args.get("id"):
            supplier = await Material.filter(id=args.get("id")).update(is_forbidden=args.get("is_forbidden"))
        return

    class Meta:
        table = "material_base_info"


class BOM(AbstractBaseModel):
    """
    BOM
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
    primary_inner_id = fields.CharField(32)
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


class PoList(AbstractBaseModel):
    po_code = fields.CharField(32)
    supplier_code = fields.CharField(32)
    supplier_name = fields.CharField(32)
    delivery_time = fields.DatetimeField(null=True)
    commit_time = fields.DatetimeField(null=True)
    is_disable = fields.IntField(default=0)

    def __str__(self):
        return self.po_code

    class Meta:
        table = "po_info_primary"


class PoDetail(AbstractBaseModel):
    po_list_id = fields.CharField(32)
    serial_num = fields.CharField(32)
    part_num = fields.CharField(32)
    unit_price = fields.CharField(32)
    qty = fields.CharField(32)
    total_price = fields.CharField(64)

    def __str__(self):
        return self.part_num

    class Meta:
        table = "po_info_detail"


class Order(AbstractBaseModel):
    sales_order_code = fields.CharField(32)
    contract_code = fields.CharField(32)
    customer_code = fields.CharField(32)
    customer_name = fields.CharField(32)
    finally_customer_code = fields.CharField(32)
    finally_customer_name = fields.CharField(32)
    delivery_time = fields.DatetimeField(null=True)
    commit_time = fields.DatetimeField(null=True)
    is_disable = fields.IntField(default=0)

    def __str__(self):
        return self.sales_order_code

    class Meta:
        table = "sales_order_primary"


class OrderDetail(AbstractBaseModel):
    order_id = fields.CharField(32)
    serial_num = fields.CharField(32)
    part_num = fields.CharField(32)
    mate_model = fields.CharField(32)
    mate_desc = fields.CharField(128)
    qty = fields.CharField(32)
    unit_name = fields.CharField(16)
    remark = fields.CharField(64)

    def __str__(self):
        return self.product_model

    class Meta:
        table = "sales_order_detail"


class DeliveryOrder(AbstractBaseModel):
    delivery_order_code = fields.CharField(64)
    customer_name = fields.CharField(32)
    sales_order_code = fields.CharField(64)
    driver_name = fields.CharField(32)
    car_number = fields.CharField(32)
    tel = fields.CharField(32)
    create_time = fields.DatetimeField(null=True)
    create_user = fields.CharField(32)

    def __str__(self):
        return self.delivery_order_code

    class Meta:
        table = "delivery_order_primary"


class DeliverayOrderDetail(AbstractBaseModel):
    deliver_order_id = fields.CharField(32)
    shelf_sn = fields.CharField(32)
    part_num = fields.CharField(32)
    mate_model = fields.CharField(32)
    mate_desc = fields.CharField(128)
    qty = fields.CharField(32)

    def __str__(self):
        return self.part_num

    class Meta:
        table = "delivery_order_detail"
