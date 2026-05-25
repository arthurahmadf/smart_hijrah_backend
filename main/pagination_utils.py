from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginate_queryset(request, queryset, page_size=10, items_key='items'):
    """
    Utility function untuk standard pagination
    
    Args:
        request: Django request object
        queryset: QuerySet yang akan dipaginasi
        page_size: Jumlah item per halaman (default 10)
        items_key: Nama key untuk items dalam response (default 'items')
    
    Returns:
        dict: Response data untuk pagination
    """
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', page_size)
    
    # Convert to int
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = 10
    
    # Batasi page_size maksimal 100
    if page_size > 100:
        page_size = 100
    
    paginator = Paginator(queryset, page_size)
    
    try:
        items_page = paginator.page(page)
    except PageNotAnInteger:
        items_page = paginator.page(1)
    except EmptyPage:
        items_page = paginator.page(paginator.num_pages)
    
    return {
        'current_page': items_page.number,
        'total_page': paginator.num_pages,
        'total_items': paginator.count,
        items_key: list(items_page)
    }