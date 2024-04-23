from typing import List
from sanic import Blueprint
from sanic.views import HTTPMethodView
from core.base import ResponseCode, baseResponse


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


class Dashboard(HTTPMethodView):
    """
    主看板
    """
    async def get(self, request):
        result = {}
        # 控制箱
        head_control_box_data = [["当月订单数", 1000, 0],
                       ["已生产数", 800, 0],
                       ["剩余", 200, 0],
                       ["", 80, 1]]
        result = formatDashboardItem(location='head', title='控制箱', infos=head_control_box_data, data=result)

        # 感应板
        head_pcba_data = [["当月订单数", 1000, 0],
                       ["已生产数", 800, 0],
                       ["剩余", 200, 0],
                       ["", 80, 1]]
        result = formatDashboardItem(location='head', title='感应板', infos=head_pcba_data, data=result)

        # 整机
        head_whole_machine_data = [["当月订单数", 100, 0],
                       ["已生产数", 70, 0],
                       ["剩余", 30, 0],
                       ["", 70, 1]]
        result = formatDashboardItem(location='head', title='整机', infos=head_whole_machine_data, data=result)

        # 详情>感应板>中易
        detail_pcba_data = [["生产数", 1000, 0],
                            ["不良数", 5, 0],
                            ["不良率", 0.5, 0],
                            ['当日不良率', 78.87, 1]]
        f1 = [5,0,0,0,0,0]
        p1 = [3,0,0,0,0,0]
        result = formatDashboardItem(location='content', title='中易', group_type='感应板', infos=detail_pcba_data, first_pass_list = f1, product_list = p1, data=result)

        # 详情>感应板>德平
        detail_pcba_data = [["生产数", 1000, 0],
                            ["不良数", 5, 0],
                            ["不良率", 0.5, 0],
                            ['当日不良率', 78.87, 1]]
        f1 = [0,0,0,0,0,0]
        p1 = [0,0,0,0,0,0]
        result = formatDashboardItem(location='content', title='德平', group_type='感应板', infos=detail_pcba_data, first_pass_list = f1, product_list = p1, data=result)

        # 详情>整机>华挚
        detail_machine_data = [["生产数", 1000, 0],
                            ["不良数", 5, 0],
                            ["不良率", 0.5, 0],
                            ['当日不良率', 78.87, 1]]
        f1 = [0,0,0,0,0,100]
        p1 = [0,0,0,0,0,0]
        result = formatDashboardItem(location='content', title='华挚', group_type='整机', infos=detail_machine_data, first_pass_list = f1, product_list = p1, data=result)

        # 详情>整机>立纳
        detail_machine_data = [["生产数", 1000, 0],
                            ["不良数", 5, 0],
                            ["不良率", 0.5, 0],
                            ['当日不良率', 78.87, 1]]
        f1 = [0,0,100,0,0,0]
        p1 = [0,0,0,0,0,0]
        result = formatDashboardItem(location='content', title='立纳', group_type='整机', infos=detail_machine_data, first_pass_list = f1, product_list = p1, data=result)

        return baseResponse(ResponseCode.OK, "success", result)

    async def post(self, request):
        args = request.json

        todo_id = args.get("task")

        return baseResponse(ResponseCode.OK, "success", {"task": todo_id})


dashboard_bp.add_route(Dashboard.as_view(), "/product")
