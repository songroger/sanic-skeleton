import json
import os
from settings import program_root_path


def loadBaseData():
    """
    加载数据字典
    """
    file_name = "data/mate_model_list.json"
    path = os.path.join(program_root_path, file_name)
    data = {}
    try:
        with open(path, 'r', encoding='utf8') as f:
            data = json.load(f)
        return True, data, "success"
    except Exception as e:
        return False, data, str(e)


