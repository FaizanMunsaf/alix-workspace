from sqladmin import ModelView

from core.models.clause_embeddings import ClauseEmbedding


class ClauseEmbeddingAdmin(ModelView, model=ClauseEmbedding):
    name = "Clause Embedding"
    name_plural = "Clause Embeddings"
    icon = "ti ti-vector"

    column_list = [
        ClauseEmbedding.id,
        ClauseEmbedding.version_id,
        ClauseEmbedding.ast_node_id,
        ClauseEmbedding.clause_category,
        ClauseEmbedding.created_at,
    ]
    column_searchable_list = [ClauseEmbedding.clause_category]
    column_sortable_list = [ClauseEmbedding.created_at]
    column_default_sort = [(ClauseEmbedding.created_at, True)]
    form_columns = [
        ClauseEmbedding.version_id,
        ClauseEmbedding.ast_node_id,
        ClauseEmbedding.clause_category,
        ClauseEmbedding.content,
    ]
    column_details_exclude_list = [ClauseEmbedding.embedding]
