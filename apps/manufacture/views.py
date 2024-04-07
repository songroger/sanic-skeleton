from sanic.views import HTTPMethodView
# from sanic.response import json as sanicjson
from apps.manufacture.utils import DeliveryOrderOperation, SalesOrderOperation, checkDiffSalesAndDelivery
from core.base import ResponseCode, SalesOrderState, baseResponse
from .models import (Supplier, Material, BOM, BOMDetail, PoList, PoDetail, Order,
    OrderDetail, DeliveryOrder, DeliverayOrderDetail)


class TodoSimple(HTTPMethodView):
    async def get(self, request, todo_id):
        data = {"todo": "todo_id"}
        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        args = request.json

        todo_id = args.get("task")

        return baseResponse(ResponseCode.OK, "success", {"task": todo_id})


class SupplierManager(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        supplier = await Supplier.all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await Supplier.all().count()

        data = {
            'supplier': [s.to_dict() for s in supplier],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        args = request.json

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

        mate = await Material.all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await Material.all().count()

        data = {
            'mate': [m.to_dict() for m in mate],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        args = request.json

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

        bom = await BOM.all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await BOM.all().count()

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
        po_code = request.args.get('po_code', "")
        start_datetime = request.args.get('start', "2024-01-01")
        end_datetime = request.args.get('end', "2050-12-01")

        po = await PoList.filter(supplier_name__contains=supplier_name,
                                 po_code__contains=po_code,
                                 commit_time__gte=start_datetime,
                                 commit_time__lt=end_datetime
                                 ).all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await PoList.filter(supplier_name__contains=supplier_name,
                                    po_code__contains=po_code,
                                    commit_time__gte=start_datetime,
                                    commit_time__lt=end_datetime
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
        po_id = int(request.args.get('po_id'))

        detail = await PoDetail.filter(po_list_id=po_id).order_by('-id')

        data = {
            'detail': [d.to_dict() for d in detail]
        }

        return baseResponse(ResponseCode.OK, "success", data)


class OrderView(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        finally_customer_name = request.args.get('supplier_name', "")
        sales_order_code = request.args.get('sales_order_code', "")
        start_datetime = request.args.get('start', "2024-01-01")
        end_datetime = request.args.get('end', "2050-12-01")

        order = await Order.filter(finally_customer_name__contains=finally_customer_name,
                                   sales_order_code__contains=sales_order_code,
                                   delivery_time__gte=start_datetime,
                                   delivery_time__lt=end_datetime
                                   ).all().order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await Order.filter(finally_customer_name__contains=finally_customer_name,
                                   sales_order_code__contains=sales_order_code,
                                   delivery_time__gte=start_datetime,
                                   delivery_time__lt=end_datetime
                                   ).all().count()

        data = {
            'po': [o.to_dict() for o in order],
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

        detail = await OrderDetail.filter(order_id=order_id).order_by('-id')

        data = {
            'detail': [d.to_dict() for d in detail]
        }

        return baseResponse(ResponseCode.OK, "success", data)


class DeliverayManage(HTTPMethodView):
    async def get(self, request):
        # page = int(request.args.get('page', 1))
        # per_page = int(request.args.get('per_page', 10))

        # bills = await DeliveryOrder.all().offset((page - 1) * per_page).limit(per_page)
        # total = await DeliveryOrder.all().count()

        # data = {
        #     'data': [b.to_dict() for b in bills],
        #     'total': total,
        #     'page': page,
        #     'per_page': per_page
        # }
        # data = await DeliveryOrderOperation.getOrderInfo("S001-1")
        
        data = await DeliveryOrder.filter(delivery_order_code="S001-1").prefetch_related("details").first()
        if data:
            for item2 in data.details:
                print(item2, type(item2))

        return baseResponse(ResponseCode.OK, "success")
    
    
    async def post(self, request):
        """
        新建出货单据
        """
        payload = request.json
        # TODO 出货单号后续自动生成
        delivery_order_code = payload.get("delivery_order_code")
        sales_order_code = payload.get("sales_order_code")
        content = payload.get("content")

        # 出货单号自动生成
        
        # 校验出货单内容与订单需求
        check_flag, check_msg = await checkDiffSalesAndDelivery(sales_order_code=sales_order_code, delivery_detail=content)
        if check_flag is False:
            return baseResponse(ResponseCode.FAIL, msg=check_msg)

        # 创建出货单数据
        await DeliveryOrderOperation.createInfo(payload=payload)

        return baseResponse(ResponseCode.OK, msg="ok")


class DeliverayDetailManage(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        bills = await DeliverayDetailManage.all().offset((page - 1) * per_page).limit(per_page)
        total = await DeliverayDetailManage.all().count()

        data = {
            'data': [b.to_dict() for b in bills],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)
        
