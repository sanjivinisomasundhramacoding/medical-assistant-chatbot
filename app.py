import os

from dotenv import load_dotenv
from google import genai

import firebase_admin
from firebase_admin import credentials, firestore

from flask import Flask, render_template, request, jsonify


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# FIREBASE CONNECTION
# =========================================================

cred = credentials.Certificate("firebase-key.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()


# =========================================================
# GEMINI CONNECTION
# =========================================================

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set in the .env file"
    )

client = genai.Client(
    api_key=gemini_api_key
)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# LANGUAGE NAMES
# =========================================================

LANGUAGE_NAMES = {
    "en": "English",
    "ta": "Tamil",
    "tl": "Tanglish (Tamil written using English letters)"
}


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# CHAT
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json() or {}

    message = data.get("message", "").strip()

    language = data.get("language", "en")

    # -----------------------------------------------------
    # VALIDATE LANGUAGE
    # -----------------------------------------------------

    if language not in LANGUAGE_NAMES:
        language = "en"

    language_name = LANGUAGE_NAMES[language]

    # -----------------------------------------------------
    # EMPTY MESSAGE
    # -----------------------------------------------------

    if not message:

        empty_messages = {
            "en": "Please enter a health-related question.",
            "ta": "தயவுசெய்து உடல்நலம் தொடர்பான கேள்வியை உள்ளிடுங்கள்.",
            "tl": "Please health-related question enter pannunga."
        }

        return jsonify({
            "reply": empty_messages[language]
        })

    # -----------------------------------------------------
    # LOWERCASE VERSION
    # -----------------------------------------------------

    message_lower = message.lower()

    # =====================================================
    # FIRESTORE KEYWORDS
    # =====================================================

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

    # =====================================================
    # FIND MATCHING FIRESTORE DOCUMENT
    # =====================================================

    document_id = None

    for keyword, doc_id in keywords.items():

        if keyword in message_lower:

            document_id = doc_id
            break

    # =====================================================
    # FIRESTORE RESPONSE
    # =====================================================

    if document_id:

        try:

            doc = (
                db
                .collection("medical_knowledge")
                .document(document_id)
                .get()
            )

            if doc.exists:

                medical_data = doc.to_dict()

                topic = medical_data.get(
                    "topic",
                    "Unknown"
                )

                symptoms = medical_data.get(
                    "symptoms",
                    ""
                )

                advice = medical_data.get(
                    "general_advice",
                    ""
                )

                warning = medical_data.get(
                    "warning_signs",
                    ""
                )

                # -------------------------------------------------
                # ENGLISH
                # -------------------------------------------------

                if language == "en":

                    reply = (
                        f"It sounds like you may be experiencing "
                        f"{topic} symptoms.\n\n"

                        f"Common symptoms include: "
                        f"{symptoms}\n\n"

                        f"Advice: "
                        f"{advice}\n\n"

                        f"Warning signs: "
                        f"{warning}\n\n"

                        f"Please consult a healthcare professional "
                        f"for proper diagnosis and treatment."
                    )

                # -------------------------------------------------
                # TAMIL
                # -------------------------------------------------

                elif language == "ta":

                    reply = (
                        f"உங்களுக்கு {topic} தொடர்பான "
                        f"அறிகுறிகள் இருக்கலாம்.\n\n"

                        f"பொதுவான அறிகுறிகள்: "
                        f"{symptoms}\n\n"

                        f"ஆலோசனை: "
                        f"{advice}\n\n"

                        f"எச்சரிக்கை அறிகுறிகள்: "
                        f"{warning}\n\n"

                        f"சரியான diagnosis மற்றும் treatment-க்கு "
                        f"மருத்துவ நிபுணரை அணுகவும்."
                    )

                # -------------------------------------------------
                # TANGLISH
                # -------------------------------------------------

                else:

                    reply = (
                        f"Ungalukku {topic} symptoms "
                        f"irukkalaam.\n\n"

                        f"Common symptoms: "
                        f"{symptoms}\n\n"

                        f"Advice: "
                        f"{advice}\n\n"

                        f"Warning signs: "
                        f"{warning}\n\n"

                        f"Correct diagnosis and treatment-ku "
                        f"healthcare professional-a consult pannunga."
                    )

                return jsonify({
                    "reply": reply
                })

        except Exception as e:

            print(
                "Firestore Error:",
                e
            )

    # =====================================================
    # GEMINI RESPONSE
    # =====================================================

    try:

        prompt = f"""
You are MediGuide AI, a helpful medical information chatbot.

User question:
{message}

The user selected this language:
{language_name}


LANGUAGE INSTRUCTION:

- If the selected language is English, answer completely in simple English.
- If the selected language is Tamil, answer in clear and easy-to-understand Tamil.
- If the selected language is Tanglish, answer in natural Tanglish using English letters.
- Do not mix languages unnecessarily.
- Keep the answer concise and easy to understand.


MEDICAL SAFETY RULES:

- Provide general health information only.
- Do not diagnose the user.
- Do not claim certainty about a medical condition.
- Do not prescribe medicines.
- Do not provide specific medication dosages.
- Do not tell the user to start or stop prescription medicines.
- Encourage the user to consult a qualified healthcare professional when appropriate.


EMERGENCY SAFETY:

If the user describes emergency symptoms such as:

- severe difficulty breathing
- severe chest pain
- loss of consciousness
- severe bleeding
- seizures
- sudden severe weakness
- rapidly worsening symptoms

advise the user to seek urgent medical attention.


ANSWER STYLE:

- Use simple language.
- Be professional and friendly.
- Keep the response reasonably short.
- Use bullet points when helpful.
- Do not unnecessarily repeat the user's question.
"""

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        return jsonify({
            "reply": response.text
        })

    except Exception as e:

        print(
            "Gemini Error:",
            e
        )

        error_messages = {

            "en":
                "Sorry, I am unable to process your question right now. Please try again later.",

            "ta":
                "மன்னிக்கவும், உங்கள் கேள்வியை இப்போது செயல்படுத்த முடியவில்லை. சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கவும்.",

            "tl":
                "Sorry, unga question-a ippo process panna mudiyala. Konjam neram kazhichu again try pannunga."
        }

        return jsonify({
            "reply": error_messages[language]
        })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )