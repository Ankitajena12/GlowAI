from flask import Flask, request, jsonify, render_template
from rag_engine import engine

app = Flask(__name__)
engine.load()  # loads once when server starts

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data     = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "No question provided"}), 400

    result = engine.ask(question)

    return jsonify({
        "answer":  result["answer"],
        "sources": result["sources"],
        "time":    result["time_taken"]
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)