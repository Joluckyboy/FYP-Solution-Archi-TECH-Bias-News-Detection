"""
S3 Upload utility for scraper
Uploads CSV files to S3 with backup functionality
"""
import os
import logging
import boto3
from datetime import datetime

logger = logging.getLogger(__name__)


class S3Uploader:
    """Handles uploading scraped articles to S3"""
    
    def __init__(self):
        self.bucket = os.environ.get('S3_BUCKET')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.enabled = os.environ.get('S3_UPLOAD_ENABLED', 'false').lower() == 'true'
        
        if self.enabled and not self.bucket:
            logger.warning("S3_UPLOAD_ENABLED=true but S3_BUCKET not set")
            self.enabled = False
        
        if self.enabled:
            try:
                self.s3_client = boto3.client('s3', region_name=self.region)
                logger.info(f"S3 uploader initialized: bucket={self.bucket}, region={self.region}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.enabled = False
    
    def upload_csv(self, csv_file_path, create_backup=True):
        """
        Upload CSV file to S3
        
        Args:
            csv_file_path: Local path to CSV file
            create_backup: Whether to create timestamped backup
        
        Returns:
            dict: Upload result with status and URLs
        """
        if not self.enabled:
            logger.info("S3 upload disabled (S3_UPLOAD_ENABLED not set)")
            return {'success': False, 'message': 'S3 upload disabled'}
        
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found: {csv_file_path}")
            return {'success': False, 'message': 'CSV file not found'}
        
        try:
            # Main upload
            main_key = 'scraped_articles/scraped_articles.csv'
            
            logger.info(f"Uploading to s3://{self.bucket}/{main_key}")
            
            self.s3_client.upload_file(
                csv_file_path,
                self.bucket,
                main_key,
                ExtraArgs={'ContentType': 'text/csv'}
            )
            
            main_url = f"s3://{self.bucket}/{main_key}"
            logger.info(f"✓ Uploaded main CSV: {main_url}")
            
            result = {
                'success': True,
                'main_url': main_url,
                'backup_url': None
            }
            
            # Create backup if requested
            if create_backup:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_key = f"scraped_articles/backups/scraped_articles_{timestamp}.csv"
                
                logger.info(f"Creating backup: {backup_key}")
                
                self.s3_client.upload_file(
                    csv_file_path,
                    self.bucket,
                    backup_key,
                    ExtraArgs={'ContentType': 'text/csv'}
                )
                
                backup_url = f"s3://{self.bucket}/{backup_key}"
                logger.info(f"✓ Created backup: {backup_url}")
                
                result['backup_url'] = backup_url
            
            return result
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return {'success': False, 'message': str(e)}
    
    def download_csv(self, s3_key, local_path):
        """
        Download CSV file from S3
        
        Args:
            s3_key: S3 object key
            local_path: Local path to save file
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            logger.info(f"Downloading from s3://{self.bucket}/{s3_key}")
            
            self.s3_client.download_file(
                self.bucket,
                s3_key,
                local_path
            )
            
            logger.info(f"✓ Downloaded to {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            return False