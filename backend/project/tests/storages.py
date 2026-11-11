from django.core.files.storage import InMemoryStorage


class OverwritingMemoryStorage(InMemoryStorage):
    """In-memory storage that replaces an existing file of the same name, as django-storages does
    for S3 and Google Cloud Storage by default (file_overwrite=True). Django's own storages rename
    instead, which would hide the overwrite problem in tests."""

    def get_available_name(self, name, max_length=None):
        return name
