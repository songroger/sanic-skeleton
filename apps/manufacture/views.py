from sanic.views import HTTPMethodView
# from sanic.response import json as sanicjson
from core.base import baseResponse
from .models import (Supplier, Material, BOM, BOMDetail, PoList, PoDetail, Order,
    OrderDetail, DeliveryOrder, DeliverayOrderDetail


class TodoSimple(HTTPMethodView):
    async def get(self, request, todo_id):
        data = {"todo": "todo_id"}
        return baseResponse(200, "success", data)

    async def post(self, request):
        args = request.json

        todo_id = args.get("task")

        return baseResponse(200, "success", {"task": todo_id})


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

        return baseResponse(200, "success", data)

    async def post(self, request):
        args = request.json

        _ = await Supplier().create_or_update(args)

        return baseResponse(200, "success", {})

    async def delete(self, request):
        args = request.json

        _ = await Supplier().disable_or_not(args)

        return baseResponse(200, "success", {})


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

        return baseResponse(200, "success", data)

    async def post(self, request):
        args = request.json

        _ = await Material().create_or_update(args)

        return baseResponse(200, "success", {})

    async def delete(self, request):
        args = request.json

        _ = await Material().disable_or_not(args)

        return baseResponse(200, "success", {})


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

        return baseResponse(200, "success", data)


class BOMDetailView(HTTPMethodView):
    async def get(self, request):
        bom_id = int(request.args.get('bom_id'))

        detail = await BOMDetail.filter(primary_inner_id=bom_id)

        data = {
            'detail': [d.to_dict() for d in detail]
        }

        return baseResponse(200, "success", data)


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

        return baseResponse(200, "success", data)


class PODetailView(HTTPMethodView):
    async def get(self, request):
        po_id = int(request.args.get('po_id'))

        detail = await PoDetail.filter(po_list_id=po_id).order_by('-id')

        data = {
            'detail': [d.to_dict() for d in detail]
        }

        return baseResponse(200, "success", data)


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

        return baseResponse(200, "success", data)


class OrderDetailView(HTTPMethodView):
    async def get(self, request):
        order_id = request.args.get('order_id')

        detail = await OrderDetail.filter(order_id=order_id).order_by('-id')

        data = {
            'detail': [d.to_dict() for d in detail]
        }

        return baseResponse(200, "success", data)


class DeliverayManage(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        bills = await DeliveryOrder.all().offset((page - 1) * per_page).limit(per_page)
        total = await DeliveryOrder.all().count()

        data = {
            'data': [b.to_dict() for b in bills],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(200, "success", data)
    
    async def post(self, request):
        payload = request.json
        """
        
        """
        


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

        return baseResponse(200, "success", data)
        
