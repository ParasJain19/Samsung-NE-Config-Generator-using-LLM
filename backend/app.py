from flask import Flask, request, jsonify 
from rag_pipeline import answer_question
from flask_cors import CORS
import time 

app = Flask(__name__)
CORS(app)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("question", "")
    mode = data.get("mode", "factual")  # Optional mode

    if not query:
        return jsonify({"error": "Empty query"}), 400

    print(f"[INFO] Received question: {query}, Mode: {mode}")

    start_time = time.time()  #  Start timer

    answer = answer_question(query, mode=mode)

    end_time = time.time()  #  End timer
    elapsed = round(end_time - start_time, 3)
    print(f"[INFO] Total retrieval + generation time: {elapsed} seconds")

    return jsonify({
        "answer": answer,
        "time_taken": f"{elapsed} sec"
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

