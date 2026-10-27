"""
URL Configuration for backend core.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

def api_root(request):
    """Root informative API overview."""
    return JsonResponse({
        'title': 'EduSaathi Backend API',
        'status': 'online',
        'docs': '/api/docs/',
        'django_admin': '/admin/',
        'endpoints': {
            'jwt_login': '/api/admin/auth/login/',
            'jwt_refresh': '/api/admin/auth/token/refresh/',
            'admin_stats': '/api/admin/dashboard/stats/',
            'admin_users': '/api/admin/users/',
            'website_health': '/api/website/health/',
            'website_courses': '/api/website/courses/',
            'website_lead_submit': '/api/website/leads/submit/',
            'website_contact_submit': '/api/website/contact/submit/',
            'website_faqs': '/api/website/faqs/',
        }
    })

from website.views import CourseListView, CourseDetailView, StudentFormSubmitView

urlpatterns = [
    # API Landing
    path('', api_root, name='api_root'),

    # Django Admin Interface
    path('admin/', admin.site.urls),

    # OpenAPI 3 Schema & Swagger UI Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Direct public endpoints matching frontend calls (/api/courses, /api/enquiries)
    path('api/courses/', CourseListView.as_view(), name='public_courses_root'),
    path('api/courses/<slug:slug>/', CourseDetailView.as_view(), name='public_course_detail_root'),
    path('api/enquiries/', StudentFormSubmitView.as_view(), name='public_enquiries_root'),

    # Admin & Consultant Application (JWT Auth, User & Consultant Management)
    path('api/admin/', include('admin_app.urls')),
    path('api/auth/', include('admin_app.urls')),
    path('api/', include('admin_app.urls')),

    # Website Application (Public Leads, Courses, Contact, FAQs)
    path('api/website/', include('website.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
