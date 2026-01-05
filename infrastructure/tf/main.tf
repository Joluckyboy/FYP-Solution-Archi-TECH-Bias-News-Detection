# module "website" {
#   source = "./modules/website"
#   project_id = var.project_id
#   domain_name = var.domain_name
# }


resource "google_container_cluster" "backend_cluster" {
  name     = var.backend_cluster_name
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1

  deletion_protection = false
}

resource "google_container_node_pool" "backend_cluster_nodes" {
  name       = "backend-node-pool"
  location   = var.region
  cluster    = google_container_cluster.backend_cluster.name
  node_count = 1

  node_config {
    machine_type = "e2-standard-8"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    disk_size_gb = 100
  }
}
