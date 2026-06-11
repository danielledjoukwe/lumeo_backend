from rest_framework.response import Response
from rest_framework import status


def paginate_queryset(request, queryset, serializer_class):
    try:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
    except ValueError:
        page = 1
        page_size = 10

    page = max(page, 1)
    page_size = max(page_size, 1)

    start = (page - 1) * page_size
    end = start + page_size

    total_count = queryset.count()
    paginated_qs = queryset[start:end]

    serializer = serializer_class(paginated_qs, many=True)

    return Response(
        {
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "results": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


def paginate_list(request, data_list):
    try:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
    except ValueError:
        page = 1
        page_size = 10

    page = max(page, 1)
    page_size = max(page_size, 1)

    start = (page - 1) * page_size
    end = start + page_size

    total_count = len(data_list)
    paginated_data = data_list[start:end]

    return Response(
        {
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "results": paginated_data,
        },
        status=status.HTTP_200_OK,
    )