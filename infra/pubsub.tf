resource "google_pubsub_schema" "job_trends_generation" {
  name = "job-trends-generation"
  type = "AVRO"
  definition = jsonencode({
    "type" = "record"
    "name" = "Avro"
    "fields" = [
      {
        "name" = "category"
        "type" = "string"
      },
      {
        "name" = "dataset_prefix"
        "type" = "string"
      }
    ]
  })
}

resource "google_pubsub_topic" "job_trends_generation" {
  name                       = "job-trends-generation"
  message_retention_duration = "3600s"
  schema_settings {
    schema   = google_pubsub_schema.job_trends_generation.id
    encoding = "JSON"
  }
  depends_on = [google_pubsub_schema.job_trends_generation]
}
