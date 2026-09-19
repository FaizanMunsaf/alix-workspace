from sqladmin import ModelView

from core.models.documents import Document


class DocumentAdmin(ModelView, model=Document):
    name = "Document"
    name_plural = "Documents"
    icon = "ti ti-file-text"

    column_list = [
        Document.id,
        Document.title,
        Document.document_type,
        Document.status,
        Document.created_at,
        Document.updated_at,
    ]
    column_searchable_list = [Document.title, Document.document_type, Document.status]
    column_sortable_list = [Document.title, Document.created_at, Document.updated_at]
    column_default_sort = [(Document.created_at, True)]
    form_columns = [
        Document.title,
        Document.document_type,
        Document.status,
        Document.metadata_info,
    ]
