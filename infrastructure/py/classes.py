import boto3
from botocore.config import Config

from google.cloud import storage, compute_v1, dns
import os
import time

class GCP_AGENT:
    def __init__(self, project_id: str, domain_name: str, service_account_path: str) -> None:
        self.project_id = project_id
        self.domain_name = domain_name
        self.bucket_name = domain_name.replace(".", "-")
        self.region = "asia-southeast1"
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
        
        self.storage_client = storage.Client(project=self.project_id)
        self.compute_client = compute_v1
        
    def create_bucket(self) -> None:
        """Creates a Cloud Storage bucket for static website hosting."""
        bucket = self.storage_client.bucket(self.bucket_name)
        bucket.storage_class = "STANDARD"
        
        bucket.create(location="ASIA")
        print(f"Bucket {self.bucket_name} created.")
        
        # Enable website hosting
        bucket_website_config = {
            "mainPageSuffix": "index.html",
            "notFoundPage": "index.html"
        }
        bucket.configure_website(**bucket_website_config)
        print(f"Bucket {self.bucket_name} configured for static website hosting")
    
    def create_ssl_certificate(self):
        """Creates a Google-managed SSL certificate for the custom domain"""
        ssl_cert_name = f"{self.domain_name.replace('.', '-')}-cert"
        ssl_client = self.compute_client.SslCertificatesClient()

        ssl_cert = compute_v1.SslCertificate(
            name=ssl_cert_name,
            type_="MANAGED",
            managed=compute_v1.SslCertificateManagedSslCertificate(
            domains=[self.domain_name]
            )
        )
        operation = ssl_client.insert(project=self.project_id, ssl_certificate_resource=ssl_cert)
        print(f"Creating SSL certificate for {self.domain_name}...")

        return ssl_cert_name
    
    def create_backend_bucket(self):
        """Creates a backend bucket for serving website content."""
        backend_bucket_name = f"{self.domain_name.replace('.', '-')}-backend"
        backend_client = self.compute_client.BackendBucketsClient()

        backend_bucket = compute_v1.BackendBucket(
            name=backend_bucket_name,
            bucket_name=self.bucket_name,
            enable_cdn=True
        )

        operation = backend_client.insert(project=self.project_id, backend_bucket_resource=backend_bucket)
        print("Creating backend bucket...")
        return backend_bucket_name

    def create_url_map(self, backend_bucket_name):
        """Creates a URL map for the load balancer."""
        url_map_name = f"{self.domain_name.replace('.', '-')}-url-map"
        url_map_client = self.compute_client.UrlMapsClient()
        
        url_map = compute_v1.UrlMap(
            name=url_map_name,
            default_service=f"projects/{self.project_id}/global/backendBuckets/{backend_bucket_name}"
        )
        
        operation = url_map_client.insert(project=self.project_id, url_map_resource=url_map)
        print("Creating URL map for load balancer...")

        return url_map_name

    def create_http_https_forwarding_rule(self, url_map_name, ssl_cert_name):
        """Creates an HTTPS forwarding rule for the domain."""
        target_https_proxy_name = f"{self.domain_name.replace('.', '-')}-https-proxy"
        proxy_client = self.compute_client.TargetHttpsProxiesClient()
        
        target_https_proxy = compute_v1.TargetHttpsProxy(
            name=target_https_proxy_name,
            url_map=f"projects/{self.project_id}/global/urlMaps/{url_map_name}",
            ssl_certificates=[f"projects/{self.project_id}/global/sslCertificates/{ssl_cert_name}"]
        )

        operation = proxy_client.insert(project=self.project_id, target_https_proxy_resource=target_https_proxy)
        print("Creating HTTPS proxy...")

        forwarding_rule_client = self.compute_client.GlobalForwardingRulesClient()
        forwarding_rule_name = f"{self.domain_name.replace('.', '-')}-https-rule"
        forwarding_rule = compute_v1.ForwardingRule(
            name=forwarding_rule_name,
            load_balancing_scheme="EXTERNAL",
            target=f"projects/{self.project_id}/global/targetHttpsProxies/{target_https_proxy_name}",
            port_range="443"
        )

        operation = forwarding_rule_client.insert(project=self.project_id, forwarding_rule_resource=forwarding_rule)
        print("Creating HTTPS forwarding rule...")
        
    def create_dns_zone(self):
        """Creates a Cloud DNS managed zone for the domain."""
        zone_name = self.domain_name.replace(".", "-") + "-zone"
        dns_client = dns.Client(project=self.project_id)

        # Check if the zone already exists
        for zone in dns_client.list_zones():
            if zone.name == zone_name:
                print(f"DNS Zone {zone_name} already exists.")
                return zone_name

        # Create the managed DNS zone
        zone = dns_client.zone(zone_name, self.domain_name + ".")
        zone.create()
        print(f"Created DNS Zone: {zone_name}")

        return zone_name

    def setup_static_website(self):
        """Runs the setup process for hosting a static website."""
        self.create_bucket()
        ssl_cert_name = self.create_ssl_certificate()
        backend_bucket_name = self.create_backend_bucket()
        url_map_name = self.create_url_map(backend_bucket_name)
        self.create_http_https_forwarding_rule(url_map_name, ssl_cert_name)

        print(f"Static website hosting for {self.domain_name} is set up!")
        
