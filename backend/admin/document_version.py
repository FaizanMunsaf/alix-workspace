from sqladmin import ModelView

from core.models.document_version import DocumentVersion


class DocumentVersionAdmin(ModelView, model=DocumentVersion):
    name = "Document Version"
    name_plural = "Document Versions"
    icon = "ti ti-versions"

    column_list = [
        DocumentVersion.id,
        DocumentVersion.document_id,
        DocumentVersion.version_number,
        DocumentVersion.processing_status,
        DocumentVersion.created_at,
    ]
    column_searchable_list = [DocumentVersion.processing_status]
    column_sortable_list = [
        DocumentVersion.version_number,
        DocumentVersion.created_at,
    ]
    column_default_sort = [(DocumentVersion.created_at, True)]
    form_columns = [
        DocumentVersion.document_id,
        DocumentVersion.version_number,
        DocumentVersion.raw_text,
        DocumentVersion.file_path,
        DocumentVersion.ast_json,
        DocumentVersion.processing_status,
    ]
