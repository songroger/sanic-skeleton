import os
import json
import pytz
import re
from core.logger import logger
from datetime import datetime


def getCurrentDatetime() -> str:
    """
    generate the current datatime with timezone info
    :return: str datatime with timezone
    """

    tz = pytz.timezone('Asia/Shanghai')
    datetime_format = "%Y-%m-%d %H:%M:%S %z"
    res = datetime.now(tz).strftime(datetime_format)
    return res


def getFileCurrentDatetime() -> str:
    """
    generate the current datatime
    :return: str datatime
    """
    tz = pytz.timezone('Asia/Shanghai')
    datetime_format = "%Y-%m-%dT%HH%MM%SS"
    res = datetime.now(tz).strftime(datetime_format)
    return res


def getPathList(path_str: str) -> list:
    """
    generate the path list for image
    :param path_str:
    :return:
    """
    path_dict = json.loads(path_str)
    path_list = []
    for key, value in path_dict.items():
        path_list.append(value)
    return path_list


def getImageIndex(file_name: str) -> str:
    """
    return the img_index of the file
    :param file_name:
    :return:
    """
    index = file_name.split('-')[-1].split('.')[0]
    return index


def deleteFile(file_path: str) -> bool:
    """
    delete the file in server
    :param file_path: file path
    :return: bool
    """
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        logger.error("[ERROR] delete file error: {}".format(e))
        return False


def getTotalCapacityFromType(shelf_type: str):
    """
    extract the total capacity number from shelf type
    :param shelf_type: str shelf_type
    :return: str total capacity or None if regex match method fail
    """
    pattern = re.compile(r"\w{2,3}-\d[S|D](\d+)")
    res = re.match(pattern, shelf_type)
    if res is None:
        return res
    else:
        return res.group(1)


def validated_shelf_type(shelf_type: str):
    pattern = re.compile(r"\w{2,3}-\d[S|D]\d+")
    res = re.fullmatch(pattern, shelf_type)
    if res is None:
        return False
    else:
        return True


def validated_shelf_sn(shelf_sn: str):
    pattern = re.compile(r"SN\w{3}-\w{3}-\w{3}")
    res = re.fullmatch(pattern, shelf_sn)
    if res is None:
        return False
    else:
        return True
