"""Storage service for file management."""

import os
import uuid
from pathlib import Path
from typing import Optional, BinaryIO
import aiofiles
import aiofiles.os

from app.config import settings


class StorageService:
    """Service for managing file storage."""

    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.upload_dir = Path(settings.UPLOAD_DIR)

        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file: BinaryIO,
        filename: str,
        project_id: str,
        category: str,
    ) -> tuple[str, str]:
        """
        Save a file and return (stored_filename, file_path).

        Args:
            file: File-like object to save
            filename: Original filename
            project_id: Project UUID
            category: Document category (guidelines/beneficiary)

        Returns:
            Tuple of (stored_filename, relative_path)
        """
        # Generate unique filename
        file_ext = Path(filename).suffix.lower()
        stored_filename = f"{uuid.uuid4()}{file_ext}"

        # Create directory structure: uploads/project_id/category/
        relative_dir = Path(project_id) / category
        full_dir = self.upload_dir / relative_dir
        await aiofiles.os.makedirs(full_dir, exist_ok=True)

        # Full path for the file
        file_path = full_dir / stored_filename
        relative_path = str(relative_dir / stored_filename)

        if self.storage_type == "local":
            await self._save_local(file, file_path)
        elif self.storage_type in ("s3", "minio"):
            await self._save_s3(file, relative_path)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")

        return stored_filename, relative_path

    async def _save_local(self, file: BinaryIO, file_path: Path) -> None:
        """Save file to local storage."""
        content = file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

    async def _save_s3(self, file: BinaryIO, key: str) -> None:
        """Save file to S3/MinIO storage."""
        import boto3
        from botocore.config import Config

        config = Config(signature_version='s3v4')

        client_kwargs = {
            'aws_access_key_id': settings.S3_ACCESS_KEY,
            'aws_secret_access_key': settings.S3_SECRET_KEY,
            'config': config,
        }

        if settings.S3_ENDPOINT:
            client_kwargs['endpoint_url'] = settings.S3_ENDPOINT
        else:
            client_kwargs['region_name'] = settings.S3_REGION

        s3_client = boto3.client('s3', **client_kwargs)

        # Ensure bucket exists
        try:
            s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        except Exception:
            s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)

        s3_client.upload_fileobj(file, settings.S3_BUCKET_NAME, key)

    async def get_file(self, file_path: str) -> bytes:
        """Retrieve a file's content."""
        if self.storage_type == "local":
            return await self._get_local(file_path)
        elif self.storage_type in ("s3", "minio"):
            return await self._get_s3(file_path)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")

    async def _get_local(self, file_path: str) -> bytes:
        """Get file from local storage."""
        full_path = self.upload_dir / file_path
        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def _get_s3(self, key: str) -> bytes:
        """Get file from S3/MinIO storage."""
        import boto3
        from io import BytesIO

        client_kwargs = {
            'aws_access_key_id': settings.S3_ACCESS_KEY,
            'aws_secret_access_key': settings.S3_SECRET_KEY,
        }

        if settings.S3_ENDPOINT:
            client_kwargs['endpoint_url'] = settings.S3_ENDPOINT
        else:
            client_kwargs['region_name'] = settings.S3_REGION

        s3_client = boto3.client('s3', **client_kwargs)

        buffer = BytesIO()
        s3_client.download_fileobj(settings.S3_BUCKET_NAME, key, buffer)
        buffer.seek(0)
        return buffer.read()

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            if self.storage_type == "local":
                full_path = self.upload_dir / file_path
                await aiofiles.os.remove(full_path)
            elif self.storage_type in ("s3", "minio"):
                import boto3

                client_kwargs = {
                    'aws_access_key_id': settings.S3_ACCESS_KEY,
                    'aws_secret_access_key': settings.S3_SECRET_KEY,
                }

                if settings.S3_ENDPOINT:
                    client_kwargs['endpoint_url'] = settings.S3_ENDPOINT
                else:
                    client_kwargs['region_name'] = settings.S3_REGION

                s3_client = boto3.client('s3', **client_kwargs)
                s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=file_path)

            return True
        except Exception:
            return False

    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Get a URL for accessing the file."""
        if self.storage_type == "local":
            # For local storage, return a relative path that can be served
            return f"/api/v1/files/{file_path}"
        elif self.storage_type in ("s3", "minio"):
            import boto3

            client_kwargs = {
                'aws_access_key_id': settings.S3_ACCESS_KEY,
                'aws_secret_access_key': settings.S3_SECRET_KEY,
            }

            if settings.S3_ENDPOINT:
                client_kwargs['endpoint_url'] = settings.S3_ENDPOINT
            else:
                client_kwargs['region_name'] = settings.S3_REGION

            s3_client = boto3.client('s3', **client_kwargs)

            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': file_path},
                ExpiresIn=expires_in,
            )
            return url

        raise ValueError(f"Unsupported storage type: {self.storage_type}")

    def get_full_path(self, file_path: str) -> str:
        """Get the full filesystem path for a file (local storage only)."""
        if self.storage_type != "local":
            raise ValueError("Full path only available for local storage")
        return str(self.upload_dir / file_path)
