resource "null_resource" "apply_backend_services" { # 34.58.57.17
  provisioner "local-exec" {

  command =  <<EOT

    gcloud auth activate-service-account --key-file=${local.credentials_file_path}

    gcloud container clusters get-credentials ${google_container_cluster.backend_cluster.name} --region ${var.region} --project ${local.gcp_credentials.project_id}

    kubectl cluster-info

    kubectl create namespace backend
    kubectl create namespace service

    kubectl delete secret factcheck-secret -n backend

    kubectl create secret generic factcheck-secret \
      --from-literal=API_KEY=$API_KEY \
      --from-literal=API_KEYDS=$API_KEYDS \
      -n backend

    kubectl apply -f ./manifests/managed-certs-backup.yaml
    kubectl apply -f ./manifests/backend-config.yaml

    kubectl apply -f ./manifests/backend-sentiment.yaml
    kubectl apply -f ./manifests/backend-emotion.yaml
    kubectl apply -f ./manifests/backend-propaganda.yaml
    kubectl apply -f ./manifests/backend-factcheck.yaml
    kubectl apply -f ./manifests/backend-scraper.yaml
    
    kubectl apply -f ./manifests/backend-ingress.yaml
    EOT
    # kubectl apply -f ./manifests/backend-cert.yaml
  }
  depends_on = [ google_container_cluster.backend_cluster, google_container_node_pool.backend_cluster_nodes]

  triggers = {
    always_run = "${timestamp()}"
  }
}

resource "null_resource" "apply_services" { # 34.42.152.183
  provisioner "local-exec" {

  command = <<EOT

    gcloud auth activate-service-account --key-file=${local.credentials_file_path}

    gcloud container clusters get-credentials ${google_container_cluster.backend_cluster.name} --region ${var.region} --project ${local.gcp_credentials.project_id}

    kubectl cluster-info

    kubectl create namespace service

    kubectl delete secret telebot-secret -n service
    kubectl delete secret application-secret -n service

    kubectl create secret generic telebot-secret \
      --from-literal=TELEBOT_TOKEN=$TELEBOT_TOKEN \
      -n service 

    kubectl create secret generic application-secret \
      --from-literal=PRESCRAPE=$PRESCRAPE \
      -n service 
    
    kubectl create secret generic database-secret \
      --from-literal=MONGO_SERVER=$MONGO_SERVER \
      -n service

    kubectl apply -f ./manifests/service-config.yaml

    kubectl apply -f ./manifests/service-database.yaml
    kubectl apply -f ./manifests/service-application.yaml
    kubectl apply -f ./manifests/service-telebot.yaml

    kubectl apply -f ./manifests/service-ingress.yaml

    EOT
    # kubectl apply -f ./manifests/service-cert.yaml
    # kubectl apply -f ./manifests/egress.yaml
  }
  depends_on = [null_resource.apply_backend_services]

  triggers = {
    always_run = "${timestamp()}"
  }

}