import os

from dotenv import load_dotenv
from google import genai

import firebase_admin
from firebase_admin import credentials, firestore, auth

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
# FIREBASE AUTHENTICATION
# =========================================================

def verify_firebase_token():

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    id_token = auth_header.split(
        "Bearer ",
        1
    )[1].strip()

    if not id_token:
        return None

    try:

        decoded_token = auth.verify_id_token(
            id_token
        )

        return decoded_token

    except Exception as e:

        print(
            "Firebase Authentication Error:",
            e
        )

        return None


# =========================================================
# SAVE CHAT HISTORY
# =========================================================

def save_chat_history(
    user_uid,
    user_email,
    message,
    reply,
    language
):

    try:

        chat_data = {

            "message": message,

            "reply": reply,

            "language": language,

            "user_email": user_email,

            "timestamp":
                firestore.SERVER_TIMESTAMP
        }

        db.collection(
            "users"
        ).document(
            user_uid
        ).collection(
            "chats"
        ).add(
            chat_data
        )

        print(
            "Chat history saved for:",
            user_email
        )

    except Exception as e:

        print(
            "Chat History Save Error:",
            e
        )


# =========================================================
# LANGUAGE NAMES
# =========================================================

LANGUAGE_NAMES = {

    "en": "English",

    "ta": "Tamil",

    "tl":
        "Tanglish (Tamil written using English letters)"
}


# =========================================================
# HEALTHCARE QUESTION FILTER
# =========================================================

def is_healthcare_question(message):

    healthcare_keywords = [

        # GENERAL HEALTH

        "health",
        "healthy",
        "healthcare",
        "medical",
        "medicine",
        "medicines",
        "symptom",
        "symptoms",
        "disease",
        "diseases",
        "illness",
        "condition",
        "treatment",
        "doctor",
        "hospital",
        "clinic",
        "diagnosis",
        "diagnose",

        # COMMON SYMPTOMS

        "pain",
        "fever",
        "cold",
        "common cold",
        "cough",
        "coughing",
        "headache",
        "head pain",
        "migraine",
        "sneezing",
        "sneeze",
        "runny nose",
        "blocked nose",
        "itching",
        "itchy",
        "rash",
        "vomiting",
        "vomit",
        "diarrhea",
        "dizziness",
        "dizzy",
        "weakness",
        "tired",
        "fatigue",
        "breathing",
        "breath",
        "shortness of breath",
        "chest pain",
        "chest tightness",
        "stomach pain",
        "stomach ache",
        "abdominal pain",
        "stomach cramps",
        "sore throat",
        "throat pain",
        "swallowing",
        "body pain",
        "hand pain",
        "hand hurts",
        "hand ache",

        # MEDICAL CONDITIONS

        "asthma",
        "diabetes",
        "allergy",
        "allergies",
        "infection",
        "blood pressure",
        "high blood pressure",
        "low blood pressure",
        "hypertension",
        "heart disease",
        "heart problem",
        "lung disease",
        "anemia",
        "anaemia",
        "dengue",
        "flu",

        # BODY / HEALTH

        "skin",
        "skin problem",
        "eye",
        "eyes",
        "ear",
        "ears",
        "nose",
        "throat",
        "stomach",
        "heart",
        "lung",
        "lungs",
        "blood",
        "brain",
        "bone",
        "bones",
        "muscle",
        "muscles",
        "joint",
        "joints",
        "hand",
        "hands",
        "wrist",
        "finger",
        "fingers",

        # MEDICINE RELATED

        "tablet",
        "tablets",
        "capsule",
        "capsules",
        "drug",
        "drugs",
        "dosage",
        "dose",
        "side effect",
        "side effects",
        "prescription",
        "antibiotic",
        "antibiotics",
        "painkiller",
        "medicine allergy",

        # WOMEN'S HEALTH

        "pregnancy",
        "pregnant",
        "period",
        "periods",
        "menstrual",
        "menstruation",
        "pregnancy symptoms",

        # EMERGENCY / FIRST AID

        "emergency",
        "first aid",
        "bleeding",
        "seizure",
        "unconscious",
        "fainted",
        "fainting",
        "burn",
        "burns",
        "injury",
        "injured"
    ]

    message_lower = message.lower()

    return any(
        keyword in message_lower
        for keyword in healthcare_keywords
    )


# =========================================================
# QUESTION PATTERNS
# =========================================================

