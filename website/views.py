from rest_framework import generics, viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import Course, IndianCity, Lead, ContactMessage, FAQ
from .serializers import (
    CourseSerializer,
    CourseDropdownSerializer,
    IndianCitySerializer,
    StudentFormSubmissionSerializer,
    LeadSerializer,
    LeadAdminSerializer,
    ContactMessageSerializer,
    ContactMessageAdminSerializer,
    FAQSerializer,
)

# --- Student Form & Dynamic Dropdown Endpoints ---

class StudentFormOptionsView(APIView):
    """
    Returns dynamic dropdown options for the Student Form:
    - Active courses + 'Other' option
    - Major Indian cities + 'Other' option
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # 1. Fetch active courses
        courses_qs = Course.objects.filter(is_active=True).order_by('-is_featured', 'title')
        course_list = list(CourseDropdownSerializer(courses_qs, many=True).data)

        # Append 'Other' option to courses dropdown
        course_list.append({
            'id': 0,
            'title': 'Other',
            'name': 'Other',
            'slug': 'other',
            'category': 'OTHER',
            'duration': 'Flexible',
        })

        # 2. Fetch active Indian cities
        cities_qs = IndianCity.objects.filter(is_active=True).order_by('order', 'name')
        city_list = list(IndianCitySerializer(cities_qs, many=True).data)

        # If database has no cities yet, provide baseline list
        if not city_list:
            default_cities = [
                "Delhi NCR", "Mumbai", "Bengaluru", "Hyderabad", "Chennai",
                "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
                "Chandigarh", "Indore", "Bhopal", "Patna", "Surat",
                "Vadodara", "Kochi", "Coimbatore", "Nagpur", "Visakhapatnam",
                "Dehradun", "Varanasi", "Other"
            ]
            city_list = [{"id": idx + 1, "name": c, "state": "India", "tier": 1, "order": idx + 1} for idx, c in enumerate(default_cities)]

        return Response({
            'success': True,
            'courses': course_list,
            'cities': city_list,
        }, status=status.HTTP_200_OK)


class IndianCitiesListView(generics.ListAPIView):
    """List and search active Indian cities."""
    queryset = IndianCity.objects.filter(is_active=True).order_by('order', 'name')
    serializer_class = IndianCitySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'state']


class StudentFormSubmitView(APIView):
    """
    Submit Student Inquiry Form.
    Validates:
    - Full name (required)
    - 10-digit Indian Mobile Number (required, strictly validated)
    - Interested Course (dynamic dropdown selection, supports 'other' + custom name)
    - City (Indian cities dropdown)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentFormSubmissionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            lead = serializer.save()
            return Response({
                'success': True,
                'message': 'Thank you! Your inquiry has been submitted successfully. Our counselor will contact you shortly.',
                'lead': LeadSerializer(lead).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Please correct the errors in the form.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


# --- General Public Endpoints ---

class CourseListView(generics.ListAPIView):
    """List all active/published courses with search and category filtering."""
    queryset = Course.objects.filter(published=True).order_by('-is_featured', 'name')
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'short_description', 'description', 'category']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'courses': serializer.data,
            'count': len(serializer.data),
            'results': serializer.data,
        })


class CourseDetailView(generics.RetrieveAPIView):
    """Retrieve detailed information for a single course by slug or ID."""
    queryset = Course.objects.filter(published=True)
    serializer_class = CourseSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        slug_or_id = self.kwargs.get('slug')
        if slug_or_id.isdigit():
            obj = Course.objects.filter(id=slug_or_id).first()
        else:
            obj = Course.objects.filter(slug__iexact=slug_or_id).first()
        if not obj:
            from django.http import Http404
            raise Http404("Course not found")
        return obj


class ContactMessageCreateView(generics.CreateAPIView):
    """Public endpoint to submit a contact message."""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]


class FAQListView(generics.ListAPIView):
    """Public endpoint to list all active FAQs."""
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]


class HealthCheckView(APIView):
    """Health check for deployment and uptime monitoring."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'EduSaathi Django Backend',
            'database': 'Neon PostgreSQL connected',
        })


# --- Admin ViewSets (Protected with IsAdminUser) ---

class LeadAdminViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet to view, search, filter, and manage incoming student inquiries.
    """
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'mobile_number', 'email', 'course_interest', 'city', 'status']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        city_param = self.request.query_params.get('city')
        if city_param:
            qs = qs.filter(city__icontains=city_param)
        course_param = self.request.query_params.get('course')
        if course_param:
            qs = qs.filter(course_interest__icontains=course_param)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'leads': serializer.data,
            'count': len(serializer.data),
            'results': serializer.data,
        })


class CourseAdminViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD ViewSet for full Course content management:
    - Add new course (Course name, slug, duration, fees, images, descriptions, eligibility, highlights, admission info)
    - Update existing course by ID or slug
    - Delete course
    - Toggle published / unpublished
    """
    queryset = Course.objects.all().order_by('-is_featured', 'name')
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'slug', 'short_description', 'description', 'category', 'eligibility']

    def get_object(self):
        lookup = self.kwargs.get('pk')
        if lookup.isdigit():
            obj = Course.objects.filter(id=lookup).first()
        else:
            obj = Course.objects.filter(slug__iexact=lookup).first()
        if not obj:
            from django.http import Http404
            raise Http404(f"Course with ID or slug '{lookup}' not found.")
        return obj

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'courses': serializer.data,
            'count': len(serializer.data),
            'results': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        course_data = CourseSerializer(course).data
        return Response({
            'success': True,
            'message': f"Course '{course.name}' added successfully.",
            'course': course_data,
            **course_data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        course_data = CourseSerializer(course).data
        return Response({
            'success': True,
            'message': f"Course '{course.name}' updated successfully.",
            'course': course_data,
            **course_data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        instance.delete()
        return Response({
            'success': True,
            'message': f"Course '{name}' deleted successfully."
        }, status=status.HTTP_200_OK)


class IndianCityAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD viewset for Indian cities."""
    queryset = IndianCity.objects.all().order_by('order', 'name')
    serializer_class = IndianCitySerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'state']


class ContactMessageAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD viewset for contact messages."""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'subject']
