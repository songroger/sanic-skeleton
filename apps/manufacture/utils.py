import xlrd
from core.logger import logger
from core.base import SalesOrderState
from .models import (Material, DeliverayOrderDetail, DeliveryOrder, Supplier, Order, OrderDetail,
                     PoList, PoDetail)


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
        if order_info.state == SalesOrderState.FINISHED.value:
            return True
        return False

    @classmethod
    async def getOrderInfo(cls, sales_order_code, is_need_detail=False):
        """
        获取订单信息(外键关联,获取主表信息及内容详情)
        :params sales_order_code: 订单号
        :params is_need_detail: boll 是否需要详情
        """
        order_info = await Order.filter(sales_order_code=sales_order_code)
        if is_need_detail is True:
            order_info = order_info.prefetch_related("details")
        order_info = order_info.first()
        return order_info

    @classmethod
    async def getSalesOrderByCustomer(cls, customer_code):
        """
        通过客户查询销售订单
        :params custom_code:客户代码(代理商) 
        """
        order_list = await Order.filter(customer_code=customer_code, state=SalesOrderState.Inprocess.value).order_by("-created_time")
        print(order_list)
        # TODO 通过客户查询订单:待实现

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
            if item.part_num in sales_map:
                sales_map[item.part_num] += item.qty
            else:
                sales_map[item.part_num] = item.qty

        # 2. 获取订单累计出货数量
        history_map = await DeliveryOrderOperation.getDeliveryHistoryData(sales_order_code=sales_order_code)
        
        # 3. 计算出最新剩余需求量
        if history_map:
            sales_map_copy = sales_map.copy()
            for pn, qty in sales_map_copy.items():
                # 料号可能没有出库数据,设置默认值0
                if pn in history_map:
                    if qty <= history_map[pn]:
                        del sales_map[pn]
                    else:
                        sales_map[pn] = qty - history_map[pn]
        # 返回订单有需求的料号
        return sales_map


class DeliveryOrderOperation:
    """
    出货单操作
    """
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
        await delivery.save()
        data = []
        for item in content:
            _sn = item.get("shelf_sn")
            _pn = item.get("part_num")
            _model = item.get("mate_model")
            _desc = item.get("mate_desc")
            _qty = item.get("qty")
            data.append(DeliverayOrderDetail(shelf_sn=_sn, part_num=_pn, mate_model=_model, mate_desc=_desc, qty=_qty, primary_inner=delivery))
        
        await DeliverayOrderDetail.bulk_create(data)
        # TODO 更新销售单状态


    @classmethod
    async def getDeliveryHistoryData(cls, delivery_order_code: str = "", sales_order_code: str = ""):
        """
        统计出货单发料数据
        :parmas delivery_order_code: 出货单号
        :parmas sales_order_code: 销售订单号
        :returns dict
        """
        query = DeliveryOrder.filter()

        if delivery_order_code:
            query = query.filter(delivery_order_code=delivery_order_code)

        if sales_order_code:
            query = query.filter(sales_order_code=sales_order_code)
        data = await query.prefetch_related("details").first()
        history_cache = {}
        if not data:
            return history_cache
        for item in data.details:
            if item.part_num in history_cache:
                history_cache[item.part_num] += item.qty
            else:
                history_cache[item.part_num] = item.qty
        return history_cache
        

    @classmethod
    async def getOrderInfo(cls, delivery_order_code):
        """获取出货单信息"""
        order_info = await DeliveryOrder.filter(delivery_order_code=delivery_order_code).prefetch_related("details").first()
        return order_info


async def checkDiffSalesAndDelivery(sales_order_code, delivery_detail):
    # 获取订单剩余需求
    salse_cache = await SalesOrderOperation.getLatestSurplusDemandForSalesOrder(sales_order_code=sales_order_code)
    if not salse_cache:
        return  False, "订单无需求,无法进行出货单创建!"
    # 按料号统计出库单物料数量
    delivery_cache = {}
    for item in delivery_detail:
        _pn = item.get("part_num")
        _qty = item.get("qty")
        if _pn in delivery_cache:
            delivery_cache[_pn] += _qty
        else:
            delivery_cache[_pn] = _qty

    # 检查出库单内的料号,对比订单需求
    for pn, qty in delivery_cache.items():
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
    for i in range(1, total_rows):
        row_data = sheet_table.row_values(i)
        objects.append(Material(part_num=row_data[1],
                                mate_model=row_data[2],
                                mate_desc=row_data[3],
                                spec_size=row_data[4],
                                spec_weight=row_data[5],
                                spec_min_qty=row_data[6],
                                spec_max_qty=row_data[7],
                                mate_type=row_data[8],
                                purchase_type=row_data[9],
                                purchase_cycle=row_data[10],
                                safety_stock=row_data[11],
                                safety_lower=row_data[12],
                                ))

    try:
        _ = await Material.bulk_create(objects)
        return True
    except Exception as e:
        logger.info(e)
        return False


async def parse_bom_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    return True


async def parse_po_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    try:
        for i in range(1, total_rows):
            row_data = sheet_table.row_values(i)
            # print(row_data)
            if row_data[0]:
                po = await PoList.create(po_code=row_data[1],
                                         supplier_code=row_data[2],
                                         supplier_name=row_data[3],
                                         delivery_time=row_data[4],
                                         commit_time=row_data[5]
                                         )

            elif row_data[1] != "物料编码":
                detail = await PoDetail.create(primary_inner_id=po.id,
                                               serial_num=0,
                                               part_num=row_data[1],
                                               unit_price=row_data[2],
                                               qty=row_data[3],
                                               total_price=row_data[4]
                                               )
        return True
    except Exception as e:
        logger.info(e)
        return False


async def parse_order_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    return True
