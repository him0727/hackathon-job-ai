resource "google_storage_bucket" "jobs_input_data" {
  name                        = "job-ai-jobs-input-data"
  location                    = upper(local.main_region)
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "build_artefects" {
  name                        = "job-ai-build-artefects"
  location                    = upper(local.main_region)
  force_destroy               = true
  uniform_bucket_level_access = true
}
