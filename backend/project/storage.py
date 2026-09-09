from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticS3Boto3Storage(S3Boto3Storage):
    location = settings.STATICFILES_LOCATION

    def __init__(self, **kwargs):
        kwargs['bucket_name'] = settings.AWS_STORAGE_BUCKET_NAME
        if hasattr(settings, 'AWS_S3_ENDPOINT_URL'):
            kwargs['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        if settings.MINIO_ACCESS_URL:
            self.secure_urls = False
            self.custom_domain = settings.MINIO_ACCESS_URL
        super(StaticS3Boto3Storage, self).__init__(**kwargs)


class S3MediaStorage(S3Boto3Storage):
    def __init__(self, **kwargs):
        kwargs['bucket_name'] = settings.AWS_STORAGE_BUCKET_NAME
        if hasattr(settings, 'AWS_S3_ENDPOINT_URL'):
            kwargs['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        if settings.MINIO_ACCESS_URL:
            self.secure_urls = False
            self.custom_domain = settings.MINIO_ACCESS_URL
        super(S3MediaStorage, self).__init__(**kwargs)
