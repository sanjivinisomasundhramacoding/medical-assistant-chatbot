import os
from dotenv import load_dotenv
from google import genai
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, jsonify

# Load environment variables
load_dotenv()

# Firebase connection
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Gemini connection
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file")

client = genai.Client(api_key=gemini_api_key)

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip().lower()

    if not message:
        return jsonify({
            "reply": "Please enter a health-related question."
        })

    # Keywords mapped to Firestore document IDs
    keywords = {
        # Allergy
        "sneezing": "allergy",
        "runny nose": "allergy",
        "itchy eyes": "allergy",
        "skin rash": "allergy",
        "itching": "allergy",

        # Asthma
        "wheezing": "asthma",
        "shortness of breath": "asthma",
        "chest tightness": "asthma",

        # Migraine
        "migraine": "migraine",

        # Fever
        "fever": "fever",
        "high temperature": "fever",

        # Cough
        "cough": "cough",
        "coughing": "cough",

        # Headache
        "headache": "headache",
        "head pain": "headache",

        # Stomach Ache
        "stomach ache": "stomach_ache",
        "stomach pain": "stomach_ache",
        "abdominal pain": "stomach_ache",
        "stomach cramps": "stomach_ache",

        # Food Poisoning
        "food poisoning": "food_poisoning",
        "vomiting": "food_poisoning",
        "diarrhea": "food_poisoning",

        # Sore Throat
        "sore throat": "sore_throat",
        "throat pain": "sore_throat",
        "pain while swallowing": "sore_throat"
    }

    # Find matching Firestore document
    document_id = None

    for keyword, doc_id in keywords.items():
        if keyword in message:
            document_id = doc_id
            break

    # ------------------------------------------------
    # 1. FIRESTORE RESPONSE
    # ------------------------------------------------
    if document_id:
        doc = db.collection("medical_knowledge").document(document_id).get()

        if doc.exists:
            medical_data = doc.to_dict()

            topic = medical_data.get("topic", "Unknown")
            symptoms = medical_data.get("symptoms", "")
            advice = medical_data.get("general_advice", "")
            warning = medical_data.get("warning_signs", "")

            reply = (
                f"It sounds like you may be experiencing "
                f"{topic} symptoms.\n\n"
                f"Common symptoms include: {symptoms}\n\n"
                f"Advice: {advice}\n\n"
                f"Warning signs: {warning}\n\n"
                f"Please consult a healthcare professional for proper "
                f"diagnosis and treatment."
            )

            return jsonify({"reply": reply})

    # ------------------------------------------------
    # 2. GEMINI RESPONSE FOR OTHER QUESTIONS
    # ------------------------------------------------
    try:
        prompt = f"""
You are a helpful medical information chatbot.

User question:
{message}

Give general health information in simple and clear language.

Important safety rules:
- Do not diagnose the user.
- Do not claim certainty about a medical condition.
- Do not prescribe medicines or give specific medication dosages.
- Encourage the user to consult a qualified healthcare professional
  when appropriate.
- If the user describes emergency symptoms such as severe difficulty
  breathing, severe chest pain, loss of consciousness, severe bleeding,
  seizures, or a rapidly worsening condition, advise them to seek
  urgent medical attention.

Keep the answer concise and easy to understand.
"""

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        return jsonify({
            "reply": response.text
        })

    except Exception as e:
        print("Gemini Error:", e)

        return jsonify({
            "reply": (
                "Sorry, I am unable to process your question right now. "
                "Please try again later."
            )
        })


if __name__ == "__main__":
    app.run(debug=True)