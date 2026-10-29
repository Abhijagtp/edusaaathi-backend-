from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import User, AdminAuditLog, SiteSetting, Consultant, generate_unique_referral_code
from .permissions import IsConsultant, IsAdminOrStaff
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserCreateUpdateSerializer,
    ChangePasswordSerializer,
    AdminAuditLogSerializer,
    SiteSettingSerializer,
    ConsultantSerializer,
    ConsultantCreateSerializer,
    ConsultantLeadUpdateSerializer,
)

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login endpoint: Exchange email & password for JWT access and refresh tokens
    plus complete user metadata.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(APIView):
    """
    Retrieve or update the authenticated user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Endpoint for users to update their own password.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'old_password': ['Incorrect old password.']}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Admin management of users.
    Restricted to Staff / Superusers.
    """
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateUpdateSerializer
        return UserSerializer


class AdminDashboardStatsView(APIView):
    """
    Aggregates statistical overview for the Admin Dashboard:
    - User breakdowns
    - Website inquiries & leads
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        admin_users = User.objects.filter(role='ADMIN').count()
        staff_users = User.objects.filter(role='STAFF').count()
        active_users = User.objects.filter(is_active=True).count()
        recent_cutoff = timezone.now() - timedelta(days=7)
        new_users_last_7_days = User.objects.filter(date_joined__gte=recent_cutoff).count()

        # Dynamic metrics from website app if present
        website_stats = {}
        try:
            from website.models import Lead, ContactMessage, Course
            website_stats = {
                'total_leads': Lead.objects.count(),
                'new_leads_7_days': Lead.objects.filter(created_at__gte=recent_cutoff).count(),
                'total_contact_messages': ContactMessage.objects.count(),
                'unread_contact_messages': ContactMessage.objects.filter(is_read=False).count(),
                'total_courses': Course.objects.count(),
                'active_courses': Course.objects.filter(is_active=True).count(),
            }
        except Exception:
            website_stats = {
                'total_leads': 0,
                'total_contact_messages': 0,
                'total_courses': 0,
            }

        data = {
            'users': {
                'total': total_users,
                'admins': admin_users,
                'staff': staff_users,
                'active': active_users,
                'new_last_7_days': new_users_last_7_days,
            },
            'website': website_stats,
            'server_time': timezone.now(),
        }
        return Response(data, status=status.HTTP_200_OK)


class AdminAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View audit history of admin operations."""
    queryset = AdminAuditLog.objects.all()
    serializer_class = AdminAuditLogSerializer
    permission_classes = [permissions.IsAdminUser]


class SiteSettingViewSet(viewsets.ModelViewSet):
    """Manage dynamic application configuration flags."""
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [permissions.IsAdminUser]


# --- Consultant Management Views ---

class AdminConsultantViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet to manage consultants:
    - Lists all consultants with live referral links and lead counts
    - Creates a new consultant, automatically provisioning account and referral link
    - Regenerates referral links on demand
    """
    queryset = Consultant.objects.all().select_related('user').order_by('-created_at')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return ConsultantCreateSerializer
        return ConsultantSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consultant = serializer.save()

        # Build response with generated credentials and referral link
        response_data = ConsultantSerializer(consultant, context={'request': request}).data
        response_data['initial_password'] = getattr(consultant, 'generated_password', None)
        return Response({
            'success': True,
            'message': f"Consultant {consultant.user.get_full_name} created successfully with referral link.",
            'consultant': response_data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='regenerate-link')
    def regenerate_link(self, request, pk=None):
        """Regenerate a new unique referral code and link for this consultant."""
        consultant = self.get_object()
        code = generate_unique_referral_code()
        while Consultant.objects.filter(referral_code=code).exists():
            code = generate_unique_referral_code()
        consultant.referral_code = code
        consultant.save()

        return Response({
            'success': True,
            'message': 'New referral code and link generated successfully.',
            'referral_code': consultant.referral_code,
            'referral_link': consultant.get_referral_link(request),
        }, status=status.HTTP_200_OK)


class ConsultantDashboardView(APIView):
    """
    Endpoint for a logged-in consultant to view their own profile,
    their unique referral link, and their student lead performance metrics.
    """
    permission_classes = [IsConsultant]

    def get(self, request):
        user = request.user
        consultant = getattr(user, 'consultant_profile', None)

        if not consultant and not (user.is_staff or user.is_superuser):
            return Response({'error': 'Consultant profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        from website.models import Lead
        from website.serializers import LeadSerializer
        from django.db.models import Q

        if consultant:
            leads_qs = Lead.objects.filter(
                Q(assigned_consultant=user) | Q(referral_code__iexact=consultant.referral_code)
            ).distinct()
            referral_code = consultant.referral_code
            referral_link = consultant.get_referral_link(request)
            agency_name = consultant.agency_name
        else:
            # Fallback for admin preview
            leads_qs = Lead.objects.all()
            referral_code = "ADMIN-VIEW"
            referral_link = f"{request.build_absolute_uri('/')}?ref=ADMIN"
            agency_name = "System Administrator"

        total_leads = leads_qs.count()
        new_leads = leads_qs.filter(status='NEW').count()
        contacted_leads = leads_qs.filter(status='CONTACTED').count()
        in_progress_leads = leads_qs.filter(status='IN_PROGRESS').count()
        enrolled_leads = leads_qs.filter(status='ENROLLED').count()
        closed_leads = leads_qs.filter(status='CLOSED').count()

        recent_leads = LeadSerializer(leads_qs.order_by('-created_at')[:5], many=True).data

        return Response({
            'success': True,
            'consultant': {
                'id': consultant.id if consultant else user.id,
                'full_name': user.get_full_name,
                'email': user.email,
                'phone_number': user.phone_number,
                'agency_name': agency_name,
                'referral_code': referral_code,
                'referral_link': referral_link,
            },
            'metrics': {
                'total_leads': total_leads,
                'new_leads': new_leads,
                'contacted_leads': contacted_leads,
                'in_progress_leads': in_progress_leads,
                'enrolled_leads': enrolled_leads,
                'closed_leads': closed_leads,
                'conversion_rate_percentage': round((enrolled_leads / total_leads * 100), 1) if total_leads > 0 else 0,
            },
            'recent_leads': recent_leads,
        }, status=status.HTTP_200_OK)


class ConsultantLeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for consultants to view and manage their assigned student leads.
    Non-admin consultants can only see and manage leads assigned to their account.
    """
    permission_classes = [IsConsultant]

    def get_serializer_class(self):
        from website.serializers import LeadSerializer
        return LeadSerializer

    def get_queryset(self):
        from website.models import Lead
        from django.db.models import Q
        user = self.request.user
        if user.is_staff or user.is_superuser or user.role == 'ADMIN':
            return Lead.objects.all().order_by('-created_at')
        consultant = getattr(user, 'consultant_profile', None)
        if consultant and consultant.referral_code:
            return Lead.objects.filter(
                Q(assigned_consultant=user) | Q(referral_code__iexact=consultant.referral_code)
            ).distinct().order_by('-created_at')
        return Lead.objects.filter(assigned_consultant=user).order_by('-created_at')

    def partial_update(self, request, *args, **kwargs):
        """Allow consultant to update status and counselor notes."""
        lead = self.get_object()
        serializer = ConsultantLeadUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if 'status' in serializer.validated_data:
            lead.status = serializer.validated_data['status']
        if 'counselor_notes' in serializer.validated_data:
            lead.counselor_notes = serializer.validated_data['counselor_notes']
        lead.save()

        from website.serializers import LeadSerializer
        return Response(LeadSerializer(lead).data, status=status.HTTP_200_OK)
