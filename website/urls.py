from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentFormOptionsView,
    StudentFormSubmitView,
    IndianCitiesListView,
    CourseListView,
    CourseDetailView,
    ContactMessageCreateView,
    FAQListView,
    HealthCheckView,
    LeadAdminViewSet,
    CourseAdminViewSet,
    IndianCityAdminViewSet,
    ContactMessageAdminViewSet,
)

router = DefaultRouter()
router.register(r'admin/leads', LeadAdminViewSet, basename='admin-leads')
router.register(r'admin/courses', CourseAdminViewSet, basename='admin-courses')
router.register(r'admin/cities', IndianCityAdminViewSet, basename='admin-cities')
router.register(r'admin/contact-messages', ContactMessageAdminViewSet, basename='admin-contact-messages')

urlpatterns = [
    # Student Form APIs
    path('student-form/options/', StudentFormOptionsView.as_view(), name='student_form_options'),
    path('student-form/submit/', StudentFormSubmitView.as_view(), name='student_form_submit'),
    path('cities/', IndianCitiesListView.as_view(), name='cities_list'),

    # Frontend aliases for seamless integration
    path('enquiries/', StudentFormSubmitView.as_view(), name='enquiry_submit'),
    path('leads/submit/', StudentFormSubmitView.as_view(), name='lead_submit'),
    path('dropdowns/options/', StudentFormOptionsView.as_view(), name='dropdown_options'),

    # Public Courses, Contact, FAQs, Health
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('courses/', CourseListView.as_view(), name='course_list'),
    path('courses/<slug:slug>/', CourseDetailView.as_view(), name='course_detail'),
    path('contact/submit/', ContactMessageCreateView.as_view(), name='contact_submit'),
    path('faqs/', FAQListView.as_view(), name='faq_list'),

    # Admin sub-routes under website
    path('', include(router.urls)),
]
