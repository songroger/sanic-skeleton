import re
import xlrd
import datetime
from core.logger import logger
from tortoise.transactions import atomic, in_transaction
from core.base import MateTypeEnum, PurchaseTypeEnum, SalesOrderStateEnum, SupplierIdentityEnum
from typing import List, Optional
from .models import (BOM, Material, DeliveryOrderDetail, DeliveryOrder, Supplier, Order, OrderDetail,
                     PoList, PoDetail, BOMDetail)


def function():
    pass


class ComponyOperation:
    """
    客户/供应商公司信息管理操作
    """

    @classmethod
    async def getCustomerInfoByUnfinishSalesOrder(cls, sales_order_code: str = ""):
        """
        获取未完成订单的客户
        """
        # 查询未完成订单
        orders = await SalesOrderOperation.getOrderInfo(sales_order_code=sales_order_code, sales_state=SalesOrderStateEnum.Inprocess.value)
        customer_list = []
        order_map = {}
        for item in orders:
            _code = item.customer_code
            customer_list.append(_code)
            if _code in order_map:
                order_map[_code].append(item.to_dict())
            else:
                order_map[_code] = [item.to_dict()]

        # 查询订单对应的客户
        customers = await Supplier.all().filter(company_code__in=customer_list, identity=SupplierIdentityEnum.Customer.value)
        result = []
        for item in customers:
            result.append({
                "customer_code": item.company_code,
                "customer_name": item.company_name,
                "short_name": item.short_name,
                "details": order_map[item.company_code]
            })
        return result


class MaterialOperation:

    @classmethod
    async def getPartNumInfos(cls, part_num_list: Optional[List[str]] = None, mate_type: str = "", purchase_type: str = ""):
        """
        获取料号信息
        :params part_num_list: 料号列表
        :params mate_type: 物料类型
        :params purchase_type: 采购类型
        """
        query = Material
        if part_num_list:
            query = query.filter(part_num__in=part_num_list)
        if mate_type:
            query = query.filter(mate_type=mate_type)
        if purchase_type:
            query = query.filter(purchase_type=purchase_type)
        result = await query.all()

        return result


