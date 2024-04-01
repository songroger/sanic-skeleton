from sanic.views import HTTPMethodView
# from sanic.response import json as sanicjson
from core.base import baseResponse
from .models import Supplier


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
            'data': [s.to_dict() for s in supplier],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(200, "success", data)

