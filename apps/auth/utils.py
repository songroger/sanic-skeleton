from .models import FactoryParm


def get_test_case_special_group(test_case_name: str) -> list:
    """
    解析测试名称获取特殊分组信息
    协特殊符号@为分组符号，如name@1则表示该测试项属于特殊分组1，name@1@2表示同时属于分组1和分组2
    :param test_case_name: 测试名称
    :return: 分组信息列表 name -> [], name@1 -> [1], name@1@2 -> [1,2]
    """
    group_list = test_case_name.split('@')
    test_case_name_position = 0
    group_list.pop(test_case_name_position)
    return group_list


async def getParaSetting(para_name: str) -> str:
    """
    参数配置表： factory_para_config
    """
    param = await FactoryParm.filter(para_name=para_name).first()

    return param.para_value if param else 'notDefined'
