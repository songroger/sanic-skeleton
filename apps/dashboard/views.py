from sanic.views import HTTPMethodView
from core.base import ResponseCode, baseResponse
# from manufacture.models import 


class Dashboard(HTTPMethodView):
    async def get(self, request):
        data = {}
        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        args = request.json

        todo_id = args.get("task")

        return baseResponse(ResponseCode.OK, "success", {"task": todo_id})

