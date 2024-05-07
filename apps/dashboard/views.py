from typing import List
from sanic import Blueprint
from sanic.views import HTTPMethodView
from core.base import ResponseCode, baseResponse
from core.utils import DashBoard, getCurrentMonthPurchaseInfo


dashboard_bp = Blueprint('dashboard', url_prefix='/dashboard')


def formatDashboardItem(location: str, title: str, infos: List[dict], group_type: str = None, first_pass_list: List[int] = None, product_list: List[int] = None, data: dict = None,):
    """
    看板单元数据格式化
    :param location: head|content
    :param group_type: 控制箱|感应板|整机
    """
    if data is None:
        data = {}
    if location not in data:
        data[location] = []
    
    group_temp = {}
    idx = -1
    if group_type:
        for i, item in enumerate(data[location]):
            if item.get("group") == group_type:
                idx = i
                break
        if idx == -1:
            group_temp = {"group": group_type, "group_details": []}
        else:
            group_temp = data[location][idx]
    temp = {"title": title, "details": []}
    for i in infos:
        temp['details'].append({
            "name": i[0],
            "value": i[1],
            "type": i[2]
        })
        if first_pass_list:
            temp['first_pass_list'] = first_pass_list
        if product_list:
            temp['product_list'] = product_list


    if group_temp:
        group_temp['group_details'].append(temp)

    else:
        group_temp = temp

    if idx != -1:
        data[location][idx] = group_temp
    else:
        data[location].append(group_temp)

    return data


class DashboardPage(HTTPMethodView):
    """
    主看板
    """
    async def get(self, request):
        result = {}
        # 头部数据构造
        data = await DashBoard.StatisticsHeadData()
        for k, v in data.items():
            # '感应板': {'当月订单数': 30, '已生产数': 0, '剩余': 30}
            title = k
            total = v[0]
            finish = v[1]
            progress = 0
            if total > 0:
                progress = round(finish / total * 100, 2)
            head_data = [["当月订单数", total, 0],
                       ["已生产数", finish, 0],
                       ["剩余", total - finish, 0],
                       ["", progress, 1]]
            result = formatDashboardItem(location='head', title=k, infos=head_data, data=result)

        # pcba数据
        pcba_record = await DashBoard.StatisticsPCBARecord()
        for supplier, info in pcba_record.items():
            title = info.get("supplier_name")
            location = 'content'
            group_type = '感应板'
            total = info.get("total")
            fail = info.get("fail")
            fail_scale = info.get("fail_scale")
            product_list = info.get("product_list")
            fail_scale_list = info.get("fail_scale_list")
            detail_pcba_data = [
                ["生产数", total, 0],
                ["不良数", fail, 0],
                ["不良率", f"{fail_scale}%", 0],
                ["当日不良率", fail_scale, 1],
                ]
            result = formatDashboardItem(location=location, title=title, group_type=group_type, infos=detail_pcba_data, first_pass_list=fail_scale_list, product_list=product_list, data=result)

        # 整机数据
        machine_record = await DashBoard.StatisticsMachineRecord()
        for supplier, info in machine_record.items():
            title = info.get("supplier_name")
            location = 'content'
            group_type = '整机'
            total = info.get("total")
            fail = info.get("fail")
            fail_scale = info.get("fail_scale")
            product_list = info.get("product_list")
            fail_scale_list = info.get("fail_scale_list")
            detail_pcba_data = [
                ["生产数", total, 0],
                ["不良数", fail, 0],
                ["不良率", f"{fail_scale}%", 0],
                ["当日不良率", fail_scale, 1],
                ]
            result = formatDashboardItem(location=location, title=title, group_type=group_type, infos=detail_pcba_data, first_pass_list=fail_scale_list, product_list=product_list, data=result)

        return baseResponse(ResponseCode.OK, "success", result)

    async def post(self, request):
        args = request.json

        todo_id = args.get("task")

        return baseResponse(ResponseCode.OK, "success", {"task": todo_id})


@dashboard_bp.route("/test")
async def a(request):
    # 整机进度统计
    data = await DashBoard.StatisticsMachineRecord()
    print(data)
    # # PCBA进度统计
    # data = await DashBoard.StatisticsPCBARecord()
    # print(data)
    # data = await DashBoard.StatisticsHeadData()
    # print(data)
    return baseResponse(ResponseCode.OK, "success")



dashboard_bp.add_route(DashboardPage.as_view(), "/product")
