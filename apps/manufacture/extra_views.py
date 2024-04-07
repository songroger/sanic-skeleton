import xlrd
from sanic.views import HTTPMethodView
from core.base import baseResponse
from .utils import parse_mate_data, parse_bom_data, parse_po_data, parse_order_data


class MaterialImport(HTTPMethodView):

    async def post(self, request):
        upload_file = request.files.get('file')

        file_name = upload_file.name

        # 解析数据写入数据库
        ret = await parse_mate_data(upload_file)

        return baseResponse(200, "success", {})


class BOMImport(HTTPMethodView):

    async def post(self, request):
        upload_file = request.files.get('file')

        file_name = upload_file.name

        # 解析数据写入数据库
        ret = await parse_bom_data(upload_file)

        return baseResponse(200, "success", {})


class POImport(HTTPMethodView):

    async def post(self, request):
        upload_file = request.files.get('file')

        file_name = upload_file.name

        # 解析数据写入数据库
        ret = await parse_po_data(upload_file)

        return baseResponse(200, "success", {})


class OrderImport(HTTPMethodView):

    async def post(self, request):
        upload_file = request.files.get('file')

        file_name = upload_file.name

        # 解析数据写入数据库
        ret = await parse_order_data(upload_file)

        return baseResponse(200, "success", {})
