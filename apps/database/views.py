from sanic import Blueprint
from apps.database.utils import parseReceiveDataForMachineTest
from core.utils import loadBaseData
from core.base import baseResponse, ResponseCode, MateTypeEnum, PurchaseTypeEnum


database_bp = Blueprint('database', url_prefix='/database')


@database_bp.route("/getMateTypeList")
async def getMateTypeList(request):
    """
    获取物料类型及采购类型配置
    """
    mate_model_list = []
    for item in MateTypeEnum:
        mate_model_list.append(item.value)
    
    purchase_type_list = []
    for item in PurchaseTypeEnum:
        purchase_type_list.append(item.value)
    data = {
        "mate_type_list": mate_model_list,
        "purchase_list": purchase_type_list
    }
    return baseResponse(ResponseCode.OK, msg="success", data=data)


@database_bp.route("/getMateModelList")
async def getMateModelList(request):
    """
    获取物料型号
    """
    payload = request.args
    mate_type = payload.get("mate_type")

    # 加载配置文件
    flag, data, msg = loadBaseData()
    if flag is False:
        return baseResponse(ResponseCode.FAIL, msg=msg)
    if mate_type not in data:
        return baseResponse(ResponseCode.FAIL, msg=f"<{mate_type}>类型没有相应的物料型号数据字典配置!")

    # 返回对应数据
    mate_models = data[mate_type]
    
    return baseResponse(ResponseCode.OK, "success", data=mate_models)


@database_bp.route("/receiveUploadData", methods=['POST'])
async def receiveUploadData(request):
    payload = request.json
    request_type = payload.get("request_type", -1)
    if request_type == 0:
        data = payload.get("data")
        await parseReceiveDataForMachineTest(data)
        return baseResponse(ResponseCode.OK, "success", {})
    elif request_type == 1:
        return baseResponse(ResponseCode.OK, "success", {})
    else:
        return baseResponse(ResponseCode.FAIL, "请求类型错误,无法识别上传数据类型", {})

