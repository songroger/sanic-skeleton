from sanic import Blueprint
from apps.database.utils import parseReceiveDataForMachineTest, parseReceiveDataForPCBATest
from core.utils import checkSupplierCode, loadJsonConf
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
    file_path = "data/mate_model_list.json"
    flag, data, msg = loadJsonConf(file_path=file_path)
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
    factory_code = payload.get("factory_code")

    supplier_info = await checkSupplierCode(factory_code=factory_code, is_disable=0)
    if not supplier_info:
        return baseResponse(ResponseCode.FAIL, f"供应商<{factory_code}>不存在,无法上传数据!", {})
    # data = payload.get("data")
    if request_type == 0:
        await parseReceiveDataForMachineTest(payload)
        return baseResponse(ResponseCode.OK, "success", {})
    elif request_type == 1:
        await parseReceiveDataForPCBATest(payload)
        return baseResponse(ResponseCode.OK, "success", {})
    else:
        return baseResponse(ResponseCode.FAIL, "请求类型错误,无法识别上传数据类型", {})

