import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery
from vertexai.preview.language_models import TextEmbeddingModel
from vertexai.language_models import TextGenerationModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)

TRENDS_CACHE = {}
BQ_EMBEDDINGS_TABLE = "jobai-420303.jobai_data.job_data_embeddings"
BQ_JOBS_TABLE = "jobai-420303.jobai_data.job_data_deduplicated"
BQ_JOBS_SUMMARY_TABLE = "jobai-420303.jobai_data.job_category_summary"

bq_client = bigquery.Client()
embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko")
ll_text_model = TextGenerationModel.from_pretrained("text-bison")


@app.route("/trends", methods=["GET"])
def get_trends():
    global TRENDS_CACHE
    if TRENDS_CACHE and (datetime.now() - TRENDS_CACHE["last_updated"]).total_seconds() < 3600:
        logging.info("Return trends from memory cache.")
        return jsonify({"data": TRENDS_CACHE["summaries"]})
    
    query = f"""
        SELECT category, ANY_VALUE(summary HAVING MAX created_at) AS summary
        FROM `{BQ_JOBS_SUMMARY_TABLE}`
        GROUP BY category
    """
    data = [
        {"category": row["category"], "summary": json.loads(row["summary"])} 
        for row in bq_client.query_and_wait(query)
    ]
    TRENDS_CACHE = {"last_updated": datetime.now(), "summaries": data}
    
    return jsonify({"data": data})


@app.route("/recommendations", methods=["POST"])
def get_recommendations():
    top_k = int(request.args.get('topk', 5))
    if top_k > 10 or top_k <= 0 or not request.data:
        logger.info("Received invalid payload from user.")
        return jsonify({"error": "Invalid topk parameter (> 0 and <= 10) or empty payload."}), 400
    
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
        SELECT id, title, company, url, categories 
        FROM `{BQ_JOBS_TABLE}` 
        WHERE id IN ({top_jobs_ids})
    """
    recommend_jobs = bq_client.query(recommend_jobs_data_query)
    
    return jsonify({"data": [
        {"id": row["id"], "title": row["title"], "company": row["company"], "url": row["url"], "categories": json.loads(row["categories"])} 
        for row in recommend_jobs.result()
    ]})


@app.route("/questions/<id>", methods=["GET"])
def generate_interview_questions(id):
    job_query = f"""
        SELECT company, company_description, title, description, skills, other_requirements 
        FROM {BQ_JOBS_TABLE}
        WHERE id = "{id}"
    """
    data = [row for row in bq_client.query_and_wait(job_query)]
    if not data:
        logging.info(f"Unable to get job {id} from table.")
        return jsonify({"error": "No such job in our records."}), 404
    data = data[0]
    
    prompt_template = f"""
        Generate 5 interview questions for the following job. Those questions should be specific to the company business and the company values and the role requirements.
        Return a JSON document with a "questions" property, following this structure: {{"questions": ["question"]}}.
        Do not include duplicate information.
        
        Here is the job:
        ---
        Title: {data["title"]}
        Company: {data["company"]}
        Job description: {data["description"]}
        Company description: {data["company_description"] or "N/A"}
        Skills: {", ".join(json.loads(data["skills"]))}
        Other requirements: {data["other_requirements"] or "N/A"}
        ---
        JSON:
    """

    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 1024,
        "temperature": 0.9,
        "top_p": 0.9
    }
    resp = ll_text_model.predict(prompt_template, **parameters).text.strip()
    logging.info(type(resp))
    logging.info(resp[:4])
    if resp.startswith("```"):
        logging.info("yes!!")
        resp = resp[resp.find("\n") + 1 : -3]
    resp = json.loads(resp)
    return jsonify({"data": resp["questions"]})


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "UP"})


if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0', debug=True)