class SalesOrderOperation:
    """
    销售订单操作
    """
    @classmethod
    async def checkOrderIsFinished(cls, sales_order_code):
        """
        检查订单是否完结
        :return bool
        """
        order_info = cls.getOrderInfo(sales_order_code=sales_order_code)
        if order_info.state == SalesOrderStateEnum.FINISHED.value:
            return True
        return False

    @classmethod
    async def getOrderInfo(cls, sales_order_code: str = "", is_need_detail=False, sales_state: list = None):
        """
        获取订单信息(外键关联,获取主表信息及内容详情)
        :params sales_order_code: 订单号
        :params is_need_detail: boll 是否需要详情
        """
        order_info_sql = Order.all()
        if sales_order_code:
            order_info_sql = order_info_sql.filter(sales_order_code__contains=sales_order_code)
        if sales_state:
            order_info_sql = order_info_sql.filter(state__in=sales_state)
        if is_need_detail is True:
            order_info_sql = order_info_sql.prefetch_related("details")
        order_info = await order_info_sql
    
        return order_info

    @classmethod
    async def getLatestSurplusDemandForSalesOrder(cls, sales_order_code):
        """
        获取订单的最新剩余需求
        返回订单中,有需求的料号及剩余需求数量
        :parmas sales_order_code: 销售订单
        """
        # 1. 获取订单总需求量
        sales_info = await Order.filter(sales_order_code=sales_order_code).prefetch_related("details").first()
        if not sales_info:
            raise Exception(f"订单数据不存在!")

        # 按料号统计需求
        sales_map = {}
        for item in sales_info.details:
            qty = item.qty
            out_qty = item.out_qty
            if out_qty >= qty:
                continue
            if item.part_num in sales_map:
                sales_map[item.part_num] += (qty - out_qty)
            else:
                sales_map[item.part_num] = (qty - out_qty)

        # 返回订单有需求的料号
        return sales_map

    @classmethod
    async def updateSalesOrderStateByDelivery(cls, sales_order_code):
        """
        更新销售订单状态,实时对比出货进度,刷新订单状态
        :params sales_order_code: 销售订单号
        """
        # 查询订单对应的出货数据
        deliverys = await DeliveryOrder.filter(sales_order_code=sales_order_code).prefetch_related("details").all()
        if not deliverys:
            return
        delivery_map = {}
        # 按料号统计历史出货数据
        for item in deliverys:
            for item2 in item.details:
                pn = item2.part_num
                qty = item2.qty
                if pn in delivery_map:
                    delivery_map[pn] += qty
                else:
                    delivery_map[pn] = qty

        # 获取订单数据
        sales = await Order.filter(sales_order_code=sales_order_code).prefetch_related("details").first()
        row_state_list = []
        row_update = []
        for item in sales.details:
            pn = item.part_num
            qty = item.qty
            row_state = 0
            # 如果订单料号没有出货记录,则当前料号状态=0
            if pn in delivery_map:
                if delivery_map[pn] < qty:
                    row_state = 1
                else:
                    row_state = 2
                item.out_qty = delivery_map[pn]
                row_update.append(item)
            row_state_list.append(row_state)
        
        # 存在需要更新的需求行,将出货数量进行更新
        if row_update:
            await OrderDetail.bulk_update(row_update, fields=['out_qty'])

        if sum(row_state_list) == 0:
            state = SalesOrderStateEnum.CREATE.value
        elif sum(row_state_list) == len(row_state_list) * 2:
            state = SalesOrderStateEnum.FINISHED.value
        else:
            state = SalesOrderStateEnum.OUTING.value
        sales.state = state
        # 对比订单及出货单进度,判断最终状态
        await sales.save()

    @classmethod
    async def getInfosByOrderList(cls, sales_order_list):
        """
        获取工单信息列表
        """
        sales_order_list = list(set(sales_order_list))
        infos = await Order.filter(sales_order_code__in=sales_order_list).all()
        order_map = {}
        for info in infos:
            order_map[info.sales_order_code] = info
        return order_map


