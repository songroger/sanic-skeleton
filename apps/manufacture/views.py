from sanic.views import HTTPMethodView
# from sanic.response import json as sanicjson
from core.base import baseResponse
from .models import Supplier, Material, BOM, BOMDetail


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

        supplier = await Supplier.all().offset((page - 1) * per_page).limit(per_page)
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

        supplier = await Supplier().create_or_update(args)

        return baseResponse(200, "success", {})

    async def delete(self, request):
        args = request.json

        supplier = await Supplier().disable_or_not(args)

        return baseResponse(200, "success", {})


class MaterialManager(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        mate = await Material.all().offset((page - 1) * per_page).limit(per_page)
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

        supplier = await Material().create_or_update(args)

        return baseResponse(200, "success", {})

    async def delete(self, request):
        args = request.json

        supplier = await Material().disable_or_not(args)

        return baseResponse(200, "success", {})


class BOMManager(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        bom = await BOM.all().offset((page - 1) * per_page).limit(per_page)
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
