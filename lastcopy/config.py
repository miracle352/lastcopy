"""Server-only settings. Validation returns names, never values or credentials."""
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv
from .models import ConfigurationStatus

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "zetaris": ["ZETARIS_SQL_ENDPOINT", "ZETARIS_HEADERS_JSON", "ZETARIS_QUERY_FIELD", "ZETARIS_ROWS_POINTER", "ZETARIS_DEVICE_TABLE", "ZETARIS_SERVER_TABLE", "ZETARIS_S3_PREFIX", "ZETARIS_DEPLOYMENT_VERSION"],
    "nightshift": ["NIGHTSHIFT_BASE_URL", "NIGHTSHIFT_TOKEN", "NIGHTSHIFT_ROUTE"],
    "odk": ["ODK_BASE_URL", "ODK_EMAIL", "ODK_PASSWORD", "ODK_PROJECT_ID", "ODK_FORM_ID", "ODK_SUBMISSION_ID", "ODK_VERSION_ID", "ODK_ATTACHMENT_NAME", "ODK_CENTRAL_VERSION"],
}
LIMITS = {"MAX_UPLOAD_BYTES": 10485760, "MAX_UNCOMPRESSED_BYTES": 33554432,
          "MAX_ZIP_ENTRIES": 500, "MAX_XML_BYTES": 1048576, "MAX_XML_DEPTH": 64,
          "MAX_XML_NODES": 10000, "MAX_XML_TEXT": 524288, "MAX_RUN_SECONDS": 300}


@dataclass(frozen=True)
class Settings:
    values: dict[str, str]

    @classmethod
    def load(cls):
        load_dotenv(ROOT / ".env", override=False)
        return cls(dict(os.environ))

    @property
    def sample(self):
        return self.values.get("SAMPLE_MODE", "true").lower() != "false"

    def limit(self, name):
        raw = self.values.get(name, str(LIMITS[name]))
        try:
            value = int(raw)
        except ValueError:
            raise ValueError(f"{name} must be an integer") from None
        if not 0 < value <= LIMITS[name]:
            raise ValueError(f"{name} must be between 1 and {LIMITS[name]}")
        return value

    def status(self, provider=None):
        errors = []
        if self.values.get("SAMPLE_MODE", "true").lower() not in ("true", "false"):
            errors.append("SAMPLE_MODE must be true or false")
        for name in LIMITS:
            try:
                self.limit(name)
            except ValueError as e:
                errors.append(str(e))
        missing = {provider: [name for name in names if not self.values.get(name)] for provider, names in REQUIRED.items()}
        if not self.sample:
            for name in ("ZETARIS_SQL_ENDPOINT", "NIGHTSHIFT_BASE_URL", "ODK_BASE_URL"):
                if provider and not name.startswith({"zetaris": "ZETARIS_", "nightshift": "NIGHTSHIFT_", "odk": "ODK_"}[provider]):
                    continue
                value = self.values.get(name)
                if not value:
                    continue
                try:
                    url = urlsplit(value)
                    valid = (url.scheme == "https" or (url.scheme == "http" and url.hostname in ("127.0.0.1", "localhost", "::1")))
                    if not valid or not url.hostname or url.username or url.password or url.query or url.fragment:
                        raise ValueError()
                except ValueError:
                    errors.append(f"{name} requires HTTPS or loopback HTTP, without credentials, query or fragment")
            if provider in (None, "odk") and self.values.get("ODK_TEST_PROJECT") != "true":
                errors.append("ODK_TEST_PROJECT must be true for the dedicated synthetic test project")
            project = self.values.get("ODK_PROJECT_ID")
            if provider in (None, "odk") and project and (not project.isdecimal() or int(project) < 1):
                errors.append("ODK_PROJECT_ID must be a positive integer")
        required_missing = missing.values() if provider is None else [missing[provider]]
        return ConfigurationStatus(mode="sample" if self.sample else "connected", ready=not errors and (self.sample or not any(required_missing)), missing=missing, errors=errors)