class DeliveryOrderOperation:
    """
    出货单操作
    """

    @classmethod
    async def generateDeliveryOrderCode(cls, sales_order_code):
        """
        生成出货单号
        :params sales_order_code:销售订单号
        """
        info = await Order.filter(sales_order_code=sales_order_code).first()
        customer_code = info.customer_code
        today = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # D+客户代码+时间
        code = f"D{customer_code}{today}"
        return code

    @classmethod
    async def createInfo(cls, payload):
        """
        创建出货单据(创建数据由其他流程进行校验,此函数仅负责在校验通过后,添加数据)
        """
        delivery_order_code = payload.get("delivery_order_code")
        sales_order_code = payload.get("sales_order_code")
        customer_name = payload.get("customer_name")
        driver_name = payload.get("driver_name")
        car_number = payload.get("car_number")
        tel = payload.get("tel")
        content = payload.get("content")
        
        delivery = DeliveryOrder(delivery_order_code=delivery_order_code, customer_name=customer_name, 
                                       sales_order_code=sales_order_code, driver_name=driver_name, car_number=car_number, 
                                       tel=tel)
        
        # 事务操作
        async with in_transaction():
            # 出货单主表添加
            await delivery.save()

            data = []

            # 料架sn统计
            shelf_sn_list = []
            for item in content:
                _pn = item.get("part_num")
                _model = item.get("mate_model")
                _desc = item.get("mate_desc")
                _mate_type = item.get("mate_type")
                _unit_name = item.get("unit_name")
                _purchase_type = item.get("purchase_type")
                # 设备出货，每个sn单独一条，配件类每个料号保存一条
                # 成品+生成=自产出货设备(基于SN)
                if _mate_type == MateTypeEnum.FINISHED_PRODUCT.value and _purchase_type == PurchaseTypeEnum.PRODUCT.value:
                    _sn_list = item.get("sn_list", [])
                    _qty = 1
                    shelf_sn_list += _sn_list
                else:
                    _sn_list = [""]
                    _qty = item.get("out_qty", 0)
                # 没有出货数量的,不添加
                if _qty <= 0:
                    continue

                for _sn in _sn_list:
                    data.append(DeliveryOrderDetail(shelf_sn=_sn, part_num=_pn, mate_model=_model, mate_desc=_desc, qty=_qty, primary_inner=delivery, unit_name=_unit_name))
            # 详情不能为空
            if not data:
                raise Exception("出货单内容不能为空!")
            exist_infos = await DeliveryOrderDetail.filter(shelf_sn__in=shelf_sn_list).all()
            if exist_infos:
                sn = exist_infos[0].shelf_sn
                raise Exception(f"{sn}设备已出货!无法再次扫描")
                
            # 出货单详情添加
            await DeliveryOrderDetail.bulk_create(data)
            # 更新销售单状态
            await SalesOrderOperation.updateSalesOrderStateByDelivery(sales_order_code=sales_order_code)


    @classmethod
    async def getDeliveryHistoryData(cls, delivery_order_code: str = "", sales_order_code: str = ""):
        """
        统计出货单发料数据
        :params delivery_order_code: 出货单号
        :params sales_order_code: 销售订单号
        :returns dict
        """
        query = DeliveryOrder

        if delivery_order_code:
            query = query.filter(delivery_order_code=delivery_order_code)

        if sales_order_code:
            query = query.filter(sales_order_code=sales_order_code)
        data = await query.prefetch_related("details").all()
        history_cache = {}
        if not data:
            return history_cache
        for item in data:
            for item2 in item.details:
                if item2.part_num in history_cache:
                    history_cache[item2.part_num] += item2.qty
                else:
                    history_cache[item2.part_num] = item2.qty
        return history_cache
        
    @classmethod
    async def getOrderInfo(cls, payload):
        """获取出货单信息"""
        customer_name = payload.get("customer_name")
        delivery_order_code = payload.get("delivery_order_code")

        query = DeliveryOrder
        if delivery_order_code:
            query = query.filter(delivery_order_code=delivery_order_code)
        if customer_name:
            query = query.filter(customer_name=customer_name)
        order_info = await query.prefetch_related("details").first()
        return order_info
    
    @classmethod
    async def checkHistoryByShelfSN(cls, shelf_sn: str):
        """
        查询SN是否有出货记录
        """
        data = await DeliveryOrderDetail.filter(shelf_sn=shelf_sn).first()
        return data is not None


def parseShelfTag(tag_str: str):
    """解析货架标签数据"""
    data = {
        "result": 0,
        "msg": ""
    }

    if '&' not in tag_str:
        data.update(msg="标签格式错误,未找到分隔符!")
        return data
    tag_list = tag_str.split("&")
    shelf_id = tag_list[0]
    part_num = tag_list[1]

    group = re.match(r"^(SN)?\w{3}-\w{3}-\w{3}$", shelf_id)
    if not group:
        data.update(msg="SN序列号格式错误!")
        return data

    group = re.match(r"^\w{3}-\w{3}-\w{3}$", part_num)
    if not group:
        data.update(msg="料号格式错误!")
        return data
    if not shelf_id.startswith("SN"):
        shelf_id = f"SN{shelf_id}"
    data.update(result=1, shelf_sn=shelf_id, part_num=part_num)
    return data


async def checkDiffSalesAndDelivery(sales_order_code, delivery_detail):
    # 获取订单剩余需求
    salse_cache = await SalesOrderOperation.getLatestSurplusDemandForSalesOrder(sales_order_code=sales_order_code)
    if not salse_cache:
        return  False, "订单无需求,无法进行出货单创建!"
    # 按料号统计出库单物料数量
    delivery_cache = {}
    for item in delivery_detail:
        _pn = item.get("part_num")
        sn_list = item.get("sn_list", [])
        sn_list = list(set(sn_list))
        _mate_type = item.get("mate_type")
        _purchase_type = item.get("purchase_type")
        # 设备出货，每个sn单独一条，配件类每个料号保存一条
        # 成品+生成=自产出货设备(基于SN)
        if _mate_type == MateTypeEnum.FINISHED_PRODUCT.value and _purchase_type == PurchaseTypeEnum.PRODUCT.value:
            _qty = len(sn_list)
        else:
            _qty = item.get("out_qty")
        if _pn in delivery_cache:
            delivery_cache[_pn] += _qty
        else:
            delivery_cache[_pn] = _qty

    # 检查出库单内的料号,对比订单需求
    for pn, qty in delivery_cache.items():
        if qty == 0:
            continue
        # 出货单数据的料号没有订单需求，或数量超出需求，都进行错误提示
        if pn not in salse_cache:
            return False, f"{pn}料号没有订单需求,出货单数据异常,创建失败!"
        if qty > salse_cache[pn]:
            return False, f"{pn}料号订单需求数量:{salse_cache[pn]};本次出货单数量:{qty},超出订单需求,创建失败!"
        
    return True, "success"


