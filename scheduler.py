from apscheduler.schedulers.asyncio import AsyncIOScheduler
# 定时任务
import datetime
from core.utils import DashBoard

scheduler = AsyncIOScheduler()



async def DashBoardTast():    
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
        result = await DashBoard.formatDashboardItem(location='head', title=k, infos=head_data, data=result)

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
        result = await DashBoard.formatDashboardItem(location=location, title=title, group_type=group_type, infos=detail_pcba_data, first_pass_list=fail_scale_list, product_list=product_list, data=result)

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
        result = await DashBoard.formatDashboardItem(location=location, title=title, group_type=group_type, infos=detail_pcba_data, first_pass_list=fail_scale_list, product_list=product_list, data=result)


def scheduler_start():
    scheduler.add_job(DashBoardTast, 'interval', seconds=30)
    # 启动调度器
    scheduler.start()
