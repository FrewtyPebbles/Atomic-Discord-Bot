import pymongo
from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client = AsyncIOMotorClient(getenv("DB_HOST"))
db = mongo_client[getenv("DB_NAME")]