async def parse_mate_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    objects = []
    try:
        for i in range(1, total_rows):
            row_data = sheet_table.row_values(i)

            _exist = await Material.filter(part_num=row_data[1]).exists()
            if _exist:
                return False, f"料号{row_data[1]}已存在"

            objects.append(Material(part_num=row_data[1],
                                    mate_model=row_data[2],
                                    mate_desc=row_data[3],
                                    spec_size=row_data[4],
                                    spec_weight=row_data[5],
                                    spec_min_qty=int(row_data[6]) if isinstance(row_data[6], float) else row_data[6],
                                    spec_max_qty=int(row_data[7]) if isinstance(row_data[7], float) else row_data[7],
                                    mate_type=row_data[8],
                                    purchase_type=row_data[9],
                                    purchase_cycle=int(row_data[10]) if isinstance(row_data[10], float) else row_data[10],
                                    safety_stock=int(row_data[11]) if isinstance(row_data[11], float) else row_data[11],
                                    safety_lower=int(row_data[12]) if isinstance(row_data[12], float) else row_data[12],
                                    ))

        _ = await Material.bulk_create(objects)
        return True, ""
    except Exception as e:
        logger.info(e)
        return False, str(e)


async def parse_bom_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    try:
        async with in_transaction() as connection:
            for i in range(1, total_rows):
                row_data = sheet_table.row_values(i)
                # print(row_data)
                if row_data[0]:
                    _exist = await Material.filter(part_num=row_data[1]).exists()
                    _is_forbidden = await Material.filter(part_num=row_data[1], is_forbidden=1).exists()
                    if not _exist or _is_forbidden:
                        return False, f"料号{row_data[1]}不存在或已被禁用"

                    _bom_exists = await BOM.filter(part_num=row_data[1], product_version=row_data[2]).exists()
                    if _bom_exists:
                        return False, f"BOM：{row_data[1]}已存在"

                    bo = await BOM.create(part_num=row_data[1],
                                          product_version=row_data[2],
                                          mate_model=row_data[3],
                                          mate_desc=row_data[4],
                                          mate_type=row_data[5]
                                         )

                elif row_data[1] != "物料编码":
                    _mate_exist = await Material.filter(part_num=row_data[1]).exists()
                    _is_forbidden = await Material.filter(part_num=row_data[1], is_forbidden=1).exists()
                    if not _mate_exist or _is_forbidden:
                        _ = await bo.delete()
                        return False, f"料号{row_data[1]}不存在或已被禁用"

                    detail = await BOMDetail.create(primary_inner_id=bo.id,
                                                    serial_num=0,
                                                    part_num=row_data[1],
                                                    mate_model=row_data[2],
                                                    mate_desc=row_data[3],
                                                    mate_type=row_data[4],
                                                    unit_num=int(row_data[5]) if isinstance(row_data[5], float) else row_data[5],
                                                    unit_name=row_data[6],
                                                    tier_flag=row_data[7]
                                                   )
        return True, ""
    except Exception as e:
        logger.info(e)
        return False, str(e)


