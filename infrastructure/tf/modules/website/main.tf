resource "google_storage_bucket" "website" {
  name          = "${var.project_id}-react-hosting"
  location      = "ASIA"
  storage_class = "STANDARD"
  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page = "index.html"
  }
}

resource "google_storage_bucket_iam_binding" "public_read" {
  bucket = google_storage_bucket.website.name
  role   = "roles/storage.objectViewer"
  members = ["allUsers"]
}

resource "google_storage_bucket_object" "index_html" {
  name   = "index.html"
  bucket = google_storage_bucket.website.name
  source = var.index_file
  content_type = "text/html"
}