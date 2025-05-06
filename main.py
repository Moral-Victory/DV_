from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pickle
import pandas as pd
import numpy as np
from pymongo import MongoClient
from typing import List, Dict, Any
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import random
import os
import json

app = FastAPI(title="Predictive Maintenance API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
# Get MongoDB connection from environment variable or use default
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("MONGODB_DB", "maintenance_db")
COLLECTION_NAME = os.environ.get("MONGODB_COLLECTION", "machine_data")

DATA_FILE = "machine_data.json"  # For fallback file-based storage

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Test connection
    client.server_info()
    print(f"✅ Connected to MongoDB at {MONGODB_URI}")
    use_mongodb = True
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    print("Using fallback to JSON file storage.")
    # Fallback to file-based storage
    # Initialize empty data file if it doesn't exist
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    use_mongodb = False

# Load the trained model
try:
    with open("model.pkl", "rb") as file:
        model = pickle.load(file)
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    # Create a dummy model for demonstration
    class DummyModel:
        def predict(self, X):
            return np.random.choice([0, 1], size=len(X))
    model = DummyModel()
    print("⚠️ Warning: model.pkl not found. Using dummy model instead.")

class MachineData(BaseModel):
    Type: int = Field(..., description="Machine type (0, 1, or 2)")
    Air_temperature_K: float = Field(..., description="Air temperature in Kelvin")
    Process_temperature_K: float = Field(..., description="Process temperature in Kelvin")
    Rotational_speed_rpm: float = Field(..., description="Rotational speed in RPM")
    Torque_Nm: float = Field(..., description="Torque in Nm")
    Tool_wear_min: float = Field(..., description="Tool wear in minutes")

class MachineDataBatch(BaseModel):
    data: List[MachineData]

# File-based storage functions (fallback)
def get_all_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data_list):
    with open(DATA_FILE, "w") as f:
        json.dump(data_list, f, indent=2)

@app.post("/predict", response_model=Dict[str, Any])
async def predict(data: MachineData):
    try:
        # Create DataFrame with updated column names
        df = pd.DataFrame([{
            "Type": data.Type,
            "Air temperature [K]": data.Air_temperature_K,
            "Process temperature [K]": data.Process_temperature_K,
            "Rotational speed [rpm]": data.Rotational_speed_rpm,
            "Torque [Nm]": data.Torque_Nm,
            "Tool wear [min]": data.Tool_wear_min
        }])
        
        prediction = int(model.predict(df)[0])
        
        # Store data and prediction
        record = df.iloc[0].to_dict()
        record["prediction"] = prediction
        
        if use_mongodb:
            collection.insert_one(record)
        else:
            all_data = get_all_data()
            all_data.append(record)
            save_data(all_data)
        
        return {"prediction": prediction, "failure": bool(prediction)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_data", response_model=Dict[str, Any])
async def generate_data(count: int = 100):
    try:
        generated_data = []
        
        for _ in range(count):
            machine_type = random.choice([0, 1, 2])
            air_temp = round(random.uniform(295, 304), 1)
            process_temp = round(random.uniform(305, 313), 1)
            rotational_speed = round(random.uniform(1000, 2500))
            torque = round(random.uniform(3.5, 77), 2)
            tool_wear = round(random.uniform(0, 253))
            
            data = {
                "Type": machine_type,
                "Air temperature [K]": air_temp,
                "Process temperature [K]": process_temp,
                "Rotational speed [rpm]": rotational_speed,
                "Torque [Nm]": torque,
                "Tool wear [min]": tool_wear
            }
            
            # Convert to DataFrame for prediction
            df = pd.DataFrame([data])
            prediction = int(model.predict(df)[0])
            
            # Add prediction to the data
            data["prediction"] = prediction
            
            # Store data
            if use_mongodb:
                collection.insert_one(data)
            else:
                generated_data.append(data)
            
        if not use_mongodb:
            all_data = get_all_data()
            all_data.extend(generated_data)
            save_data(all_data)
        
        return {"message": f"Generated {count} data points", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data", response_model=Dict[str, Any])
async def get_data(limit: int = 10000):
    try:
        if use_mongodb:
            data = list(collection.find({}, {"_id": 0}).limit(limit))
        else:
            data = get_all_data()
            # Apply limit
            data = data[-limit:] if len(data) > limit else data
        
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear_data", response_model=Dict[str, Any])
async def clear_data():
    try:
        if use_mongodb:
            result = collection.delete_many({})
            deleted_count = result.deleted_count
        else:
            all_data = get_all_data()
            deleted_count = len(all_data)
            save_data([])
        
        return {"message": f"Deleted {deleted_count} data points"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if not os.path.exists("model.pkl"):
    class DummyModel:
        def predict(self, X):
            return np.random.choice([0, 1], size=len(X))
    model = DummyModel()
    print("⚠️ Warning: model.pkl not found. Using dummy model instead.")

