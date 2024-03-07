from sanic import Sanic
from sanic_auth import Auth

# Init Sanic APP
app = Sanic(__name__)

auth_instance = Auth()