class AWS_AGENT:
    def __init__(self):
        
        self.ec2 = self.session.client('ec2')
        self.ecs = self.session.client('ecs')


    def test(self):
        response = self.ec2.describe_instances()
        print(response)

        return response

    def deploy_ecs_service(self, cluster_name, service_name, docker_image, container_name, task_role_arn=None, execution_role_arn=None, desired_count=1, region='us-east-1'):
        """
        Deploys an ECS service using a Docker image from Docker Hub.

        Parameters:
        - cluster_name: Name of the ECS cluster.
        - service_name: Name of the ECS service to create or update.
        - docker_image: Docker image (e.g., 'nginx:latest').
        - container_name: Name of the container.
        - task_role_arn: ARN of the IAM role that containers can assume (optional).
        - execution_role_arn: ARN of the IAM role that ECS can assume to pull images and publish logs (optional).
        - desired_count: Number of tasks to run (default is 1).
        - region: AWS region where the ECS cluster is located (default is 'us-east-1').

        Returns:
        - Response from the ECS client.
        """
        ecs_client = boto3.client('ecs', region_name=region)

        # Define the container definition
        container_definitions = [
            {
                'name': container_name,
                'image': docker_image,
                'essential': True,
                'portMappings': [
                    {
                        'containerPort': 80,
                        'hostPort': 80,
                        'protocol': 'tcp'
                    }
                ],
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': f'/ecs/{service_name}',
                        'awslogs-region': region,
                        'awslogs-stream-prefix': 'ecs'
                    }
                }
            }
        ]

        # Register the task definition
        response = ecs_client.register_task_definition(
            family=service_name,
            taskRoleArn=task_role_arn,
            executionRoleArn=execution_role_arn,
            networkMode='awsvpc',
            containerDefinitions=container_definitions,
            requiresCompatibilities=['FARGATE'],
            cpu='256',
            memory='512'
        )

        task_definition_arn = response['taskDefinition']['taskDefinitionArn']

        # Create or update the ECS service
        try:
            response = ecs_client.create_service(
                cluster=cluster_name,
                serviceName=service_name,
                taskDefinition=task_definition_arn,
                desiredCount=desired_count,
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': ['subnet-xxxxxxxx'],  # Replace with your subnet IDs
                        'assignPublicIp': 'ENABLED'
                    }
                }
            )
        except ecs_client.exceptions.ServiceAlreadyExistsException:
            response = ecs_client.update_service(
                cluster=cluster_name,
                service=service_name,
                taskDefinition=task_definition_arn,
                desiredCount=desired_count
            )

        return response

        return "containers deployed"
    
    def deploy_apigateway(self):
        print("deploying apigateways")
        return "apigateways deployed"
    
    def deploy_s3_static_website(self):
        print("deploying s3 static website")
        return "s3 static website deployed"
    
