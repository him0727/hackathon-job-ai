# Job source scrapper
data "archive_file" "job_source_scrapper" {
  type        = "zip"
  output_path = "${path.root}/.terraform/tmp/job_source_scrapper.zip"
  source_dir  = "${path.root}/../src/cloud_functions/job_source_scrapper/"
}

resource "google_storage_bucket_object" "job_source_scrapper" {
  name   = "cloud_functions/job_source_scrapper.zip"
  bucket = google_storage_bucket.build_artefects.name
  source = data.archive_file.job_source_scrapper.output_path
}

resource "google_cloudfunctions2_function" "job_source_scrapper" {
  name        = "job_source_scrapper"
  location    = local.main_region
  description = "Extract job data from external source and insert into BigQuery"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.build_artefects.name
        object = google_storage_bucket_object.job_source_scrapper.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    available_memory   = "1G"
    available_cpu      = 2
    timeout_seconds    = 3600
  }
}

# Job trends generator
data "archive_file" "job_trends_generator" {
  type        = "zip"
  output_path = "${path.root}/.terraform/tmp/job_trends_generator.zip"
  source_dir  = "${path.root}/../src/cloud_functions/job_trends_generator/"
}

resource "google_storage_bucket_object" "job_trends_generator" {
  name   = "cloud_functions/job_trends_generator.zip"
  bucket = google_storage_bucket.build_artefects.name
  source = data.archive_file.job_trends_generator.output_path
}

resource "google_cloudfunctions2_function" "job_trends_generator" {
  name        = "job_trends_generator"
  location    = local.main_region
  description = "Load embeddings from GCS and write the job category summary to BigQuery"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = google_storage_bucket.build_artefects.name
        object = google_storage_bucket_object.job_trends_generator.name
      }
    }
  }

  service_config {
    max_instance_count = 15
    available_memory   = "3G"
    available_cpu      = 4
    timeout_seconds    = 500
  }

  event_trigger {
    event_type   = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic = google_pubsub_topic.job_trends_generation.id
    retry_policy = "RETRY_POLICY_RETRY"
  }
}
