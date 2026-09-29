from fastapi import FastAPI, Response
import pymongo
import datetime
from bson.json_util import dumps
from bson.timestamp import Timestamp
from bson.objectid import ObjectId
from fastapi.staticfiles import StaticFiles
import json
import os
import requests
from typing import Dict, Any
from fastapi.middleware.cors import CORSMiddleware

api_app = FastAPI(title="api-app")
app = FastAPI(title="spa-app")
app.mount("/api", api_app)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

#client = pymongo.MongoClient(os.environ["MDBCONNSTR"].strip())
#db = client[""]
#col = db[""]

@api_app.get("/hello")
async def hello():
    return {"message": "Hello World"}
