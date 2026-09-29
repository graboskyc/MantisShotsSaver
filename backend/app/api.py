from fastapi import FastAPI, Response
import pymongo
from datetime import datetime, timedelta
from bson.json_util import dumps
import csv
import io
import json
import requests
from collections import defaultdict
from bson.objectid import ObjectId
from fastapi.staticfiles import StaticFiles
import json
import os
import requests
from typing import Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

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

scheduler = BackgroundScheduler()
client = pymongo.MongoClient(os.environ["MDBCONNSTR"].strip())
db = client["mantis"]
col = db["shots"]

url = os.environ["BASEURL"].strip()

def import_shots_last_day():
    lastDayUrl = url + "?start_date=" + (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + "&end_date=" + datetime.now().strftime("%Y-%m-%d")
    shots = parse_shots_csv(lastDayUrl)
    if shots:
        col.insert_many(shots)
    return {"imported": len(shots) if shots else 0, "urlUsed": lastDayUrl}

scheduler.add_job(
    import_shots_last_day,
    trigger=CronTrigger(hour=0, minute=0),
    id='import_shots_job',
    replace_existing=True
)
scheduler.start()

@api_app.get("/sessions")
async def get_sessions(skip: int = 0, limit: int = 10):
    sessions = list(col.find().sort("date", -1).skip(skip).limit(limit))
    return json.loads(dumps(sessions))

@api_app.get("/hello")
async def hello():
    return {"message": "Hello World"}

@api_app.get("/importShotsAll")
async def import_all_shots():
    allShotHistoryUrl = url + "?start_date=2025-12-01&end_date=" + datetime.now().strftime("%Y-%m-%d")
    shots = parse_shots_csv(allShotHistoryUrl)
    if shots:
        col.insert_many(shots)
    return {"imported": len(shots) if shots else 0, "urlUsed": allShotHistoryUrl}

@api_app.get("/importShotsLastDay")
async def import_shots_last_day_endpoint():
    return import_shots_last_day()
    

def parse_shots_csv(source):
    """
    Parses a shots CSV file from a file path or URL, grouping shots by Session ID.
    """
    if source.startswith(('http://', 'https://')):
        response = requests.get(source)
        response.raise_for_status()
        f = io.StringIO(response.text)
    else:
        f = open(source, 'r', encoding='utf-8')
    
    try:
        sessions = defaultdict(lambda: {"shots": [], "date": None})
        
        # Skip lines until we find the header row (starting with 'Session ID')
        reader = csv.reader(f)
        header = None
        for row in reader:
            if row and row[0] == 'Session ID':
                header = row
                break
        
        if not header:
            return None

        # Parse data rows
        for row in reader:
            if not row:
                continue
            
            data = dict(zip(header, row))
            
            session_id = data['Session ID']
            session_date = datetime.fromisoformat(data['Date'].replace('Z', '+00:00'))
            image = data['Image']
            targets = json.loads(data['Targets'])
            
            # Parse date (only set once per session)
            if sessions[session_id]["date"] is None:
                sessions[session_id]["date"] = session_date
            
            # Parse numbers
            shot = {
                "Score": float(data['Score']),
                "Player Index": int(data['Player Index']),
                "Index": int(data['Index']),
                "Position X": float(data['Position X']),
                "Position Y": float(data['Position Y']),
                "Time": float(data['Time'])
            }
            
            sessions[session_id]["shots"].append(shot)
            sessions[session_id]["image"] = image
            sessions[session_id]["targets"] = targets
            
        # Convert to a list of objects ready for MongoDB
        result = []
        for session_id, content in sessions.items():
            result.append({
                "session_id": session_id,
                "date": content["date"],
                "image": content["image"],
                "targets": content["targets"],
                "shots": content["shots"]
            })
            
        return result
    finally:
        if not isinstance(f, io.StringIO):
            f.close()
