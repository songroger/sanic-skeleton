from sanic.views import HTTPMethodView
from core.base import baseResponse
from .models import Order


class CustomerCodeList(HTTPMethodView):

    async def get(self, request):
        """
        state:2 已完结单
        return: 供应商代码列表
        """
        order = await Order.filter(state__not_in=[2]).all()

        data = {
            'customer_code': [o.customer_code for o in order]
        }

        return baseResponse(200, "success", data)


class OrderCode(HTTPMethodView):

    async def get(self, request):
        """
        return: 订单号
        """
        customer_code = request.args.get('customer_code', "")
        order = await Order.filter(customer_code=customer_code).all().order_by('-id')

        data = {
            'sales_order_code': [o.sales_order_code for o in order]
        }

        return baseResponse(200, "success", data)
