terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.21.0"
    }
  }
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "ctrlaltelite" 

    workspaces { 
      name = "ctrlaltelite" 
    } 
  }
}


data "google_client_config" "default" {}



provider "google" {
  project = local.gcp_credentials.project_id
  region  = "asia-southeast1"
  credentials = file(local.credentials_file_path)
}


