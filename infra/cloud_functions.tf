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