async def parse_po_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    try:
        async with in_transaction() as connection:
            for i in range(1, total_rows):
                row_data = sheet_table.row_values(i)
                # print(row_data)

                if row_data[0]:
                    if not row_data[1] or not row_data[2] or not row_data[3]:
                        return False, f"请填写完整表格数据"

                    _exist_supplier_code = await Supplier.filter(company_code=row_data[2], identity=0).exists()
                    _is_forbidden = await Supplier.filter(company_code=row_data[2],
                                                          is_forbidden=1,
                                                          identity=0).exists()
                    _exist_po = await PoList.filter(po_code=row_data[1]).exists()
                    if _exist_po:
                        return False, f"采购单号:{row_data[1]} 已存在"

                    if not _exist_supplier_code or _is_forbidden:
                        return False, f"供应商代码:{row_data[2]} 不存在或者该供应商已被禁用"

                    po = await PoList.create(po_code=str(int(row_data[1])) if isinstance(row_data[1], float) else row_data[1],
                                             supplier_code=row_data[2],
                                             supplier_name=row_data[3],
                                             delivery_time=row_data[4],
                                             commit_time=row_data[5]
                                             )

                elif row_data[1] != "物料编码":
                    _mate_info = await Material.filter(part_num=row_data[1]).first()
                    if not _mate_info:
                        _ = await po.delete()
                        return False, f"料号{row_data[1]}不存在"
                    elif _mate_info.is_forbidden == 1:
                        _ = await po.delete()
                        return False, f"料号{row_data[1]}已被禁用"

                    detail = await PoDetail.create(primary_inner_id=po.id,
                                                   serial_num=0,
                                                   part_num=row_data[1],
                                                   mate_model=_mate_info.mate_model,
                                                   unit_price=row_data[2],
                                                   qty=int(row_data[3]) if isinstance(row_data[3], float) else row_data[3],
                                                   total_price=row_data[4]
                                                   )
        return True, ""
    except Exception as e:
        logger.info(e)
        return False, str(e)


async def parse_order_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    try:
        async with in_transaction() as connection:
            for i in range(1, total_rows):
                row_data = sheet_table.row_values(i)
                # print(row_data)
                if row_data[0]:
                    _exist_order = await Order.filter(sales_order_code=row_data[1]).exists()
                    _exist_supplier_code = await Supplier.filter(company_code=row_data[3], identity=1).exists()
                    _is_forbidden = await Supplier.filter(company_code=row_data[3],
                                                          is_forbidden=1,
                                                          identity=1).exists()

                    if _exist_order:
                        return False, f"订单号:{row_data[1]} 已存在"

                    if not _exist_supplier_code or _is_forbidden:
                        return False, f"客户代码:{row_data[3]} 不存在或者该客户已被禁用"
                    
                    _exist_supplier_code = await Supplier.filter(company_code=row_data[5]).exists()
                    _is_forbidden = await Supplier.filter(company_code=row_data[5], is_forbidden=1).exists()
                    if not _exist_supplier_code or _is_forbidden:
                        return False, f"最终客户代码:{row_data[5]} 不存在或者该客户已被禁用"

                    od = await Order.create(sales_order_code=str(int(row_data[1])) if isinstance(row_data[1], float) else row_data[1],
                                            contract_code=str(int(row_data[2])) if isinstance(row_data[2], float) else row_data[2],
                                            customer_code=row_data[3],
                                            customer_name=row_data[4],
                                            finally_customer_code=row_data[5],
                                            finally_customer_name=row_data[6],
                                            delivery_time=row_data[7],
                                            commit_time=row_data[8]
                                            )

                elif row_data[1] != "料号":
                    _mate_exist = await Material.filter(part_num=row_data[1]).exists()
                    _is_forbidden = await Material.filter(part_num=row_data[1], is_forbidden=1).exists()
                    if not _mate_exist or _is_forbidden:
                        # return False, f"料号{row_data[1]}不存在或已被禁用"
                        _ = await od.delete()
                        raise Exception(f"料号{row_data[1]}不存在或已被禁用")

                    detail = await OrderDetail.create(primary_inner=od,
                                                       serial_num=0,
                                                       part_num=row_data[1],
                                                       mate_model=row_data[2],
                                                       mate_desc=row_data[3],
                                                       qty=row_data[4],
                                                       unit_name=row_data[5],
                                                       remark=row_data[6]
                                                       )
        return True, ""
    except Exception as e:
        logger.info(e)
        return False, str(e)
