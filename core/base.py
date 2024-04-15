import time
import datetime
from enum import Enum
from sanic import response
from typing import Union
from .logger import logger
import traceback
from sanic.handlers import ErrorHandler


# 全局异常处理
class ServerErrorHandler(ErrorHandler):
    def response(self, request, exception):
        try:
            exception_type = exception.args[0]
            exc_traceback = traceback.extract_tb(exception.__traceback__)
            logger.error(f"some error cache:{exc_traceback}", exc_info=True)
            return baseResponse(ResponseCode.FAIL, msg=exception_type)
        except Exception as e:
            logger.error("Sever Error Handler Error", exc_info=True)
        return super().response(request, exception)


class ResponseCode:
    """
    基础响应状态码
    """
    OK = 200
    FAIL = 201


def baseResponse(status_code: ResponseCode, msg: str, data: Union[dict, list] = {}) -> dict:
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


class SupplierIdentityEnum(Enum):
    """
    公司身份标识
    """
    Supplier = 0      # 供应商
    Customer = 1      # 客户


class SalesOrderStateEnum(Enum):
    """
    销售单状态
    """
    # 基础状态

    CREATE = 0    # 新建
    OUTING = 1    # 出货中
    FINISHED = 2  # 出货完成

    # 组合状态
    ## 处理中的状态
    Inprocess = [CREATE, OUTING]


class MateTypeEnum(Enum):
    """
    物料类型
    """
    FINISHED_PRODUCT = "成品"
    SEMI_PRODUCT = "半成品"
    RAW_MATERIAL = "原材料"


class PurchaseTypeEnum(Enum):
    """
    采购类型
    """
    PURCHASE = "采购"
    PRODUCT = "生产"

