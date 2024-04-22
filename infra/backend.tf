terraform {
  required_version = "~> 1.8.0"

  required_providers {
    google = {
      version = "~> 5.20.0"
    }
    archive = {
      version = "~> 2.4.0"
    }
  }

  backend "gcs" {
    bucket = "job-ai-tf-state"
  }
}

provider "google" {
  project = local.project_id
  region  = local.main_region
}
