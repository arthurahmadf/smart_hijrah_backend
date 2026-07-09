# main/endpoint/hadis_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from main.utils_hadis.hybrid_search import hybrid_search

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_hybrid_search(request):
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({
            'success': True,
            'message': 'Masukkan parameter q',
            'data': []
        })
    
    results = hybrid_search(query, limit=5)
    
    return JsonResponse({
        'success': True,
        'query': query,
        'total': len(results),
        'data': results
    })