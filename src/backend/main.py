import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery
from vertexai.preview.language_models import TextEmbeddingModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)

TRENDS_CACHE = {}
BQ_EMBEDDINGS_TABLE = "jobai-420303.jobai_data.job_data_embeddings"
BQ_JOBS_TABLE = "jobai-420303.jobai_data.job_data_deduplicated"

bq_client = bigquery.Client()
embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko")


@app.route("/trends", methods=["GET"])
def get_trends():
    global TRENDS_CACHE
    if TRENDS_CACHE and (datetime.now() - TRENDS_CACHE["last_updated"]).total_seconds() < 3600:
        logging.info("Return trends from memory cache.")
        return jsonify({"data": TRENDS_CACHE["summaries"]})
    
    query = f"""
        SELECT category, ANY_VALUE(summary HAVING MAX created_at) AS summary
        FROM `jobai-420303.jobai_data.job_category_summary`
        GROUP BY category
    """
    data = [
        {"category": row["category"], "summary": json.loads(row["summary"])} for row in bq_client.query_and_wait(query)
    ]
    TRENDS_CACHE = {"last_updated": datetime.now(), "summaries": data}
    
    return jsonify({"data": data})


@app.route("/recommendations", methods=["POST"])
def get_recommendations():
    top_k = int(request.args.get('topk', 5))
    if top_k > 10 or top_k <= 0 or not request.data:
        logger.info("Received invalid payload from user.")
        return jsonify({"error": "Invalid top_k parameter or empty payload."}), 400
    
    embedding = embedding_model.get_embeddings([request.data.decode("utf-8")])[0].values
    recommend_jobs_ids_query = f"""
      SELECT base.id as id FROM VECTOR_SEARCH(
        TABLE `{BQ_EMBEDDINGS_TABLE}`,
        'ml_generate_embedding_result',
        (SELECT {str(embedding)} as ml_generate_embedding_result),
        top_k => {top_k},
        distance_type => 'COSINE',
        options => '{{"use_brute_force":true}}'
      )
    """   
    recommend_jobs_ids = bq_client.query(recommend_jobs_ids_query)
    recommend_jobs_ids = [row["id"] for row in recommend_jobs_ids.result()]
    top_jobs_ids = ", ".join(f"\"{x}\"" for x in recommend_jobs_ids)
    logger.info(f"Job recommendations: {top_jobs_ids}")
    
    recommend_jobs_data_query = f"""
      SELECT id, title, company, url 
      FROM `{BQ_JOBS_TABLE}` 
      WHERE id IN ({top_jobs_ids})
    """
    recommend_jobs = bq_client.query(recommend_jobs_data_query)
    
    return jsonify(
        {"data": [{"id": row["id"], "title": row["title"], "company": row["company"], "url": row["url"]} for row in recommend_jobs.result()]}
    )


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "UP"})


if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0', debug=True)
