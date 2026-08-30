from sqladmin import ModelView

from core.models.document_ast_node import DocumentASTNode


class DocumentASTNodeAdmin(ModelView, model=DocumentASTNode):
    name = "AST Node"
    name_plural = "AST Nodes"
    icon = "fa-solid fa-sitemap"

    column_list = [
        DocumentASTNode.id,
        DocumentASTNode.version_id,
        DocumentASTNode.parent_id,
        DocumentASTNode.node_type,
        DocumentASTNode.node_index,
        DocumentASTNode.title,
        DocumentASTNode.created_at,
    ]
    column_searchable_list = [DocumentASTNode.node_type, DocumentASTNode.title]
    column_sortable_list = [
        DocumentASTNode.node_index,
        DocumentASTNode.created_at,
    ]
    column_default_sort = [(DocumentASTNode.node_index, False)]
    form_columns = [
        DocumentASTNode.version_id,
        DocumentASTNode.parent_id,
        DocumentASTNode.node_type,
        DocumentASTNode.node_index,
        DocumentASTNode.title,
        DocumentASTNode.content,
        DocumentASTNode.metadata_info,
    ]
