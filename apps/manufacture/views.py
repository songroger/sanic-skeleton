from sanic.views import HTTPMethodView
# from sanic.response import json as sanicjson
from apps.manufacture.utils import DeliveryOrderOperation, SalesOrderOperation, checkDiffSalesAndDelivery
from core.base import ResponseCode, SalesOrderStateEnum, baseResponse
from core.utils import loadJsonConf
from .models import (Supplier, Material, BOM, BOMDetail, PoList, PoDetail, Order,
    OrderDetail, DeliveryOrder, DeliveryOrderDetail)
from tortoise import Tortoise
from tortoise.expressions import Q
from datetime import datetime, timedelta


class TodoSimple(HTTPMethodView):
    async def get(self, request, todo_id):
        data = {"todo": "todo_id"}
        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        args = request.json

        todo_id = args.get("task")
        conn = Tortoise.get_connection("default")

        val = await conn.execute_query_dict("SELECT * FROM company_base_info")

        return baseResponse(ResponseCode.OK, "success", {"task": todo_id})


class SupplierManager(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        company_name = request.args.get('company_name', "")

        supplier = await Supplier.filter(company_name__contains=company_name
                                        ).all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await Supplier.filter(company_name__contains=company_name
                                      ).all().count()

        data = {
            'supplier': [s.to_dict() for s in supplier],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        args = request.json

        _exist = await Supplier.filter(company_code=args.get("company_code"), identity=args.get("identity")).exists()
        if _exist and not args.get("id"):
            return baseResponse(ResponseCode.FAIL, "企业已存在", {})

        _ = await Supplier().create_or_update(args)

        return baseResponse(ResponseCode.OK, "success", {})

    async def delete(self, request):
        args = request.json

        _ = await Supplier().disable_or_not(args)

        return baseResponse(ResponseCode.OK, "success", {})


class MaterialManager(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        part_num = request.args.get('part_num', "")

        mate = await Material.filter(part_num__contains=part_num
                                    ).all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await Material.filter(part_num__contains=part_num).all().count()

        data = {
            'mate': [m.to_dict() for m in mate],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        args = request.json

        _exist = await Material.filter(part_num=args.get("part_num")).exists()
        if _exist and not args.get("id"):
            return baseResponse(ResponseCode.FAIL, "物料已存在", {})

        _ = await Material().create_or_update(args)

        return baseResponse(ResponseCode.OK, "success", {})

    async def delete(self, request):
        args = request.json

        _ = await Material().disable_or_not(args)

        return baseResponse(ResponseCode.OK, "success", {})


class BOMManager(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        part_num = request.args.get('part_num', "")

        bom = await BOM.filter(part_num__contains=part_num
                    ).all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await BOM.filter(part_num__contains=part_num
                    ).all().count()

        data = {
            'bom': [b.to_dict() for b in bom],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)


class BOMDetailView(HTTPMethodView):
    async def get(self, request):
        bom_id = int(request.args.get('bom_id'))

        detail = await BOMDetail.filter(primary_inner_id=bom_id)

        data = {
            'detail': [d.to_dict() for d in detail]
        }

        return baseResponse(ResponseCode.OK, "success", data)


class PoListView(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        supplier_name = request.args.get('supplier_name', "")
        supplier_code = request.args.get('supplier_code', "")
        po_code = request.args.get('po_code', "")
        start_datetime = request.args.get('start', "2024-01-01")
        end_datetime = datetime.strptime(request.args.get('end', "2050-12-01"), "%Y-%m-%d") + timedelta(days=1)

        po = await PoList.filter(supplier_name__contains=supplier_name,
                                 po_code__contains=po_code,
                                 supplier_code__contains=supplier_code,
                                 commit_time__gte=start_datetime,
                                 commit_time__lte=end_datetime.strftime("%Y-%m-%d")
                                 ).all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await PoList.filter(supplier_name__contains=supplier_name,
                                    po_code__contains=po_code,
                                    supplier_code__contains=supplier_code,
                                    commit_time__gte=start_datetime,
                                    commit_time__lte=end_datetime.strftime("%Y-%m-%d")
                                    ).all().count()

        data = {
            'po': [p.to_dict() for p in po],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)


class PODetailView(HTTPMethodView):
    async def get(self, request):
        # 采购单ID
        po_id = request.args.get('po_id')
        # 采购单号
        po_code = request.args.get('po_code')
        # 过滤采购单内容型号【0料架，1感应板】
        filter_model = request.args.get('filter_model', -1)

        print(filter_model, type(filter_model))
        if not po_id and not po_code:
            return baseResponse(ResponseCode.FAIL, "缺失查询参数!")
        if filter_model != -1 and str(filter_model) not in ['0', '1']:
            return baseResponse(ResponseCode.FAIL, "指定过滤类型错误!")
        
        filter_model = int(filter_model)

        query = PoList
        if po_id:
            query = query.filter(id=po_id)
        if po_code:
            query = query.filter(po_code=po_code)
        po_info = await query.order_by('-id').prefetch_related("details").first()
        if po_info:
            # 加载配置数据
            file_path = "data/mate_model_group.json"
            flag, data, msg = loadJsonConf(file_path=file_path)
            mate_model_list = []
            if flag:
                if filter_model == 0:
                    mate_model_list = data.get("machine", [])
                elif filter_model == 1:
                    mate_model_list = data.get("pcba", [])
            detail = []
            for item in po_info.details:
                if mate_model_list and item.mate_model not in mate_model_list:
                    continue
                item = item.to_dict()
                detail.append(item)
            data = {
                'detail': detail
            }
        else:
            data = {"detail": []}

        return baseResponse(ResponseCode.OK, "success", data)


class OrderView(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        finally_customer_name = request.args.get('supplier_name', "")
        sales_order_code = request.args.get('sales_order_code', "")
        customer_code = request.args.get('customer_code', "")
        start_datetime = request.args.get('start', "2024-01-01")
        end_datetime = datetime.strptime(request.args.get('end', "2050-12-01"), "%Y-%m-%d") + timedelta(days=1)

        order = await Order.filter(finally_customer_name__contains=finally_customer_name,
                                   sales_order_code__contains=sales_order_code,
                                   customer_code__contains=customer_code,
                                   delivery_time__gte=start_datetime,
                                   delivery_time__lte=end_datetime.strftime("%Y-%m-%d")
                                   ).all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await Order.filter(finally_customer_name__contains=finally_customer_name,
                                   sales_order_code__contains=sales_order_code,
                                   customer_code__contains=customer_code,
                                   delivery_time__gte=start_datetime,
                                   delivery_time__lte=end_datetime.strftime("%Y-%m-%d")
                                   ).all().count()

        data = {
            'order': [o.to_dict() for o in order],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        payload = request.json
        
        sales_order_code = payload.get("sales_order_code")
        contract_code = payload.get("contract_code")
        customer_code = payload.get("customer_code")
        customer_name = payload.get("customer_name")
        finally_customer_code = payload.get("finally_customer_code")
        finally_customer_name = payload.get("finally_customer_name")
        delivery_time = payload.get("delivery_time")
        commit_time = payload.get("commit_time")
        content = payload.get("content")
        
        order = Order(sales_order_code=sales_order_code, contract_code=contract_code, customer_code=customer_code, 
                      customer_name=customer_name, finally_customer_code=finally_customer_code, 
                      finally_customer_name=finally_customer_name, delivery_time=delivery_time, commit_time=commit_time)
        await order.save()
        data = []
        serial_num = 1
        for item in content:
            _pn = item.get("part_num")
            _model = item.get("mate_model")
            _desc = item.get("mate_desc")
            _qty = item.get("qty")
            _unit_name = item.get("unit_name")
            _remark = item.get("remark")
            data.append(OrderDetail(serial_num=serial_num, part_num=_pn, mate_model=_model, mate_desc=_desc, qty=_qty, primary_inner=order, unit_name=_unit_name, remark=_remark))
            serial_num += 1
        
        await OrderDetail.bulk_create(data)
        return baseResponse(ResponseCode.OK, msg="ok")

class OrderDetailView(HTTPMethodView):
    async def get(self, request):
        order_id = request.args.get('order_id')

        detail = await OrderDetail.filter(primary_inner_id=order_id).order_by('-id')

        data = {
            'detail': [d.to_dict() for d in detail]
        }

        return baseResponse(ResponseCode.OK, "success", data)


class DeliveryManage(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        customer_name = request.args.get("customer_name")
        delivery_order_code = request.args.get("delivery_order_code")
        start = request.args.get("start")
        end = request.args.get("end")

        bills = DeliveryOrder.all()
        if customer_name:
            bills = bills.filter(customer_name__contains=customer_name)
        if delivery_order_code:
            bills = bills.filter(customer_name__contains=delivery_order_code)
        if start:
            end = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
            bills = bills.filter(created_time__gte=start, created_time__lte=end)
        # print(bills.sql())
        bills = await bills.offset((page - 1) * per_page).limit(per_page)
        sales_list = []
        for item in bills:
            sales_list.append(item.sales_order_code)
        sales_map = await SalesOrderOperation.getInfosByOrderList(sales_order_list=sales_list)

        data_list = []
        for item in bills:
            sale_info = sales_map[item.sales_order_code]
            item = item.to_dict()
            item.update(delivery_time=sale_info.delivery_time.strftime("%Y-%m-%d"))
            data_list.append(item)
        total = await DeliveryOrder.all().count()

        data = {
            'data': data_list,
            'total': total,
            'page': page,
            'per_page': per_page
        }
        return baseResponse(ResponseCode.OK, "success", data=data)
    
    
    async def post(self, request):
        """
        新建出货单据
        """
        payload = request.json
        sales_order_code = payload.get("sales_order_code")
        content = payload.get("content")
        if not content:
            return baseResponse(ResponseCode.FAIL, msg="出货内容不能为空!")

        # 出货单号自动生成
        delivery_order_code = await DeliveryOrderOperation.generateDeliveryOrderCode(sales_order_code=sales_order_code)
        
        # 校验出货单内容与订单需求
        check_flag, check_msg = await checkDiffSalesAndDelivery(sales_order_code=sales_order_code, delivery_detail=content)
        if check_flag is False:
            return baseResponse(ResponseCode.FAIL, msg=check_msg)

        # 创建出货单数据
        payload.update(delivery_order_code=delivery_order_code)
        await DeliveryOrderOperation.createInfo(payload=payload)

        return baseResponse(ResponseCode.OK, msg="ok")


class DeliveryDetailManage(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        payload = request.args

        info = await DeliveryOrderOperation.getOrderInfo(payload)
        if not info:
            result = []
            total = 0
        else:
            bills = await DeliveryOrderDetail.filter(primary_inner_id=info.id).offset((page - 1) * per_page).limit(per_page)
            total = await DeliveryOrderDetail.all().count()
            result = [b.to_dict() for b in bills]
        data = {
            'data': result,
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)




