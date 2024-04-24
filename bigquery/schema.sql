# Create deduplicate table from raw table
CREATE TABLE `jobai-420303.jobai_data.job_data_deduplicated` AS (
  SELECT
    * EXCEPT(salary),
    JSON_EXTRACT_SCALAR(salary, '$.minimum') AS salary_min,
    JSON_EXTRACT_SCALAR(salary, '$.maximum') AS salary_max,
    JSON_EXTRACT_SCALAR(salary, '$.type.salaryType') AS salary_type
  FROM `jobai-420303.jobai_data.job_data_raw`
  QUALIFY
    ROW_NUMBER() OVER (
      PARTITION BY
        date,
        id
      ORDER BY
        date DESC
    ) = 1
)


# Create text embedding remote model
CREATE OR REPLACE MODEL `jobai_data.embedding_model`
REMOTE WITH CONNECTION `asia-southeast1.vertex-ai`
OPTIONS (ENDPOINT = 'textembedding-gecko@003'); 


# Create embeddings input table
CREATE OR REPLACE TABLE jobai_data.job_data_embeddings_input AS
SELECT id, CONCAT(
  'Title: ', title, 
  '\nDescription: ', description, 
  '\nSkills: ', REPLACE(ARRAY_TO_STRING(JSON_EXTRACT_ARRAY(skills, '$'), ', '), '"', ''), 
  '\nLevels: ', REPLACE(ARRAY_TO_STRING(JSON_EXTRACT_ARRAY(levels, '$'), ', '), '"', ''), 
  '\nCategories: ', REPLACE(ARRAY_TO_STRING(JSON_EXTRACT_ARRAY(categories, '$'), ', '), '"', ''), 
  '\nMinimum year of experience: ', minimum_yoe, 
  '\nSalary: ', salary_min, ' to ', salary_max, ' ', salary_type
) as content, categories 
FROM `jobai-420303.jobai_data.job_data_deduplicated`


# Create embeddings results table from input table
CREATE OR REPLACE TABLE jobai_data.job_data_embeddings AS
SELECT *
FROM ML.GENERATE_EMBEDDING(
  MODEL `jobai_data.embedding_model`,
  TABLE `jobai_data.job_data_embeddings_input`,
  STRUCT(
    TRUE AS flatten_json_output,
    'CLUSTERING' AS task_type
  )
);


# Create job category summary table
CREATE TABLE `jobai-420303.jobai_data.job_category_summary` (
  category STRING,
  summary STRING,
  created_at TIMESTAMP
)


# Create vector search index
CREATE OR REPLACE VECTOR INDEX embeddings_index 
ON jobai_data.job_data_embeddings(ml_generate_embedding_result)
OPTIONS(distance_type='COSINE', index_type='IVF');
