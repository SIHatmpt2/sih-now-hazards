import json
from redis import asyncio as redis
from apps.core.config import get_settings
class RedisCache:
    def __init__(self):self.client=redis.from_url(get_settings().redis_url,decode_responses=True)
    async def get_json(self,key):
        try:v=await self.client.get(key);return json.loads(v) if v else None
        except Exception:return None
    async def set_json(self,key,value,ttl):
        if ttl<=0:return
        try:await self.client.set(key,json.dumps(value,default=str),ex=ttl)
        except Exception:return
    async def ping(self):
        try:return bool(await self.client.ping())
        except Exception:return False
