import xlrd
from sanic.views import HTTPMethodView
from core.base import baseResponse, ResponseCode
from .utils import parse_mate_data, parse_bom_data, parse_po_data, parse_order_data


class MaterialImport(HTTPMethodView):

    async def post(self, request):
        upload_file = request.files.get('file')

        file_name = upload_file.name

        # 解析数据写入数据库
        ret = await parse_mate_data(upload_file)

        return baseResponse(ResponseCode.OK, "success", {})


class BOMImport(HTTPMethodView):

    async def post(self, request):
        upload_file = request.files.get('file')

        file_name = upload_file.name

        # 解析数据写入数据库
        ret = await parse_bom_data(upload_file)

        return baseResponse(ResponseCode.OK, "success", {})


class POImport(HTTPMethodView):

    async def post(self, request):
        upload_file = request.files.get('file')

        file_name = upload_file.name

        # 解析数据写入数据库
        ret, msg = await parse_po_data(upload_file)
        if not ret:
            return baseResponse(ResponseCode.FAIL, msg, {})

        return baseResponse(ResponseCode.OK, "success", {})


class OrderImport(HTTPMethodView):

    async def post(self, request):
        upload_file = request.files.get('file')

        file_name = upload_file.name

        # 解析数据写入数据库
        ret, msg = await parse_order_data(upload_file)
        if not ret:
            return baseResponse(ResponseCode.FAIL, msg, {})

        return baseResponse(ResponseCode.OK, "success", {})
