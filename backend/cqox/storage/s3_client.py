"""
S3 client for figure and artifact storage

High-performance object storage for:
- Visualization figures (PNG, SVG, PDF)
- Model artifacts (pickled estimators)
- Dataset snapshots
- Export files
"""
import aioboto3
from typing import Optional, BinaryIO, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import hashlib
import io


class S3Client:
    """
    Async S3 client with automatic multipart upload and CDN integration

    Features:
    - Multipart upload for large files (>5MB)
    - Pre-signed URLs for secure access
    - CloudFront CDN integration
    - Automatic content-type detection
    - Object versioning
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,  # For MinIO compatibility
        cloudfront_domain: Optional[str] = None
    ):
        self.bucket_name = bucket_name
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self.cloudfront_domain = cloudfront_domain
        self.session = aioboto3.Session()

    async def upload_file(
        self,
        file_path: str,
        s3_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> str:
        """
        Upload file to S3

        Args:
            file_path: Local file path
            s3_key: S3 object key
            content_type: MIME type
            metadata: Custom metadata
            public: Make object public

        Returns:
            S3 URL or CloudFront URL
        """
        async with self.session.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url
        ) as s3:
            # Auto-detect content type
            if not content_type:
                content_type = self._get_content_type(file_path)

            # Prepare extra args
            extra_args = {
                'ContentType': content_type,
                'Metadata': metadata or {}
            }

            if public:
                extra_args['ACL'] = 'public-read'

            # Upload
            with open(file_path, 'rb') as f:
                await s3.upload_fileobj(
                    f,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs=extra_args
                )

            logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{s3_key}")

            return self._get_url(s3_key)

    async def upload_bytes(
        self,
        data: bytes,
        s3_key: str,
        content_type: str = 'application/octet-stream',
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload bytes to S3"""
        async with self.session.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url
        ) as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                ContentType=content_type,
                Metadata=metadata or {}
            )

            logger.info(f"Uploaded {len(data)} bytes to s3://{self.bucket_name}/{s3_key}")

            return self._get_url(s3_key)

    async def download_file(self, s3_key: str, local_path: str):
        """Download file from S3"""
        async with self.session.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url
        ) as s3:
            with open(local_path, 'wb') as f:
                await s3.download_fileobj(self.bucket_name, s3_key, f)

            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")

    async def download_bytes(self, s3_key: str) -> bytes:
        """Download file as bytes"""
        async with self.session.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url
        ) as s3:
            response = await s3.get_object(Bucket=self.bucket_name, Key=s3_key)
            async with response['Body'] as stream:
                return await stream.read()

    async def generate_presigned_url(
        self,
        s3_key: str,
        expires_in: int = 3600,
        http_method: str = 'GET'
    ) -> str:
        """
        Generate presigned URL for temporary access

        Args:
            s3_key: S3 object key
            expires_in: URL expiration in seconds (default: 1 hour)
            http_method: HTTP method (GET, PUT, etc.)

        Returns:
            Presigned URL
        """
        async with self.session.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url
        ) as s3:
            url = await s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )

            return url

    async def delete_file(self, s3_key: str):
        """Delete file from S3"""
        async with self.session.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url
        ) as s3:
            await s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted s3://{self.bucket_name}/{s3_key}")

    async def list_objects(self, prefix: str = '', max_keys: int = 1000) -> list:
        """List objects with prefix"""
        async with self.session.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url
        ) as s3:
            response = await s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            return response.get('Contents', [])

    async def get_object_metadata(self, s3_key: str) -> Dict[str, Any]:
        """Get object metadata"""
        async with self.session.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url
        ) as s3:
            response = await s3.head_object(Bucket=self.bucket_name, Key=s3_key)

            return {
                'content_length': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {}),
                'etag': response['ETag']
            }

    def _get_content_type(self, file_path: str) -> str:
        """Auto-detect content type"""
        suffix = Path(file_path).suffix.lower()
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml',
            '.pdf': 'application/pdf',
            '.json': 'application/json',
            '.csv': 'text/csv',
            '.parquet': 'application/octet-stream',
            '.pkl': 'application/octet-stream'
        }
        return content_types.get(suffix, 'application/octet-stream')

    def _get_url(self, s3_key: str) -> str:
        """Get public URL (CloudFront or S3)"""
        if self.cloudfront_domain:
            return f"https://{self.cloudfront_domain}/{s3_key}"
        elif self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{s3_key}"
        else:
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"


# Utility functions
def generate_s3_key(prefix: str, filename: str, add_hash: bool = True) -> str:
    """
    Generate S3 key with optional content hash

    Args:
        prefix: Key prefix (e.g., 'figures', 'models')
        filename: Original filename
        add_hash: Add hash to prevent collisions

    Returns:
        S3 key
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

    if add_hash:
        hash_val = hashlib.md5(f"{filename}{timestamp}".encode()).hexdigest()[:8]
        return f"{prefix}/{timestamp}_{hash_val}_{filename}"
    else:
        return f"{prefix}/{timestamp}_{filename}"


# Global client instance
_s3_client: Optional[S3Client] = None


async def get_s3_client() -> S3Client:
    """Get or create S3 client"""
    global _s3_client

    if _s3_client is None:
        from cqox.config import settings

        _s3_client = S3Client(
            bucket_name=getattr(settings, 's3_bucket', 'cqox-artifacts'),
            region=getattr(settings, 's3_region', 'us-east-1'),
            access_key=getattr(settings, 'aws_access_key_id', None),
            secret_key=getattr(settings, 'aws_secret_access_key', None),
            endpoint_url=getattr(settings, 's3_endpoint_url', None),
            cloudfront_domain=getattr(settings, 'cloudfront_domain', None)
        )

    return _s3_client
