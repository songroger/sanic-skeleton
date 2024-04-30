import datetime

from database.models import MachineTestRecord, MachineTestSummary


async def getWholeMachineHeadData():
    """
    获取整机HEAD数据
    """
    cur_month = datetime.date.today().strftime("%Y-%m")
    # TODO 看板数据计算待处理
    

async def getWholeMachineContentData():
    """
    获取整机Content数据
    """
    cur_month = datetime.date.today().strftime("%Y-%m")
    # 查询整机测试结果数据，限制测试时间,
    q_sql = """
    select shelf_sn,count(*) from factory_test_summary where created_time >='2023-01-01' and created_time<='2024-01-31' and test_case_result='2' and is_deleted group by shelf_sn;
    """
    # TODO 看板数据计算待处理
    

def 整机测试统计():
    pass


