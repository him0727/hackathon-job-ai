# Export to cloud storage
EXPORT DATA OPTIONS(
  uri='gs://job-ai-jobs-input-data/embeddings/<CATEGORY PREFIX>/*.json',
  format='JSON',
  overwrite=true
) AS
SELECT id, content, ml_generate_embedding_result FROM `jobai-420303.jobai_data.job_data_embeddings` WHERE categories LIKE "%\"<CATEGORY VALUE>\"%"


# Get latest summary for each category
SELECT category, ANY_VALUE(summary HAVING MAX created_at) AS summary FROM `jobai-420303.jobai_data.job_category_summary` GROUP BY category


# Search closest 5 records for a given embedding
SELECT base.content, base.categories FROM VECTOR_SEARCH(
  TABLE jobai_data.job_data_embeddings,
  'ml_generate_embedding_result',
  (
    SELECT [<EMBEDDING FLOAT VALUES>] as ml_generate_embedding_result
  ),
  top_k => 5,
  distance_type => 'COSINE',
  options => '{"use_brute_force":true}'
)
