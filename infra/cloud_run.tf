# Backend
resource "google_cloud_run_v2_service" "backend" {
  name     = "jobai-backend"
  location = local.main_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    timeout                          = "90s"
    max_instance_request_concurrency = 80

    containers {
      image = "asia.gcr.io/${local.project_id}/jobai-backend"

      resources {
        limits = {
          cpu    = "1"
          memory = "1024Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        name           = "http1"
        container_port = 8080
      }

      startup_probe {
        timeout_seconds   = 15
        period_seconds    = 60
        failure_threshold = 2
        tcp_socket {
          port = 8080
        }
      }
    }

    scaling {
      max_instance_count = 2
    }
  }
}

data "google_iam_policy" "backend" {
  binding {
    role    = "roles/run.invoker"
    members = ["allUsers"]
  }
}

resource "google_cloud_run_service_iam_policy" "backend" {
  location = google_cloud_run_v2_service.backend.location
  project  = google_cloud_run_v2_service.backend.project
  service  = google_cloud_run_v2_service.backend.name

  policy_data = data.google_iam_policy.backend.policy_data
}

# Frontend
resource "google_cloud_run_v2_service" "frontend" {
  name     = "jobai-frontend"
  location = local.main_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    timeout                          = "90s"
    max_instance_request_concurrency = 80

    containers {
      image = "asia.gcr.io/${local.project_id}/jobai-frontend"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        name           = "http1"
        container_port = 7860
      }

      startup_probe {
        timeout_seconds   = 30
        period_seconds    = 90
        failure_threshold = 2
        tcp_socket {
          port = 7860
        }
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 2
    }
  }
}

data "google_iam_policy" "frontend" {
  binding {
    role    = "roles/run.invoker"
    members = ["allUsers"]
  }
}

resource "google_cloud_run_service_iam_policy" "frontend" {
  location = google_cloud_run_v2_service.frontend.location
  project  = google_cloud_run_v2_service.frontend.project
  service  = google_cloud_run_v2_service.frontend.name

  policy_data = data.google_iam_policy.frontend.policy_data
}