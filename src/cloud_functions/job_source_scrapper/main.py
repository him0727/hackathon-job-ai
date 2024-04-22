import logging
import json
import time
import random
import concurrent.futures
import requests
import functions_framework
from bs4 import BeautifulSoup
from google.cloud import bigquery

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_HOST = "https://api.mycareersfuture.gov.sg/v2"
BQ_RAW_DATA_TABLE = "jobai-420303.jobai_data.job_data_raw"


def process(start_page, end_page, limit, chunk_size):
    cnt = 0
    bq_client = bigquery.Client()
    results = []
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    for jobs in scrape_jobs(start_page, end_page, limit):
        futures = (executor.submit(process_job, job) for job in jobs)
        for future in concurrent.futures.as_completed(futures):
            data = future.result()
            if data is not None:
                results.append(data)
        if len(results) >= chunk_size:
            bigquery_insert(bq_client, results)
            results.clear()
        cnt += 1
        if cnt % 4 == 0:
            time.sleep(random.randint(1, 3))
    if len(results) > 0:
        bigquery_insert(bq_client, results)
    executor.shutdown()


def scrape_jobs(page, end_page, limit):
    while page <= end_page:
        logging.info(f"Processing page {page}")
        succeed = True
        try:
            resp = requests.post(f"{API_HOST}/search?limit={limit}&page={page}", json={"sessionId":"","postingCompany":[],"sortBy":["new_posting_date"]})
        except Exception as e:
            logging.error(f"Failed to scrape page: ${page}, limit: {limit}, error: {e}")
            succeed = False
        finally:
            page += 1
        if not succeed:
            continue
        if resp.status_code != 200:
            logging.error(f"Failed to scrape page: ${page}, limit: {limit}, error: {resp.text}")
            continue
        resp = resp.json()
        if len(resp["results"]) == 0:
            break
        yield resp["results"]


def scrape_jd(uuid):
    resp = requests.get(f"{API_HOST}/jobs/{uuid}")
    if resp.status_code != 200:
        logging.error(f"Failed to scrape JD: ${uuid}, response: {resp.text}")
        return None
    return resp.json()


def process_job(job):
    try:
        record = {
            "id": job["uuid"],
            "post_id": job["metadata"]["jobPostId"],
            "title": job["title"],
            "company": job["postedCompany"]["name"],
            "url": job["metadata"]["jobDetailsUrl"],
            "categories": [x["category"] for x in job["categories"]],
            "date": job["metadata"]["newPostingDate"],
            "levels": [x["position"] for x in job["positionLevels"]],
            "skills": [x["skill"] for x in job["skills"]],
            "salary": job["salary"],
            "employment_type": [x["employmentType"] for x in job["employmentTypes"]],
            "status": job["status"]["jobStatus"]
        }
        jd = scrape_jd(job["uuid"])
        if not jd:
            return None
        record.update({
            "description": BeautifulSoup(jd["description"] or "", "html.parser").text.replace("\n", " "),
            "minimum_yoe": jd["minimumYearsExperience"],
            "vacancies": jd["numberOfVacancies"],
            "view_count": jd["metadata"]["totalNumberOfView"],
            "apply_count": jd["metadata"]["totalNumberJobApplication"],
            "other_requirements": jd["otherRequirements"],
            "screening_questions": jd["screeningQuestions"],
            "company_description": BeautifulSoup(jd["postedCompany"]["description"] or "", "html.parser").text.replace("\n", " "),
            "employee_count": jd["postedCompany"]["employeeCount"]
        })
        return record
    except Exception as e:
        logging.error(f"Failed to scrape job {job['uuid']}, error {e}")


def bigquery_insert(bq_client, job_data):
    try:
        for row in job_data:
            row["categories"] = json.dumps(row["categories"])
            row["levels"] = json.dumps(row["levels"])
            row["skills"] = json.dumps(row["skills"])
            row["salary"] = json.dumps(row["salary"])
            row["employment_type"] = json.dumps(row["employment_type"])
            row["screening_questions"] = json.dumps(row["screening_questions"])        
        errors = bq_client.insert_rows_json(BQ_RAW_DATA_TABLE, job_data)
        if errors:
            logging.error(f"Encountered errors while inserting rows: {errors}")
    except Exception as e:
        logging.error(f"Failed to insert into BigQuery: {e}")


@functions_framework.http
def main(request):
    payload = request.get_json(silent=True)
    start_page = payload.get("start_page", 0)
    end_page = start_page + payload.get("running_pages", 1) - 1
    limit = payload.get("limit", 50)
    chunk_size = payload.get("chunk_size", 200)
    process(start_page, end_page, limit, chunk_size)
    return "OK"