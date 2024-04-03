from sanic.views import HTTPMethodView
from core.base import baseResponse
# from manufacture.models import 


class Dashboard(HTTPMethodView):
    async def get(self, request):
        data = {}
        return baseResponse(200, "success", data)

    async def post(self, request):
        args = request.json

        todo_id = args.get("task")

        return baseResponse(200, "success", {"task": todo_id})

