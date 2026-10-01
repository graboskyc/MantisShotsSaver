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

SHOTURL = "https://train.mantisx.com/itarget/user-shots-csv/" + os.environ["USERNAME"].strip() + "/"
SESSIONURL = "https://train.mantisx.com/itarget/user-sessions-csv/" + os.environ["USERNAME"].strip() + "/"


def import_shots_last_day():
    lastDayUrl = SHOTURL + "?start_date=" + (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + "&end_date=" + datetime.now().strftime("%Y-%m-%d")
    updated_sessions = parse_shots_csv(lastDayUrl)
    return {"imported": len(updated_sessions) if updated_sessions else 0, "urlUsed": lastDayUrl}

def import_sessions_last_day():
    lastDayUrl = SESSIONURL + "?start_date=" + (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + "&end_date=" + datetime.now().strftime("%Y-%m-%d")
    parse_sessions_csv(lastDayUrl)
    return {"imported": "last_day", "urlUsed": lastDayUrl}

scheduler.add_job(
    import_shots_last_day,
    trigger=CronTrigger(hour=0, minute=0),
    id='import_shots_job',
    replace_existing=True
)
scheduler.add_job(
    import_sessions_last_day,
    trigger=CronTrigger(hour=0, minute=0),
    id='import_sessions_job',
    replace_existing=True
)
scheduler.start()

@api_app.get("/sessions")
async def get_sessions(skip: int = 0, limit: int = 10):
    sessions = list(col.find().sort("date", -1).skip(skip).limit(limit))
    return json.loads(dumps(sessions))

@api_app.get("/stats/shots-over-time")
async def get_shots_over_time():
    pipeline = [
        {"$project": {
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
            "shot_count": {"$size": {"$ifNull": ["$shots", []]}}
        }},
        {"$group": {
            "_id": "$date",
            "total_shots": {"$sum": "$shot_count"}
        }},
        {"$sort": {"_id": 1}}
    ]
    results = list(col.aggregate(pipeline))
    return results

@api_app.get("/stats/session-scores")
async def get_session_scores():
    # Pipeline to get min, max, open, close (first/last) scores per session
    pipeline = [
        {"$unwind": "$shots"},
        {"$match": {"shots.Score": {"$ne": None}}},
        {"$group": {
            "_id": "$_id",
            "date": {"$first": "$date"},
            "open": {"$first": "$shots.Score"},
            "close": {"$last": "$shots.Score"},
            "min": {"$min": "$shots.Score"},
            "max": {"$max": "$shots.Score"}
        }},
        {"$sort": {"date": 1}},
        {"$project": {
            "_id": 0,
            "x": {"$dateToString": {"format": "%Y-%m-%d %H:%M", "date": "$date"}},
            "y": ["$open", "$min", "$max", "$close"]
        }}
    ]
    results = list(col.aggregate(pipeline))
    return results

@api_app.get("/stats/average-accuracy")
async def get_average_accuracy():
    pipeline = [
        {"$unwind": "$shots"},
        {"$project": {
            "is_hit": {"$cond": [{"$gt": ["$shots.Score", 0]}, 1, 0]}
        }},
        {"$group": {
            "_id": None,
            "avg_accuracy": {"$avg": "$is_hit"}
        }}
    ]
    result = list(col.aggregate(pipeline))
    if not result:
        return {"accuracy": 0}
    return {"accuracy": round(result[0]["avg_accuracy"] * 100, 2)}

@api_app.get("/stats/average-shot-time")
async def get_average_shot_time():
    pipeline = [
        {"$unwind": "$shots"},
        {"$group": {
            "_id": None,
            "avg_time": {"$avg": "$shots.Time"}
        }}
    ]
    result = list(col.aggregate(pipeline))
    if not result or result[0]["avg_time"] is None:
        return {"time": 0}
    return {"time": round(result[0]["avg_time"], 2)}

@api_app.get("/stats/shot-distribution")
async def get_shot_distribution():
    pipeline = [
        {"$unwind": "$shots"},
        {"$project": {
            "_id": 0,
            "x": {"$floor": {"$multiply": ["$shots.Position X", 10]}},
            "y": {"$floor": {"$multiply": ["$shots.Position Y", 10]}}
        }},
        {"$group": {
            "_id": {"x": "$x", "y": "$y"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "x": "$_id.x",
            "y": "$_id.y",
            "count": 1
        }}
    ]
    # Restructure for heatmap: group by x, then list of y:count
    results = list(col.aggregate(pipeline))
    heatmap_data = []
    # Simplified approach: return raw grouped data if the frontend handles it or pre-aggregate
    return results

@api_app.get("/stats/shot-consistency")
async def get_shot_consistency():
    pipeline = [
        {"$unwind": "$shots"},
        {"$group": {
            "_id": "$session_id",
            "date": {"$first": "$date"},
            "avg_score": {"$avg": "$shots.Score"},
            "std_dev": {"$stdDevPop": "$shots.Score"}
        }},
        {"$sort": {"date": 1}},
        {"$project": {"_id": 0, "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "avg_score": 1, "std_dev": 1}}
    ]
    return list(col.aggregate(pipeline))

@api_app.get("/stats/drill-performance")
async def get_drill_performance():
    pipeline = [
        {"$unwind": "$shots"},
        {"$group": {
            "_id": "$drill_name",
            "avg_score": {"$avg": "$shots.Score"},
            "avg_time": {"$avg": "$shots.Time"}
        }},
        {"$project": {"_id": 0, "drill": "$_id", "avg_score": 1, "avg_time": 1}}
    ]
    return list(col.aggregate(pipeline))

@api_app.get("/stats/time-accuracy-correlation")
async def get_time_accuracy_correlation():
    pipeline = [
        {"$unwind": "$shots"},
        {"$project": {"_id": 0, "x": "$shots.Time", "y": "$shots.Score"}}
    ]
    return list(col.aggregate(pipeline))

@api_app.get("/hello")
async def hello():
    return {"message": "Hello World"}

@api_app.get("/importSessionsAll")
async def import_all_sessions():
    allSessionHistoryUrl = SESSIONURL + "?start_date=2025-12-01&end_date=" + datetime.now().strftime("%Y-%m-%d")
    parse_sessions_csv(allSessionHistoryUrl)
    return {"imported": "all", "urlUsed": allSessionHistoryUrl}

@api_app.get("/importSessionsLastDay")
async def import_sessions_last_day():
    lastDayUrl = SESSIONURL + "?start_date=" + (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + "&end_date=" + datetime.now().strftime("%Y-%m-%d")
    parse_sessions_csv(lastDayUrl)
    return {"imported": "last_day", "urlUsed": lastDayUrl}

@api_app.get("/importShotsAll")
async def import_all_shots():
    allShotHistoryUrl = SHOTURL + "?start_date=2025-12-01&end_date=" + datetime.now().strftime("%Y-%m-%d")
    shots = parse_shots_csv(allShotHistoryUrl)
    if shots:
        for shot in shots:
            col.update_one({"session_id": shot["session_id"]}, {"$set": shot}, upsert=True)
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
            col.update_one(
                {"session_id": session_id},
                {"$set": {
                    "session_id": session_id,
                    "date": content["date"],
                    "image": content["image"],
                    "targets": content["targets"],
                    "shots": content["shots"]
                }},
                upsert=True
            )
            result.append(session_id)
            
        return result
    finally:
        if not isinstance(f, io.StringIO):
            f.close()

def parse_sessions_csv(source):
    """
    Parses a sessions CSV file from a file path or URL and upserts into MongoDB.
    """
    if source.startswith(('http://', 'https://')):
        response = requests.get(source)
        response.raise_for_status()
        f = io.StringIO(response.text)
    else:
        f = open(source, 'r', encoding='utf-8')
    
    try:
        reader = csv.reader(f)
        header = None
        for row in reader:
            if row and row[0] == 'ID':
                header = row
                break
        
        if not header:
            return None
        
        for row in reader:
            if not row:
                continue
            data = dict(zip(header, row))
            session_id = data['ID']
            session_data = {
                "session_id": session_id,
                "date": datetime.fromisoformat(data['Date'].replace('Z', '+00:00')),
                "targets": json.loads(data['Targets']),
                "start_time": datetime.fromisoformat(data['Start Time'].replace('Z', '+00:00')),
                "end_time": datetime.fromisoformat(data['End Time'].replace('Z', '+00:00')),
                "par_time": float(data['Par Time']),
                "drill_name": data['Drill Name'],
                "num_players": int(data['Num Players']),
                "target_distance_yards": float(data['Target Distance Yards']),
                "view_aspect": float(data['View Aspect']),
            }
            col.update_one(
                {"session_id": session_id}, 
                {"$set": session_data}, 
                upsert=True
            )
    finally:
        if not isinstance(f, io.StringIO):
            f.close()
