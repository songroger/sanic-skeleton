from typing import List
from tortoise.transactions import in_transaction
from .models import MachineTestRecord, MachineTestSummary


async def parseReceiveDataForMachineTest(data):
    """
    解析整机测试上报数据
    """
    test_id_list = []
    # 供应商编号
    # factory_code = data.get("factory_code")
    data_list = data
    for test_item in data_list:
        test_id = test_item.get("test_id")
        test_id_list.append(test_id)

    if not test_id_list:
        return
    
    # 主表更新及添加
    update_summary_dict = {}
    insert_summary_list = []
    # 详情更新及添加
    insert_record_list = []
    update_record_dict = {}

    # 搜索测试ID历史测试记录(即允许更新测试状态)
    local_test_history, local_test_detail_history = await MachineTestSummaryOperation.getHistoryRecordInfoByTestIDList(test_id_list=test_id_list)
    
    # 再次循环数据
    for item in data_list:
        details = item.get("details")
        test_id = item.get("test_id")
        is_deleted = int(item.get("is_deleted"))
        test_case_result = int(item.get("test_case_result"))

        del item['details']
        # 检查test_id对应数据，不存在或状态不一致，进行添加或更新
        if test_id in local_test_history:
            history = local_test_history[test_id]
            # 删除标记或测试结果不一致,需要更新
            if is_deleted != history.record_deleted or test_case_result != history.record_result:
                update_summary_dict[history.id] = {
                    "id": history.id, 
                    "record_deleted": is_deleted,
                    "record_result": test_case_result
                    }
        else:
            insert_summary_list.append(item)

        # 默认检查详情更新,如果这个test_id第一次进来,则不检查详情是否需要更新
        for item2 in details:
            item2['test_id'] = test_id
            detail_id = item2.get("detail_id")
            detail_is_deleted = item2.get("detail_is_deleted")
            # 若test_id+详情=存在,则判断详情删除标记是否一致
            if (test_id, detail_id) in local_test_detail_history:
                history = local_test_detail_history[(test_id, detail_id)]
                if detail_is_deleted != history.record_deleted:
                    update_record_dict[history.id] = {
                        "id": history.id, 
                        "record_deleted": detail_is_deleted
                    }
            else:
                insert_record_list.append(item2)
    
    await MachineTestSummaryOperation.addAndUpdateTestResultInfo(insert_summary_list=insert_summary_list, update_summary_dict=update_summary_dict, 
                                                                 insert_record_list=insert_record_list, update_record_dict=update_record_dict)

    # 添加数据

def parseReceiveDataForPCBATest(data):
    """
    解析PCBA测试上报数据
    """
    pass


class MachineTestSummaryOperation:
    @classmethod
    async def getHistoryRecordInfoByTestIDList(cls, test_id_list: list):
        """
        获取平台已存在的历史测试结果状态
        """

        # 缓存测试主数据的状态
        test_res = await MachineTestSummary.filter(record_test_id__in=test_id_list).all()
        test_map = {}
        for item in test_res:
            test_id = item.record_test_id
            test_map[test_id] = item
        
        # 缓存测试详情的状态 
        detail_res = await MachineTestRecord.filter(record_test_id__in=test_id_list).order_by("record_detail_id").all()
        data_map = {}
        for item in detail_res:
            test_id = item.record_test_id
            detail_id = item.record_detail_id
            data_map[(test_id, detail_id)] = item

        return test_map, data_map

    @classmethod
    async def addAndUpdateTestResultInfo(cls, insert_summary_list: List[dict], update_summary_dict: dict, 
                                         insert_record_list: List[dict], update_record_dict: dict):
        """
        添加即更新测试数据
        """
        insert_summary_obj_list = []
        for item in insert_summary_list:
            record_test_id = item.get("test_id")
            record_shelf_sn = item.get("shelf_sn")
            record_test_strategy = item.get("test_strategy")
            record_created_by = item.get("created_by")
            record_created_time = item.get("created_time")
            record_customer_code = item.get("customer_name")
            record_purchase_code = item.get("order_id")
            record_result = item.get("test_case_result")
            record_deleted = item.get("is_deleted")
            summary = MachineTestSummary(record_test_id=record_test_id, record_shelf_sn=record_shelf_sn, record_test_strategy=record_test_strategy,
                            record_created_by=record_created_by, record_created_time=record_created_time, record_customer_code=record_customer_code,
                            record_purchase_code=record_purchase_code, record_result=record_result, record_deleted=record_deleted)
            insert_summary_obj_list.append(summary)
        
        insert_record_obj_list = []
        for item in insert_record_list:
            record_created_by = item.get("detail_created_by")
            record_created_time = item.get("detail_created_time")
            record_test_id = item.get("test_id")
            record_detail_id = item.get("detail_id")
            record_item_name = item.get("test_case_name")
            record_result = item.get("detail_test_result")
            record_deleted = item.get("detail_is_deleted")
            record_pass_comment = item.get("test_case_comment")
            record_pass_comment_img = item.get("test_case_result_image_path")
            record_ng_comment = item.get("test_case_ng_comment")
            record_ng_comment_img = item.get("test_case_ng_image_path")
            record = MachineTestRecord(record_created_by=record_created_by, record_created_time=record_created_time, record_test_id=record_test_id, 
                            record_detail_id=record_detail_id, record_item_name=record_item_name, record_result=record_result,
                            record_deleted=record_deleted, record_pass_comment=record_pass_comment, record_pass_comment_img=record_pass_comment_img,
                            record_ng_comment=record_ng_comment, record_ng_comment_img=record_ng_comment_img)
            insert_record_obj_list.append(record)

        update_summary = []
        if update_summary_dict:
            summary = await MachineTestSummary.filter(id__in=list(update_summary_dict.keys())).all()
            for item in summary:
                item.record_deleted = update_summary_dict[item.id]['record_deleted']
                item.record_result = update_summary_dict[item.id]['record_result']
                update_summary.append(item)
        
        update_record = []
        if update_record_dict:
            summary = await MachineTestRecord.filter(id__in=list(update_record_dict.keys())).all()
            for item in summary:
                item.record_deleted = update_record_dict[item.id]['record_deleted']
                update_record.append(item)
        
        async with in_transaction():
            # 批量新增主记录
            if insert_summary_obj_list:
                await MachineTestSummary.bulk_create(insert_summary_obj_list)

            # 批量更新主记录
            if update_summary:
                await MachineTestSummary.bulk_update(update_summary, fields=['record_deleted', 'record_result'])

            # 批量新增详情
            if insert_record_obj_list:
                await MachineTestRecord.bulk_create(insert_record_obj_list)

            # 批量更新详情
            if update_record:
                await MachineTestRecord.bulk_update(update_record, fields=['record_deleted'])


