from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from google import genai
import uuid
import json
import os

# =========================
# APP SETUP
# =========================
app = Flask(__name__)
CORS(app)

# =========================
# MONGODB
# =========================
client = MongoClient("mongodb+srv://rr8807837_db_user:raja44raja@cluster0.jstxelp.mongodb.net/")
db = client["smart_resume_builder"]
collection = db["users"]

# =========================
# 🔥 GEMINI AI SETUP (NEW SDK)
# =========================

GEMINI_API_KEY = "AIzaSyD1BxeOrH-gNR4geEh9CDezv-YUwfUz5YY"   # 👈 PUT YOUR KEY HERE

client_ai = genai.Client(api_key=GEMINI_API_KEY)

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/analyzerpage")
def analyzer_page():
    return render_template("analyzer.html")

@app.route("/interviewpage")
def interview_page():
    return render_template("interview.html")

@app.route("/generatorpage")
def generator_page():
    return render_template("generator.html")

@app.route("/loginpage")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")
# =========================
# LOGIN API
# =========================
#@app.route("/login", methods=["POST"])
#def login():
    #data = request.get_json()

    #collection.insert_one({
        #"username": data["username"],
        #"email": data["email"],
        #"password": data["password"]
    #})

    #return jsonify({"message":"Login Successful"})
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data["username"]
    email = data["email"]
    password = data["password"]

    # CHECK USER EXISTS

    existing_user = collection.find_one({

        "email":email,
        "password":password

    })

    # IF USER EXISTS

    if existing_user:

        token = existing_user.get("token")

        # CREATE TOKEN IF NOT EXISTS

        if not token:

            token = str(uuid.uuid4())

            collection.update_one(

                {"email":email},

                {
                    "$set":{
                        "token":token
                    }
                }
            )

        return jsonify({

            "success":True,
            "message":"Login Successful",
            "token":token

        })

    # CREATE NEW USER

    else:

        token = str(uuid.uuid4())

        collection.insert_one({

            "username":username,
            "email":email,
            "password":password,
            "token":token

        })

        return jsonify({

            "success":True,
            "message":"Account Created Successfully",
            "token":token

        })
@app.route("/check_user", methods=["POST"])
def check_user():

    data = request.get_json()

    email = data["email"]

    user = collection.find_one({

        "email":email

    })

    if user:

        return jsonify({

            "exists":True

        })

    else:

        return jsonify({

            "exists":False

        })
# =========================
# AI RESUME ANALYZER (FIXED)
# =========================
@app.route("/analyze_resume", methods=["POST"])
def analyze_resume():

    data = request.get_json()
    resume_text = data.get("text", "")

    if not resume_text.strip():
        return jsonify({"error": "Empty resume text"}), 400

    prompt = f"""
You are an expert ATS resume analyzer.

Return ONLY valid JSON.

Keep answers SHORT and CLEAN (max 1 line per field, max 5–8 improvements only).

Resume:
{resume_text}

Return format:
{{
  "ats_score": 0,
  "summary": "short 1-2 lines only",
  "skills": ["max 6 skills"],
  "strengths": ["max 4 points"],
  "weaknesses": ["max 4 points"],
  "improvements": ["max 5 short actionable points"],
  "job_fit": "Good / Average / Poor"
}}
"""

    try:
        # ✅ NEW SDK CALL
        response = client_ai.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )

        result_text = response.text.strip()

        # clean markdown if any
        result_text = result_text.replace("```json", "").replace("```", "")

        result_json = json.loads(result_text)

        return jsonify(result_json)

    except Exception as e:
        return jsonify({
            "error": "AI parsing failed",
            "details": str(e)
        }), 500

@app.route("/generate_interview_questions", methods=["POST"])
def generate_interview_questions():

    try:

        data = request.get_json()

        resume_text = data.get("text", "")

        if not resume_text.strip():
            return jsonify({
                "error": "Empty resume text"
            }), 400

        prompt = f"""
You are an interview expert.
Generate  10 short one line interview questions
based on this resume.
Return ONLY plain text.
One question per line.
Resume:
{resume_text}
"""

        response = client_ai.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )

        result_text = response.text.strip()

        print(result_text)

        questions = []

        for line in result_text.split("\n"):

            line = line.strip()

            if line:

                # remove numbering
                line = line.replace("1.", "")
                line = line.replace("2.", "")
                line = line.replace("3.", "")
                line = line.replace("4.", "")
                line = line.replace("5.", "")
                line = line.replace("6.", "")
                line = line.replace("7.", "")
                line = line.replace("8.", "")
                line = line.replace("9.", "")
                line = line.replace("10.", "")

                questions.append(line.strip())

        return jsonify({
            "questions": questions
        })

    except Exception as e:

        print(str(e))

        return jsonify({
            "error": "AI generation failed",
            "details": str(e)
        }), 500
# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
