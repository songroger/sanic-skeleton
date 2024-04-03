import redis
from settings import settings

# 初始化 Redis
redis_conn = redis.Redis(host=settings.Data.get(
    "REDIS_ADDRESS"), port=settings.Data.get("REDIS_PORT"), db=0)

# MQ初始化创建
