#!/usr/bin/python3
# encoding: utf-8
import argparse

from core.logger import logger
from apps.auth.views import auth_bp
from apps.manufacture.business_views import business_bp 
from apps.database.views import database_bp 
from tortoise.contrib.sanic import register_tortoise
from database import TORTOISE_ORM
from core.base import ServerErrorHandler
from settings import settings
from core.extentions.exceptions import handle_404
from core.extentions.middlewares import check_content_negotiation, jsonapi_standard_response_header
from apps import app, auth_instance
# from sanic_restful_api import Resource, Api
from apps.manufacture.views import (TodoSimple, SupplierManager, MaterialManager, BOMManager, BOMDetailView,
    PoListView, PODetailView, OrderView, OrderDetailView, DeliveryManage, DeliveryDetailManage)
from apps.manufacture.extra_views import MaterialImport, POImport, OrderImport, BOMImport
from apps.manufacture.open_api import CustomerCodeList, OrderCode
from apps.dashboard.views import dashboard_bp


app.config.update_config(settings)
auth_instance.setup(app)

app.error_handler = ServerErrorHandler()

# Install Apps
app.blueprint(auth_bp)
app.blueprint(business_bp)
app.blueprint(database_bp)
app.blueprint(dashboard_bp)

app.add_route(TodoSimple.as_view(), '/api/todo')
app.add_route(SupplierManager.as_view(), '/api/supplier')
app.add_route(MaterialManager.as_view(), '/api/material')
app.add_route(BOMManager.as_view(), '/api/bom_list')
app.add_route(BOMDetailView.as_view(), '/api/bom_detail')
app.add_route(PoListView.as_view(), '/api/po_list')
app.add_route(PODetailView.as_view(), '/api/po_detail')
app.add_route(OrderView.as_view(), '/api/order')
app.add_route(OrderDetailView.as_view(), '/api/order_detail')

app.add_route(MaterialImport.as_view(), '/api/mate_import')
app.add_route(POImport.as_view(), '/api/po_import')
app.add_route(OrderImport.as_view(), '/api/order_import')
app.add_route(BOMImport.as_view(), '/api/bom_import')

app.add_route(CustomerCodeList.as_view(), '/api/customer_code')
app.add_route(OrderCode.as_view(), '/api/order_code')

app.add_route(DeliveryManage.as_view(), '/api/delivery')
app.add_route(DeliveryDetailManage.as_view(), '/api/delivery_detail')


# Regist middleware & handler
app.register_middleware(check_content_negotiation, "request")
# app.register_middleware(jsonapi_standard_response_header, "response")
# app.error_handler.add(Exception, handle_404)

# Static dir
app.static('/', './static/index.html', name='index')
app.static('/static', './static/static', name='pc_static')
app.static('/favicon.ico', './static/static/favicon.ico', name='fav')

# restful_api init
# api = Api(app)
# api.add_resource(TodoSimple, '/api/todo')

register_tortoise(
    app,
    TORTOISE_ORM,
    generate_schemas=True
)


# Command line parser options & setup default values
parser = argparse.ArgumentParser()
parser.add_argument(
    '--host', help='Setup host ip to listen up, default to 0.0.0.0', default='0.0.0.0')
parser.add_argument(
    '--port', help='Setup port to attach, default to 8093', type=int, default=8093)
parser.add_argument(
    '--workers', help='Setup workers to run, default to 1', type=int, default=1)
parser.add_argument('--debug', help='Enable or disable debugging',
                    default=True, action='store_true')
parser.add_argument('--accesslog', help='Enable or disable access log',
                    default=True, action='store_true')
args = parser.parse_args()


if __name__ == "__main__":
    app.run(
        host=args.host,
        port=args.port,
        workers=args.workers,
        debug=args.debug,
        access_log=args.accesslog
    )
