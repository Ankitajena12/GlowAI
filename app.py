from flask import Flask, request, jsonify,render_template
from supabase import create_client
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# 🧠 ROUTINE GENERATOR
# -------------------------------
def generate_routine(profile):
    routine = {"morning": [], "night": []}

    skin_type = profile.get("skin_type", "")
    concerns = profile.get("concerns", [])
    sensitivity = profile.get("sensitivity", False)

    # Morning
    if skin_type == "oily":
        routine["morning"].append("Gel Cleanser")
    else:
        routine["morning"].append("Gentle Cleanser")

    routine["morning"].append("Moisturizer")
    routine["morning"].append("Sunscreen (SPF 30+)")

    # Night
    if "acne" in concerns:
        routine["night"].append("Salicylic Acid")

    if "dark spots" in concerns:
        routine["night"].append("Niacinamide")

    if sensitivity:
        routine["night"].append("Soothing Moisturizer")

    return routine


# -------------------------------
# ⚠️ CONFLICT CHECKER
# -------------------------------
def check_conflicts(products):
    conflicts = []

    products = [p.lower() for p in products]

    if "retinol" in products and "aha" in products:
        conflicts.append("Avoid using Retinol with AHA")

    if "vitamin c" in products and "niacinamide" in products:
        conflicts.append("Use Vitamin C and Niacinamide at different times")

    return conflicts


# -------------------------------
# 🧴 INGREDIENT ANALYZER (basic)
# -------------------------------
ingredient_db = {
    "salicylic acid": {
        "good_for": ["acne", "oily skin"],
        "risk": "low"
    },
    "retinol": {
        "good_for": ["anti-aging", "acne"],
        "risk": "medium"
    }
}

def analyze_ingredient(name):
    return ingredient_db.get(name.lower(), {"message": "Unknown ingredient"})


# -------------------------------
# 👤 SAVE USER PROFILE
# -------------------------------
@app.route("/save-profile", methods=["POST"])
def save_profile():
    data = request.json
    supabase.table("users").insert(data).execute()
    return jsonify({"message": "Profile saved"})


# -------------------------------
# 🧴 GET ROUTINE
# -------------------------------
@app.route("/routine", methods=["POST"])
def routine():
    profile = request.json
    return jsonify(generate_routine(profile))


# -------------------------------
# 💬 CHATBOT
# -------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful skincare assistant."},
            {"role": "user", "content": user_input}
        ]
    )

    return jsonify({
        "reply": response.choices[0].message.content
    })


# -------------------------------
# ⚠️ CONFLICT CHECK API
# -------------------------------
@app.route("/conflicts", methods=["POST"])
def conflicts():
    products = request.json.get("products", [])
    return jsonify({"conflicts": check_conflicts(products)})


# -------------------------------
# 🧪 INGREDIENT ANALYZER API
# -------------------------------
@app.route("/ingredient", methods=["POST"])
def ingredient():
    name = request.json.get("name")
    return jsonify(analyze_ingredient(name))


# -------------------------------
# 📍 DERMATOLOGIST LIST (MVP)
# -------------------------------
@app.route("/dermatologists", methods=["GET"])
def dermatologists():
    return jsonify([
        {"name": "Dr. Sharma", "mode": "Offline", "city": "Kolkata"},
        {"name": "Dr. Roy", "mode": "Online", "platform": "Teleconsult"}
    ])


# -------------------------------
# 📊 PROGRESS TRACKER
# -------------------------------
@app.route("/track", methods=["POST"])
def track():
    data = request.json
    supabase.table("progress").insert(data).execute()
    return jsonify({"message": "Progress saved"})


# -------------------------------
# 🏠 HOME ROUTE
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------------
# ▶️ RUN APP
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True)