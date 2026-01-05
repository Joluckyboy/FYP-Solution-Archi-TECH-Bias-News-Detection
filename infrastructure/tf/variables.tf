locals {
}

locals {
  credentials_file_path = "./gcp_credentials.json"
  gcp_credentials = jsondecode(file(var.gcp_credentials_file))

  # database =  file("./manifests/database.yaml")
  # sentiment = file("./manifests/sentiment.yaml")
  # emotion = file("./manifests/emotion.yaml")
  # propaganda = file("./manifests/propaganda.yaml")
  # factcheck = file("./manifests/factcheck.yaml")
  # scraper = file("./manifests/scraper.yaml")
}

// read in a file called gcp_credentials.json
variable "gcp_credentials_file" {
  description = "Path to the GCP credentials JSON file"
  type        = string
  default     = "./gcp_credentials.json"
}

variable "backend_cluster_name" {
    default = "ctrlaltelite-backend-cluster"
}

variable "service_cluster_name" {
    default = "ctrlaltelite-service-cluster"
}

variable "region" {
    default = "us-central1-a"
}

variable "domain_name" {
  default = "chfwhitehats2024.games"
}

variable "project_id" {
  default = "ctrlaltelite-dcs-sentiment"
}