from sanic.views import HTTPMethodView
# from sanic.response import json as sanicjson
from core.base import baseResponse


class TodoSimple(HTTPMethodView):
    async def get(self, request, todo_id):
        data = {"todo": "todo_id"}
        return baseResponse(200, "success", data)

    async def post(self, request):
        args = request.json

        todo_id = args.get("task")

        return baseResponse(200, "success", {"task": todo_id})
