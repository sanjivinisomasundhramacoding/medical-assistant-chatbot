import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

docs = db.collection("medical_knowledge").stream()

data = []

for doc in docs:
    row = doc.to_dict()
    row["id"] = doc.id
    data.append(row)

df = pd.DataFrame(data)

df.to_csv("medical_knowledge.csv", index=False, encoding="utf-8-sig")

print("CSV created successfully!")