import redis
from os import environ

# 初始化 Redis
redis_conn = redis.Redis(host=environ.get(
    "REDIS_ADDRESS"), port=environ.get("REDIS_PORT"), db=0)
