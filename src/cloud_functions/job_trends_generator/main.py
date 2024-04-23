import logging
import json
import base64
import concurrent.futures
import numpy as np
import functions_framework
from datetime import datetime
from sklearn.cluster import KMeans
from google.cloud import bigquery
from google.cloud import storage
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import VertexAI

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET_NAME = "job-ai-jobs-input-data"
BQ_RESULTS_TABLE = "jobai-420303.jobai_data.job_category_summary"
JOBS_CHUNK_SIZE = 4
KMEANS_CLUSTER_NUM = 16


def clustering(vectors, num_clusters=12, random_state=42):
    kmeans = KMeans(n_clusters=num_clusters, random_state=random_state).fit(vectors)
    closest_indices = []
    for i in range(num_clusters):
        distances = np.linalg.norm(vectors - kmeans.cluster_centers_[i], axis=1)
        closest_index = np.argmin(distances)
        closest_indices.append(closest_index)
    selected_indices = sorted(closest_indices)
    return selected_indices


def download_from_gcs(bucket, blob_name):
    logging.info(f"Downloading {blob_name} from bucket {BUCKET_NAME}")
    contents = bucket.blob(blob_name).download_as_bytes()
    return [json.loads(content) for content in contents.decode("utf-8").split("\n") if content.strip() != ""]


def get_datasets(category):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    executors = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    
    records = []
    blob_names = [x.name for x in storage_client.list_blobs(BUCKET_NAME, prefix=f"embeddings/{category}")]
    futures = (executors.submit(download_from_gcs, bucket, blob) for blob in blob_names)
    for future in concurrent.futures.as_completed(futures):
        records.extend(future.result())
    executors.shutdown()
    return records


def get_datasets_local():
    """ Test function to load datasets locally for local run to save time. """
    records = []
    for blob_name in ["tmp/data1.json", "tmp/data2.json"]:
        f = open(blob_name, "r", encoding="utf-8")
        for line in f:
            if line.strip() != "":
                records.append(json.loads(line))
        f.close()
    return records


def generate_results(records):
    candidates = clustering([x["ml_generate_embedding_result"] for x in records], KMEANS_CLUSTER_NUM)
    selected_jobs = []
    for i in range(0, min(KMEANS_CLUSTER_NUM, len(candidates)), JOBS_CHUNK_SIZE):
        jds = []
        for j in range(i, min(i + JOBS_CHUNK_SIZE, len(candidates))):
            jds.append(records[candidates[j]]["content"])
        selected_jobs.append("\n\n".join(jds))
    
    jobs = [Document(page_content=x) for x in selected_jobs]
    
    palm2_llm = VertexAI(
        model_name="text-bison@002",
        max_output_tokens=1024,
        temperature=0.5,
        top_p=0.9
    )
    map_prompt_template = """
        Write a summary that includes some market trends or insights and most common skills based on the following job details.
        {text}
    """
    map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])
    
    combine_prompt_template = """
        Write a concise summary of the following text delimited by triple backquotes.
        The summary must list the top 5 market trends with elaboration and the top 10 most common skills.
        Return a JSON document with a "trends" and a "skills" property, following this structure: {{"trends": ["trend"], "skills": ["skill"]}}.
        The "trends" property must not have more than 5 elements, and "skills" property must not have more than 10 elements.
        Return only JSON, without any markdown markup surrounding it. Do not include duplicate information.
        Here is the text:
        ---
        ```{text}```
        ---
        JSON: 
    """
    combine_prompt = PromptTemplate(template=combine_prompt_template, input_variables=["text"])
    
    map_reduce_chain = load_summarize_chain(
        palm2_llm,
        chain_type="map_reduce",
        map_prompt=map_prompt,
        combine_prompt=combine_prompt,
        return_intermediate_steps=False,
    )
    map_reduce_outputs = map_reduce_chain({"input_documents": jobs})
    result = map_reduce_outputs["output_text"].strip()
    if result.startswith("```"):
        result = result[result.find("\n") + 1 : -3]
    return result


def upload_results(category, results):
    bq_client = bigquery.Client()
    errors = bq_client.insert_rows_json(BQ_RESULTS_TABLE, [{"category": category, "summary": results, "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}])
    if errors:
        logging.error(f"Encountered errors while inserting rows: {errors}")
        raise Exception("Unable to insert results into BigQuery.")


@functions_framework.cloud_event
def main(cloud_event):
    payload = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8"))
    dataset_prefix = payload["dataset_prefix"]
    category = payload["category"]
    records = get_datasets(dataset_prefix)  # get_datasets_local()
    results = generate_results(records)
    logger.info(results)
    upload_results(category, results)
