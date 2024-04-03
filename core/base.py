import time
import datetime
from enum import Enum
from sanic import response


def baseResponse(status_code: int, msg: str, data: dict = {}) -> dict:
    """
    generate the base response
    :param status_code: http status code
    :param msg: response msg
    :param data: specific data from different api
    :return: dict
    """
    response_dict = {
        "code": status_code,
        "msg": msg,
        "data": data
    }
    return response.json(response_dict)


def utc_time_conversion(date_time):
    '''
    datetime.datetime类型的时区转换
    :param date_time:datetime.datetime类型或time时间戳的时间对象，将其他时区的时间格式换成本地时间字符串
    :return:
    '''
    if isinstance(date_time, datetime.datetime):
        in_time = date_time.timestamp()
    elif isinstance(date_time, float):
        in_time = date_time
    else:
        return 'time format error'
    time_array = time.localtime(int(in_time))
    res_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return res_time


class SalesOrderState(Enum):
    """
    销售单状态
    """
    # 基础状态
    CREATE = 0
    OUTING = 1
    FINISHED = 2

    # 组合状态
    ## 处理中的状态
    Inprocess = [CREATE, OUTING]

