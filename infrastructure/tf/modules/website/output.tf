output "dns_records" {
  value = {
    "A" = google_compute_global_address.lb_ip.address
  }
}