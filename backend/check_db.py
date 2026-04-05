import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()
firebase_creds_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
if firebase_creds_path and os.path.exists(firebase_creds_path):
    print(f"Initializing Firebase Admin with {firebase_creds_path}...")
    cred = credentials.Certificate(firebase_creds_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    docs = db.collection("entries").stream()
    count = 0
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict().get('user_id')}, {doc.to_dict().get('summary')}")
        count += 1
    print(f"Total documents: {count}")
else:
    print("Firebase not configured properly")
