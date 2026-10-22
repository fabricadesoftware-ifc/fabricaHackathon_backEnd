from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Páginas de 8 itens (o front pagina de 8 em 8); `?page_size=` até 100."""

    page_size = 8
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        # Paginação estável também em querysets sem ordenação definida.
        if hasattr(queryset, "ordered") and not queryset.ordered:
            queryset = queryset.order_by("pk")
        return super().paginate_queryset(queryset, request, view)
