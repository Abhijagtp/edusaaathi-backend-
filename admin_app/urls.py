from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    CustomTokenObtainPairView,
    UserProfileView,
    ChangePasswordView,
    AdminUserViewSet,
    AdminDashboardStatsView,
    AdminAuditLogViewSet,
    SiteSettingViewSet,
    AdminConsultantViewSet,
    ConsultantDashboardView,
    ConsultantLeadViewSet,
)

from website.views import CourseAdminViewSet, LeadAdminViewSet

router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-users')
router.register(r'consultants', AdminConsultantViewSet, basename='admin-consultants')
router.register(r'consultant/leads', ConsultantLeadViewSet, basename='consultant-leads')
router.register(r'courses', CourseAdminViewSet, basename='admin-courses')
router.register(r'leads', LeadAdminViewSet, basename='admin-leads')
router.register(r'logs', AdminAuditLogViewSet, basename='admin-logs')
router.register(r'settings', SiteSettingViewSet, basename='admin-settings')

urlpatterns = [
    # Direct Auth Endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('profile/', UserProfileView.as_view(), name='user_profile_alt'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # Also support nested 'auth/' paths if accessed via /api/admin/auth/...
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='auth_token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='auth_token_verify'),
    path('auth/me/', UserProfileView.as_view(), name='auth_user_profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth_change_password'),

    # Consultant Specific Endpoints
    path('consultant/dashboard/', ConsultantDashboardView.as_view(), name='consultant_dashboard'),

    # Admin Management & Dashboard Endpoints
    path('dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin_dashboard_stats'),
    path('', include(router.urls)),
]
