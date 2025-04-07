import firebase_admin
from firebase_admin import credentials , firestore

# Load Firebase credentials
cred = credentials.Certificate("flask-mini-firebase-adminsdk-fbsvc-74af769c18.json")

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# If you previously had firebase_config, remove it.
db = firestore.client()