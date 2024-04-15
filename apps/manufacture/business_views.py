from sanic import Blueprint
from .utils import SalesOrderOperation, MaterialOperation, ComponyOperation
from core.base import baseResponse, ResponseCode, SalesOrderStateEnum, MateTypeEnum, PurchaseTypeEnum

business_bp = Blueprint('business', url_prefix='/business')


@business_bp.route("/getUnfinishedSalesOrderList", methods=['GET'])
async def getUnfinishedSalesOrderList(request):
    """
    PDA:获取未完成的销售订单客户列表(PDA出货下拉展示)
    """
    payload = request.args
    sales_order_code = payload.get("sales_order_code", "")
    data = await ComponyOperation.getCustomerInfoByUnfinishSalesOrder(sales_order_code=sales_order_code)

    return baseResponse(ResponseCode.OK, "success", data=data)


@business_bp.route("/getSalesOrderDetails", methods=['GET'])
async def getSalesOrderDetails(request):
    """
    PDA:获取销售订单内容详情
    """
    payload = request.args
    sales_order_code = payload.get("sales_order_code")
    result = await SalesOrderOperation.getOrderInfo(sales_order_code=sales_order_code, is_need_detail=True)

    # 料号列表
    part_list = []
    # 料号缓存
    content_map = {}
    for item in result:
        for itemY in item.details:
            part_list.append(itemY.part_num)
            content_map[itemY.part_num] = itemY.to_dict()
    # 自生产的成品，认为是出货产品，其余都算是配件
    material_list = await MaterialOperation.getPartNumInfos(part_num_list=part_list)
    # 设备列表
    device_list = []
    # 配件列表
    attachment_list = []
    for item in material_list:
        pn = item.part_num
        info = item.to_dict()
        info.update(qty = content_map[pn]['qty'], out_qty=0, sn_list=[])
        if item.mate_type == MateTypeEnum.FINISHED_PRODUCT.value and item.purchase_type == PurchaseTypeEnum.PRODUCT.value:
            device_list.append(info)
        else:
            attachment_list.append(info)

    data = {
        "content": list(content_map.values()),
        "device_list": device_list,
        "attachment_list": attachment_list
    }
    return baseResponse(ResponseCode.OK, "success", data=data)






