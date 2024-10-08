import datetime
import hashlib
from decimal import Decimal
import json
import os
from typing import List, Union
from apps.database.models import MachineTestSummary, PCBATestSummary
from apps.manufacture.models import Supplier, PoList, Material
from settings import program_root_path
from .logger import logger
from itsdangerous import TimedJSONWebSignatureSerializer
from settings import settings


def loadJsonConf(file_path):
    """
    加载json配置数据
    :param path:基于根目录的相对路径
    """
    path = os.path.join(program_root_path, file_path)
    data = {}
    try:
        with open(path, 'r', encoding='utf8') as f:
            data = json.load(f)
        return True, data, "success"
    except Exception as e:
        return False, data, str(e)


async def checkSupplierCode(factory_code: str, is_disable=-1):
    """
    检查供应商代码是否存在
    """
    query = Supplier.filter(company_code=factory_code, identity=0)
    if is_disable != -1:
        query  = query.filter(is_disable=is_disable)

    supplier = await query.first()
    if supplier:
        return supplier.to_dict()
    return {}


async def getCurrentMonthPurchaseInfo(month):
    """
    获取当前月份的采购订单信息
    当月交期的采购单
    """
    # cur_month = datetime.date.today().strftime("%Y-%m")
    cur_month = month
    po_infos = await PoList.filter(delivery_time__contains=cur_month).prefetch_related("details").all()

    file_path = "data/mate_model_group.json"
    flag, data, msg = loadJsonConf(file_path=file_path)

    ctrl_model = []
    pcba_model = []
    machine_model = []
    if flag:
        ctrl_model = data.get("ctrl_box", [])
        pcba_model = data.get("pcba", [])
        machine_model = data.get("machine", [])

    ctrl_count = 0
    pcba_count = 0
    machine_count = 0
    for po_item in po_infos:
        for detail_item in po_item.details:
            # 根据不同的产品，累加各自的需求数
            if detail_item.mate_model in ctrl_model:
                ctrl_count += detail_item.qty
            elif detail_item.mate_model in pcba_model:
                pcba_count += detail_item.qty
            elif detail_item.mate_model in machine_model:
                machine_count += detail_item.qty

    result = {
        "控制箱": ctrl_count,
        "整机": machine_count,
        "感应板": pcba_count
    }
    return result

async def getFinishedPurchaseInfo(month):
    """
    统计已完成的数据
    """
    cur_month = month
    po_list = []
    po_infos = await PoList.filter(delivery_time__contains=cur_month).all()
    for item_po in po_infos:
        po_list.append(item_po.po_code)

    machine_list = []
    # 只统计早于当前时间的数据
    now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    machine_summarys = await MachineTestSummary.filter(record_purchase_code__in=po_list, record_created_time__lte=now_time).all()
    for item in machine_summarys:
        if item.record_shelf_sn not in machine_list:
            machine_list.append(item.record_shelf_sn)

    pcba_list = []
    pcba_summarys = await PCBATestSummary.filter(record_purchase_code__in=po_list, record_created_time__lte=now_time).all()
    for item in pcba_summarys:
        if item.record_sn not in pcba_list:
            pcba_list.append(item.record_sn)
    # TODO 控制箱未对接,临时使用文件动态调整数据
    try:
        with open("data/control_box_count.txt", "r")as f:
            box_count = f.read().strip()
        if box_count.isdigit():
            box_count = int(box_count)
    except:
        box_count = 0
    data = {
        "控制箱": box_count,
        "感应板": len(pcba_list),
        "整机": len(machine_list)
    }
    return data

