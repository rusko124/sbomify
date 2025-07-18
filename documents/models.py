from django.db import models

from core.utils import generate_id
from sboms.models import Component


class Document(models.Model):
    """Represents a document artifact associated with a component.

    Documents can be versioned artifacts like specifications, manuals,
    reports, or any other document type associated with a software component.
    """

    class DocumentType(models.TextChoices):
        """Document types aligned with SPDX and CycloneDX standards."""

        # Technical Documentation
        SPECIFICATION = "specification", "Specification"
        MANUAL = "manual", "Manual"
        README = "readme", "README"
        DOCUMENTATION = "documentation", "Documentation"
        BUILD_INSTRUCTIONS = "build-instructions", "Build Instructions"
        CONFIGURATION = "configuration", "Configuration"

        # Legal and Compliance
        LICENSE = "license", "License"
        COMPLIANCE = "compliance", "Compliance"
        EVIDENCE = "evidence", "Evidence"

        # Release Information
        CHANGELOG = "changelog", "Changelog"
        RELEASE_NOTES = "release-notes", "Release Notes"

        # Security Documents
        SECURITY_ADVISORY = "security-advisory", "Security Advisory"
        VULNERABILITY_REPORT = "vulnerability-report", "Vulnerability Report"
        THREAT_MODEL = "threat-model", "Threat Model"
        RISK_ASSESSMENT = "risk-assessment", "Risk Assessment"
        PENTEST_REPORT = "pentest-report", "Penetration Test Report"

        # Analysis Reports
        STATIC_ANALYSIS = "static-analysis", "Static Analysis Report"
        DYNAMIC_ANALYSIS = "dynamic-analysis", "Dynamic Analysis Report"
        QUALITY_METRICS = "quality-metrics", "Quality Metrics"
        MATURITY_REPORT = "maturity-report", "Maturity Report"
        REPORT = "report", "Report"

        # Other
        OTHER = "other", "Other"

    class Meta:
        db_table = "documents_documents"
        ordering = ["-created_at"]

    id = models.CharField(max_length=20, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255, blank=False)  # document name
    version = models.CharField(max_length=255, default="")  # document version
    document_filename = models.CharField(max_length=255, default="")  # stored filename
    created_at = models.DateTimeField(auto_now_add=True)
    # Where the document came from (file-upload, api, etc)
    source = models.CharField(max_length=255, null=True)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)

    # Enhanced document-specific fields
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        help_text="Type of document aligned with SPDX and CycloneDX standards",
    )
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=100, blank=True)  # MIME type
    file_size = models.PositiveIntegerField(null=True, blank=True)  # File size in bytes

    def __str__(self) -> str:
        return self.name

    @property
    def public_access_allowed(self) -> bool:
        """Check if public access is allowed for this document.

        Returns:
            True if the component is public, False otherwise.
        """
        return self.component.is_public

    @property
    def source_display(self) -> str:
        """Return a user-friendly display name for the source.

        Returns:
            A human-readable string representing the document source.
        """
        source_display_map = {
            "api": "API",
            "manual_upload": "Manual Upload",
        }
        return source_display_map.get(self.source, self.source or "Unknown")

    @property
    def cyclonedx_external_ref_type(self) -> str:
        """Get the corresponding CycloneDX external reference type."""
        cyclonedx_mapping = {
            self.DocumentType.SPECIFICATION: "documentation",
            self.DocumentType.MANUAL: "documentation",
            self.DocumentType.README: "documentation",
            self.DocumentType.DOCUMENTATION: "documentation",
            self.DocumentType.BUILD_INSTRUCTIONS: "build-meta",
            self.DocumentType.CONFIGURATION: "configuration",
            self.DocumentType.LICENSE: "license",
            self.DocumentType.COMPLIANCE: "certification-report",
            self.DocumentType.EVIDENCE: "evidence",
            self.DocumentType.CHANGELOG: "release-notes",
            self.DocumentType.RELEASE_NOTES: "release-notes",
            self.DocumentType.SECURITY_ADVISORY: "advisories",
            self.DocumentType.VULNERABILITY_REPORT: "vulnerability-assertion",
            self.DocumentType.THREAT_MODEL: "threat-model",
            self.DocumentType.RISK_ASSESSMENT: "risk-assessment",
            self.DocumentType.PENTEST_REPORT: "pentest-report",
            self.DocumentType.STATIC_ANALYSIS: "static-analysis-report",
            self.DocumentType.DYNAMIC_ANALYSIS: "dynamic-analysis-report",
            self.DocumentType.QUALITY_METRICS: "quality-metrics",
            self.DocumentType.MATURITY_REPORT: "maturity-report",
            self.DocumentType.REPORT: "other",
            self.DocumentType.OTHER: "other",
        }
        return cyclonedx_mapping.get(self.document_type, "other")

    @property
    def spdx_reference_category(self) -> str:
        """Get the corresponding SPDX reference category."""
        security_types = {
            self.DocumentType.SECURITY_ADVISORY,
            self.DocumentType.VULNERABILITY_REPORT,
            self.DocumentType.THREAT_MODEL,
            self.DocumentType.RISK_ASSESSMENT,
            self.DocumentType.PENTEST_REPORT,
        }

        if self.document_type in security_types:
            return "SECURITY"
        else:
            return "OTHER"

    @property
    def spdx_reference_type(self) -> str:
        """Get the corresponding SPDX reference type."""
        spdx_mapping = {
            self.DocumentType.SPECIFICATION: "specification",
            self.DocumentType.MANUAL: "manual",
            self.DocumentType.README: "readme",
            self.DocumentType.DOCUMENTATION: "documentation",
            self.DocumentType.BUILD_INSTRUCTIONS: "build-instructions",
            self.DocumentType.CONFIGURATION: "configuration",
            self.DocumentType.LICENSE: "license",
            self.DocumentType.COMPLIANCE: "compliance",
            self.DocumentType.EVIDENCE: "evidence",
            self.DocumentType.CHANGELOG: "changelog",
            self.DocumentType.RELEASE_NOTES: "release-notes",
            self.DocumentType.SECURITY_ADVISORY: "advisory",
            self.DocumentType.VULNERABILITY_REPORT: "vulnerability-report",
            self.DocumentType.THREAT_MODEL: "threat-model",
            self.DocumentType.RISK_ASSESSMENT: "risk-assessment",
            self.DocumentType.PENTEST_REPORT: "pentest-report",
            self.DocumentType.STATIC_ANALYSIS: "static-analysis-report",
            self.DocumentType.DYNAMIC_ANALYSIS: "dynamic-analysis-report",
            self.DocumentType.QUALITY_METRICS: "quality-metrics",
            self.DocumentType.MATURITY_REPORT: "maturity-report",
            self.DocumentType.REPORT: "report",
            self.DocumentType.OTHER: "other",
        }
        return spdx_mapping.get(self.document_type, "other")

    def get_external_reference_url(self) -> str:
        """Get the external reference URL for this document."""
        return f"/api/v1/documents/{self.id}/download"
