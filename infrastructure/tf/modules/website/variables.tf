variable "project_id" {
  type        = string
  description = "The ID of the GCP project"
}

variable "index_file" {
  type        = string
  description = "The name of the index file for the website."
  default     = "../../frontend/index.html"
}

variable "domain_name" {
    type = string
    description = "The domain name for which the website is to be hosted on."
}