class DashBoard:

    @classmethod
    def decimal_to_float_with_precision(cls, number: Union[int, float]):
        """
        四舍五入保留2位小数
        """
        res = Decimal(number)
        b = res.quantize(Decimal('0.00'))
        return b

    # hour:idx,时间段与数组下标的映射
    DetailIdxMap = {
        9: 0,
        11: 1,
        13: 2,
        15: 3,
        17: 4,
        19: 5
    }

    @classmethod
    async def _getWholeMachineContentData(cls, supplier_id_list: List[str]):
        """
        获取整机Content数据
        """
        # logger.info("开始统计了")
        now_time = datetime.datetime.now()
        start_time = now_time.strftime("%Y-%m-%d") + " 00:00:00"
        end_time = now_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 按供应商统计
        result = {}
        for item in supplier_id_list:
            result[item] = {}

        # sn去重
        shelf_sn_duplicate_removal = []
        # sn失败去重
        shelf_sn_fail_removel = []

        # 查询整机测试结果数据，限制测试时间,
        query = MachineTestSummary.filter(record_created_time__range=(start_time, end_time))
        if supplier_id_list:
            query = query.filter(record_customer_code__in=supplier_id_list)
        summarys = await query.order_by("id").all()
        # summarys = await MachineTestSummary.all()
        # logger.info(f">>:{summarys}")
        if summarys:
            for item in summarys:
                record_customer_code = item.record_customer_code
                record_shelf_sn = item.record_shelf_sn
                record_result = item.record_result
                record_deleted = item.record_deleted
                # 构造不同供应商分组数据
                if record_customer_code not in result:
                    result[record_customer_code] = {}

                # 俩小时统计频率，若为偶数小时，则+1转为奇数
                hour = datetime.datetime.strptime(item.record_created_time, '%Y-%m-%d %H:%M:%S').hour
                if hour % 2 == 0:
                    hour += 1

                if hour not in result[record_customer_code]:
                    result[record_customer_code][hour] = {"total": 0, "fail": 0}
                
                # 当前时间段的统计结果
                cur_hour_total =  result[record_customer_code][hour]['total']
                cur_hour_fail =  result[record_customer_code][hour]['fail']

                if record_shelf_sn not in shelf_sn_duplicate_removal:
                    shelf_sn_duplicate_removal.append(record_shelf_sn)
                    cur_hour_total += 1

                # 未完成测试就删除的，认为是NG
                if record_deleted == 1 and record_result != 2:
                    if record_shelf_sn not in shelf_sn_fail_removel:
                        cur_hour_fail += 1
                        shelf_sn_fail_removel.append(record_shelf_sn)

                result[record_customer_code][hour].update(total=cur_hour_total, fail=cur_hour_fail)
        return result
    
    @classmethod
    async def StatisticsMachineRecord(cls):
        """
        整机当日详情数据统计
        """
        # TODO 临时写死，后续从供应商数据库配置中获取
        supplier_id_list = []
        file_path = "data/supplier_config.json"
        flag, data, msg = loadJsonConf(file_path=file_path)
        if flag:
            supplier_id_list = data.get("machine_supplier", [])
        data = await cls._getWholeMachineContentData(supplier_id_list=supplier_id_list)
        result = {}
        for vendor, infos in data.items():
            # 检查供应商配置信息
            supplier_info = await checkSupplierCode(vendor)
            if not supplier_info:
                continue
            product_list = [0 for i in range(len(cls.DetailIdxMap))]
            fail_list = product_list.copy()
            fail_scale_list = product_list.copy()
            infos = dict(sorted(infos.items()))
            for hour, info in infos.items():
                # print(vendor, hour, info)
                if hour in cls.DetailIdxMap:
                    idx = cls.DetailIdxMap[hour]
                    product_list[idx] = info['total']
                    fail_list[idx] = info['fail']
                    if info["total"]:
                        fail_scale_list[idx] = round((info["fail"]/info['total'])*100, 2)
                else:
                    logger.warning(f"{vendor}测试数据,{hour}时间段超出配置的8-20范围!")
                    continue
            total = sum(product_list)
            fail = sum(fail_list)
            fail_scale = 0
            if total:
                fail_scale = round(fail/total*100, 2)
            item_result = {
                "supplier_name": supplier_info.get("short_name", "Unknown"),
                "total": total,
                "fail": fail,
                "fail_scale": fail_scale,
                "product_list": product_list,
                "fail_list": fail_list,
                "fail_scale_list": fail_scale_list
            }
            result[vendor] = item_result
        return result
    
    @classmethod
    async def _getPCBAContentData(cls, supplier_id_list: List[str]):
        """
        获取pcba感应板Content数据
        """
        logger.info("开始统计了")
        now_time = datetime.datetime.now()
        start_time = now_time.strftime("%Y-%m-%d") + " 00:00:00"
        end_time = now_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 按供应商统计
        result = {}
        for item in supplier_id_list:
            result[item] = {}

        # sn去重
        shelf_sn_duplicate_removal = []
        # sn失败去重
        shelf_sn_fail_removel = []

        # 查询整机测试结果数据，限制测试时间,
        query = PCBATestSummary.filter(record_created_time__range=(start_time, end_time))
        
        if supplier_id_list:
            query = query.filter(record_customer_code__in=supplier_id_list)
        summarys = await query.order_by("id").all()
        # logger.info(f">>:{summarys}")
        if summarys:
            for item in summarys:
                record_customer_code = item.record_customer_code
                record_shelf_sn = item.record_sn
                record_result = item.record_result
                record_deleted = item.record_deleted
                # 构造不同供应商分组数据
                if record_customer_code not in result:
                    result[record_customer_code] = {}

                # 俩小时统计频率，若为偶数小时，则+1转为奇数
                hour = datetime.datetime.strptime(item.record_created_time, '%Y-%m-%d %H:%M:%S').hour
                if hour % 2 == 0:
                    hour += 1

                if hour not in result[record_customer_code]:
                    result[record_customer_code][hour] = {"total": 0, "fail": 0}
                
                # 当前时间段的统计结果
                cur_hour_total =  result[record_customer_code][hour]['total']
                cur_hour_fail =  result[record_customer_code][hour]['fail']

                if record_shelf_sn not in shelf_sn_duplicate_removal:
                    shelf_sn_duplicate_removal.append(record_shelf_sn)
                    cur_hour_total += 1

                # 未完成测试就删除的，认为是NG
                if record_result != 1:
                    if record_shelf_sn not in shelf_sn_fail_removel:
                        cur_hour_fail += 1
                        shelf_sn_fail_removel.append(record_shelf_sn)

                result[record_customer_code][hour].update(total=cur_hour_total, fail=cur_hour_fail)
        # logger.info(result)
        return result

    @classmethod
    async def StatisticsPCBARecord(cls):
        """
        PCBA当日统计
        """
        # TODO 临时写死，后续从供应商数据库配置中获取
        supplier_id_list = []
        file_path = "data/supplier_config.json"
        flag, data, msg = loadJsonConf(file_path=file_path)
        if flag:
            supplier_id_list = data.get("pcba_supplier", [])
        data = await cls._getPCBAContentData(supplier_id_list=supplier_id_list)
        result = {}
        for vendor, infos in data.items():
            # 检查供应商配置信息
            supplier_info = await checkSupplierCode(vendor)
            if not supplier_info:
                continue

            product_list = [0 for i in range(len(cls.DetailIdxMap))]
            fail_list = product_list.copy()
            fail_scale_list = product_list.copy()
            infos = dict(sorted(infos.items()))
            for hour, info in infos.items():
                # print(vendor, hour, info)
                if hour in cls.DetailIdxMap:
                    idx = cls.DetailIdxMap[hour]
                    product_list[idx] = info['total']
                    fail_list[idx] = info['fail']
                    if info["total"]:
                        fail_scale_list[idx] = round((info["fail"]/info['total'])*100, 2)
                else:
                    logger.warning(f"{vendor}测试数据,{hour}时间段超出配置的8-20范围!")
                    continue
            total = sum(product_list)
            fail = sum(fail_list)
            fail_scale = 0
            if total:
                fail_scale = round(fail/total*100, 2)

            item_result = {
                "supplier_name": supplier_info.get("short_name", "Unknown"),
                "total": total,
                "fail": fail,
                "fail_scale": fail_scale,
                "product_list": product_list,
                "fail_list": fail_list,
                "fail_scale_list": fail_scale_list
            }
            result[vendor] = item_result
        return result
    
    @classmethod
    async def StatisticsHeadData(cls):
        """
        头部当月统计汇总
        """
        cur_month = datetime.date.today().strftime("%Y-%m")
        # 统计采购单总需求
        data1 = await getCurrentMonthPurchaseInfo(cur_month)
        # 统计采购单生产数量
        data2 = await getFinishedPurchaseInfo(cur_month)
        result = {}
        for k, v in data1.items():
            result[k] = [v, data2[k]]
        return result

    @classmethod
    async def formatDashboardItem(cls, location: str, title: str, infos: List[dict], group_type: str = None, first_pass_list: List[int] = None, 
                                  product_list: List[int] = None, data: dict = None,):
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


def generate_token(info, secret_key=settings.SECRET_KEY, expires_time=settings.EXPIRATION_DELTA):
    t = TimedJSONWebSignatureSerializer(secret_key=secret_key, expires_in=expires_time)
    token = t.dumps(info).decode()
    return token


def parse_token(token, secret_key=settings.SECRET_KEY):
    t = TimedJSONWebSignatureSerializer(secret_key)
    res = t.loads(token)
    return res


def encrypt_msg(msg):
    md = hashlib.md5()
    md.update(msg.encode(encoding='utf-8'))
    msg = md.hexdigest()
    return msg
