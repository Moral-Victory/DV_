# mongodb_setup.py - Helper script to verify MongoDB connection and setup
from pymongo import MongoClient
import sys
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def check_mongodb_connection(uri=None):
    """Check if MongoDB is available and create test database/collection"""
    # Use environment variable or default
    if uri is None:
        uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    
    try:
        print(f"Attempting to connect to MongoDB at {uri}...")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Test the connection
        server_info = client.server_info()
        print(f"✅ Connected to MongoDB version {server_info.get('version')}")
        
        # Create and test database
        db = client["maintenance_db"]
        collection = db["machine_data"]
        
        # Insert test document
        test_id = collection.insert_one({"test": "connection", "timestamp": time.time()}).inserted_id
        print(f"✅ Successfully inserted test document with ID: {test_id}")
        
        # Clean up test document
        collection.delete_one({"_id": test_id})
        print("✅ Test document removed")
        
        # Print collection stats
        doc_count = collection.count_documents({})
        print(f"Current document count in machine_data collection: {doc_count}")
        
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def setup_indexes():
    """Create indexes for better query performance"""
    try:
        # Use environment variable or default
        uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client["maintenance_db"]
        collection = db["machine_data"]
        
        # Create indexes
        print("Creating indexes for better performance...")
        collection.create_index("Type")
        collection.create_index("prediction")
        collection.create_index([("Rotational speed [rpm]", 1)])
        
        print("✅ Indexes created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create indexes: {e}")
        return False

def main():
    # Check if MongoDB is installed and running
    if not check_mongodb_connection():
        print("\nTroubleshooting tips:")
        print("1. Make sure MongoDB is installed")
        print("2. Check if MongoDB service is running")
        print("3. Verify that MongoDB is listening on localhost:27017")
        print("\nAlternative options:")
        print("- Set MONGODB_URI environment variable to your MongoDB connection string")
        print("- The application will fallback to file-based storage if MongoDB is unavailable")
        sys.exit(1)
    
    # Setup indexes for better performance
    setup_indexes()
    
    print("\n🎉 MongoDB is properly configured and ready for use with your application!")
    print("You can now run your FastAPI backend and Streamlit frontend.")

if __name__ == "__main__":
    main()