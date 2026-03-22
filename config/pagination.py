from rest_framework.pagination import PageNumberPagination


class ApiPageNumberPagination(PageNumberPagination):
    """page_size padrão alinhado ao front; cliente pode pedir menos/mais até max_page_size."""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
