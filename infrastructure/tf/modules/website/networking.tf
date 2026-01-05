resource "google_compute_backend_bucket" "cdn_backend" {
    name = "react-static-bucket"
    bucket_name = google_storage_bucket.website.name
    enable_cdn = true
}

resource "google_compute_managed_ssl_certificate" "website_ssl" {
  name = "website-ssl"
  managed {
    domains = [var.domain_name]
  }
}

resource "google_compute_global_address" "lb_ip" {
  name   = "lb-ipv4"

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_compute_url_map" "website_map" {
  name            = "website-url-map"
  default_service = google_compute_backend_bucket.cdn_backend.self_link
}

resource "google_compute_target_https_proxy" "https_proxy" {
  name    = "website-https-proxy"
  url_map = google_compute_url_map.website_map.self_link
  ssl_certificates = [google_compute_managed_ssl_certificate.website_ssl.self_link]
}

resource "google_compute_global_forwarding_rule" "https_rule" {
  name       = "https-rule"
  target     = google_compute_target_https_proxy.https_proxy.self_link
  port_range = "443"
  ip_address = google_compute_global_address.lb_ip.address
  depends_on = [ google_compute_global_address.lb_ip ]
}