QUESTION_PATTERNS = {

    # HAND PAIN

    "hand pain": "hand_pain",
    "hand hurts": "hand_pain",
    "my hand hurts": "hand_pain",
    "pain in my hand": "hand_pain",
    "hand is hurting": "hand_pain",
    "my hand is hurting": "hand_pain",
    "hand ache": "hand_pain",
    "my hand is aching": "hand_pain",
    "pain on my hand": "hand_pain",

    # HEADACHE

    "headache": "headache",
    "head pain": "headache",
    "my head hurts": "headache",
    "head is hurting": "headache",
    "pain in my head": "headache",

    # STOMACH PAIN

    "stomach pain": "stomach_ache",
    "stomach ache": "stomach_ache",
    "my stomach hurts": "stomach_ache",
    "pain in my stomach": "stomach_ache",
    "stomach is hurting": "stomach_ache",
    "abdominal pain": "stomach_ache",
    "stomach cramps": "stomach_ache",

    # FEVER

    "fever": "fever",
    "i have fever": "fever",
    "high temperature": "fever",
    "my body is hot": "fever",

    # COUGH

    "cough": "cough",
    "coughing": "cough",
    "i am coughing": "cough",

    # SORE THROAT

    "sore throat": "sore_throat",
    "throat pain": "sore_throat",
    "my throat hurts": "sore_throat",
    "pain in my throat": "sore_throat",
    "pain while swallowing": "sore_throat",

    # ALLERGY

    "sneezing": "allergy",
    "runny nose": "allergy",
    "itchy eyes": "allergy",
    "skin rash": "allergy",
    "itching": "allergy",

    # ASTHMA

    "wheezing": "asthma",
    "shortness of breath": "asthma",
    "chest tightness": "asthma",

    # MIGRAINE

    "migraine": "migraine",

    # DENGUE

    "dengue": "dengue",
    "dengue fever": "dengue",
    "symptoms of dengue": "dengue",

    # FOOD POISONING

    "food poisoning": "food_poisoning",
    "vomiting": "food_poisoning",
    "diarrhea": "food_poisoning"
}


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# CHAT
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    # =====================================================
    # VERIFY FIREBASE LOGIN
    # =====================================================

    user = verify_firebase_token()

    if not user:

        return jsonify({

            "error":
                "Unauthorized. Please login first."

        }), 401


    # =====================================================
    # USER INFORMATION
    # =====================================================

    user_uid = user.get(
        "uid"
    )

    user_email = user.get(
        "email",
        ""
    )

    print("----------------------------------------")

    print(
        "Authenticated User:",
        user_email
    )

    print(
        "User UID:",
        user_uid
    )

    print("----------------------------------------")


    # =====================================================
    # GET REQUEST DATA
    # =====================================================

    data = request.get_json() or {}

    message = data.get(
        "message",
        ""
    ).strip()

    language = data.get(
        "language",
        "en"
    )


    # =====================================================
    # VALIDATE LANGUAGE
    # =====================================================

    if language not in LANGUAGE_NAMES:

        language = "en"

    language_name = LANGUAGE_NAMES[
        language
    ]


    # =====================================================
    # EMPTY MESSAGE
    # =====================================================

    if not message:

        empty_messages = {

            "en":
                "Please enter a health-related question.",

            "ta":
                "தயவுசெய்து உடல்நலம் தொடர்பான கேள்வியை உள்ளிடுங்கள்.",

            "tl":
                "Please health-related question enter pannunga."
        }

        return jsonify({

            "reply":
                empty_messages[language]

        })


    # =====================================================
    # HEALTHCARE FILTER
    # =====================================================

    if not is_healthcare_question(
        message
    ):

        non_healthcare_messages = {

            "en":
                "I'm MediGuide AI, a healthcare assistant. "
                "I can only answer health, medical, medicine, "
                "and symptom-related questions. "
                "Please ask a healthcare-related question.",

            "ta":
                "நான் MediGuide AI, ஒரு healthcare assistant. "
                "உடல்நலம், மருத்துவம், மருந்துகள் மற்றும் "
                "அறிகுறிகள் தொடர்பான கேள்விகளுக்கு மட்டும் "
                "பதிலளிக்க முடியும். "
                "தயவுசெய்து healthcare தொடர்பான கேள்வியை கேளுங்கள்.",

            "tl":
                "Naan MediGuide AI, oru healthcare assistant. "
                "Health, medical, medicine and symptom-related "
                "questions-ku mattum answer panna mudiyum. "
                "Please healthcare-related question kekkunga."
        }

        reply = non_healthcare_messages[
            language
        ]

        save_chat_history(
            user_uid,
            user_email,
            message,
            reply,
            language
        )

        return jsonify({

            "reply":
                reply

        })


    # =====================================================
    # LOWERCASE VERSION
    # =====================================================

    message_lower = message.lower()


    # =====================================================
    # FIND MEDICAL TOPIC
    # =====================================================

    document_id = None

    for pattern, doc_id in QUESTION_PATTERNS.items():

        if pattern in message_lower:

            document_id = doc_id

            break


    # =====================================================
    # FIRESTORE MEDICAL RESPONSE
    # =====================================================

    if document_id:

        try:

            doc = (
                db
                .collection(
                    "medical_knowledge"
                )
                .document(
                    document_id
                )
                .get()
            )

            if doc.exists:

                medical_data = doc.to_dict()

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


                # =========================================
                # ENGLISH
                # =========================================

                if language == "en":

                    reply = (
                        f"Possible Causes / Symptoms\n"
                        f"{symptoms}\n\n"
                        f"What You Can Do\n"
                        f"{advice}\n\n"
                        f"Warning Signs\n"
                        f"{warning}\n\n"
                        f"Note: This information is for general health guidance only."
                    )

                    


                # =========================================
                # TAMIL
                # =========================================

                elif language == "ta":

                    reply = (

                        f"### பொதுவான அறிகுறிகள்\n"
                        f"{symptoms}\n\n"

                        f"### என்ன செய்யலாம்\n"
                        f"{advice}\n\n"

                        f"### எச்சரிக்கை அறிகுறிகள்\n"
                        f"{warning}\n\n"

                        f"குறிப்பு: இது பொதுவான உடல்நல "
                        f"தகவலுக்காக மட்டுமே."
                    )


                # =========================================
                # TANGLISH
                # =========================================

                else:

                    reply = (

                        f"### Common Symptoms\n"
                        f"{symptoms}\n\n"

                        f"### Enna Pannalam\n"
                        f"{advice}\n\n"

                        f"### Warning Signs\n"
                        f"{warning}\n\n"

                        f"Note: Idhu general health "
                        f"information mattume."
                    )


                # =========================================
                # SAVE CHAT HISTORY
                # =========================================

                save_chat_history(
                    user_uid,
                    user_email,
                    message,
                    reply,
                    language
                )

                return jsonify({

                    "reply":
                        reply

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
You are MediGuide AI, a healthcare information assistant.

IMPORTANT:
You must ONLY answer healthcare, medical, medicine,
symptom, disease, treatment, or general health-related questions.

User question:
{message}

The user selected this language:
{language_name}


LANGUAGE INSTRUCTION:

- If the selected language is English, answer completely in simple English.
- If the selected language is Tamil, answer in clear and easy-to-understand Tamil.
- If the selected language is Tanglish, answer in natural Tanglish using English letters.
- Do not mix languages unnecessarily.


MEDICAL SAFETY RULES:

- Provide general health information only.
- Do not diagnose the user.
- Do not claim certainty about a medical condition.
- Do not prescribe medicines.
- Do not provide specific medication dosages.
- Do not tell the user to start or stop prescription medicines.
- Do not automatically tell the user to consult a doctor.
- Mention professional medical help only when there is a genuine reason.


EMERGENCY SAFETY:

If the user describes symptoms such as:

- severe difficulty breathing
- severe chest pain
- loss of consciousness
- severe bleeding
- seizures
- sudden severe weakness
- sudden confusion
- difficulty speaking
- rapidly worsening symptoms

advise the user to seek urgent medical attention.


ANSWER FORMAT:

Give the answer in a clean and professional format.

Use simple section headings without symbols.

Use these headings when relevant:

Possible Causes
What You Can Do
When to Seek Medical Help

Do not use Markdown symbols such as:
###
**
*
---
or bullet symbols.

Write each point as a separate simple line.

Keep the response short, clear, and easy to read.

Keep the response reasonably short.

Do not unnecessarily repeat the user's question.

Do not repeatedly say "consult a doctor".

Do not recommend prescription medicines or specific dosages.
"""


        response = client.models.generate_content(

            model="gemini-3-flash-preview",

            contents=prompt
        )

        reply = response.text


        # =================================================
        # SAVE GEMINI CHAT HISTORY
        # =================================================

        save_chat_history(
            user_uid,
            user_email,
            message,
            reply,
            language
        )


        return jsonify({

            "reply":
                reply

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


        reply = error_messages[
            language
        ]


        # =================================================
        # SAVE ERROR RESPONSE
        # =================================================

        save_chat_history(
            user_uid,
            user_email,
            message,
            reply,
            language
        )


        return jsonify({

            "reply":
                reply

        })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )