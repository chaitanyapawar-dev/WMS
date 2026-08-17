"""
migrate_to_atlas.py — Copy all local MongoDB collections & data to MongoDB Atlas.

Usage:
    python migrate_to_atlas.py "<YOUR_ATLAS_MONGODB_URL>"

Example:
    python migrate_to_atlas.py "mongodb+srv://admin:pass123@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority"
"""

import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

LOCAL_URL = os.getenv("LOCAL_MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "WMS")

def migrate(atlas_url: str):
    print("=" * 60)
    print("🚀 Starting MongoDB Migration: Local -> Atlas")
    print("=" * 60)
    print(f"📦 Source (Local) : {LOCAL_URL}")
    print(f"🎯 Target (Atlas) : {atlas_url.split('@')[-1] if '@' in atlas_url else 'Atlas Cluster'}")
    print(f"📁 Database Name  : {DATABASE_NAME}\n")

    try:
        source_client = MongoClient(LOCAL_URL, serverSelectionTimeoutMS=5000)
        source_client.admin.command('ping')
        print("✅ Connected to Local MongoDB successfully.")
    except Exception as e:
        print(f"❌ Failed to connect to Local MongoDB ({LOCAL_URL}):\n   {e}")
        return

    try:
        target_client = MongoClient(atlas_url, serverSelectionTimeoutMS=10000)
        target_client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully.\n")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas:\n   {e}")
        print("\n💡 Tip: Check username/password, and make sure IP Access List in Atlas has 0.0.0.0/0 allowed.")
        return

    src_db = source_client[DATABASE_NAME]
    tgt_db = target_client[DATABASE_NAME]

    collections = src_db.list_collection_names()
    # Filter out system collections if any
    collections = [c for c in collections if not c.startswith("system.")]

    if not collections:
        print(f"⚠️ No collections found in local database '{DATABASE_NAME}'.")
        return

    print(f"Found {len(collections)} collections to migrate: {', '.join(collections)}\n")

    total_docs = 0
    for coll_name in collections:
        src_coll = src_db[coll_name]
        tgt_coll = tgt_db[coll_name]

        docs = list(src_coll.find({}))
        count = len(docs)

        if count == 0:
            print(f"  • [{coll_name}] 0 documents (skipped)")
            continue

        print(f"  • Migrating [{coll_name}] ({count} documents)...", end="", flush=True)

        # Clear target collection to prevent duplicate key errors with pre-seeded data
        tgt_coll.delete_many({})

        # Insert all documents from local
        tgt_coll.insert_many(docs)

        print(f" Done! ({count} transferred)")
        total_docs += count

    print("\n" + "=" * 60)
    print(f"🎉 Migration Complete! Successfully migrated {total_docs} documents across {len(collections)} collections.")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_atlas_url = sys.argv[1].strip()
    else:
        # Check if ATLAS_MONGODB_URL or MONGODB_URL is in .env (if it's an atlas url)
        env_url = os.getenv("ATLAS_MONGODB_URL") or os.getenv("MONGODB_URL")
        if env_url and "mongodb+srv://" in env_url:
            target_atlas_url = env_url
        else:
            target_atlas_url = input("Enter your MongoDB Atlas Connection String:\n> ").strip()

    if not target_atlas_url:
        print("❌ Error: No Atlas MongoDB URL provided.")
        sys.exit(1)

    migrate(target_atlas_url)
