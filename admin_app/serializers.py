from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User, AdminAuditLog, SiteSetting, Consultant

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Serializer that authenticates with email and password
    and embeds comprehensive user profile data in the response.
    """
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Both email and password are required.')

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError('No active account found with the given credentials.')

        if not user.is_active:
            raise serializers.ValidationError('This account has been disabled.')

        # Call parent validate to generate refresh & access tokens
        data = super().validate(attrs)

        # Append structured user profile details
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'full_name': self.user.get_full_name,
            'phone_number': self.user.phone_number,
            'role': self.user.role,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
            'date_joined': self.user.date_joined.isoformat() if hasattr(self.user.date_joined, 'isoformat') else str(self.user.date_joined),
        }
        if hasattr(self.user, 'consultant_profile') and self.user.consultant_profile:
            data['user']['consultant_id'] = self.user.consultant_profile.id
            data['user']['referral_code'] = self.user.consultant_profile.referral_code
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for general user information."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'is_active', 'is_staff',
            'is_superuser', 'date_joined', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'updated_at']


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin user creation and updates."""
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name',
            'phone_number', 'role', 'is_active', 'is_staff', 'is_superuser'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for updating user password."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)


class AdminAuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source='actor.email', read_only=True)

    class Meta:
        model = AdminAuditLog
        fields = '__all__'


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = '__all__'


class ConsultantSerializer(serializers.ModelSerializer):
    """Full consultant detail representation including referral link and live metrics."""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    referral_link = serializers.SerializerMethodField()
    total_leads = serializers.IntegerField(read_only=True)
    new_leads = serializers.IntegerField(read_only=True)
    enrolled_leads = serializers.IntegerField(read_only=True)

    class Meta:
        model = Consultant
        fields = [
            'id', 'user_id', 'full_name', 'first_name', 'last_name', 'email',
            'phone_number', 'agency_name', 'city', 'referral_code', 'referral_link',
            'is_active', 'notes', 'total_leads', 'new_leads', 'enrolled_leads',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'referral_code', 'referral_link', 'created_at', 'updated_at']

    def get_referral_link(self, obj):
        request = self.context.get('request')
        return obj.get_referral_link(request)


class ConsultantCreateSerializer(serializers.Serializer):
    """
    Serializer for Admin creating a Consultant.
    Automatically provisions User account and generates a unique referral link.
    """
    full_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(max_length=128, required=False, write_only=True)
    agency_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    referral_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email address already exists.')
        return value.lower()

    def validate_referral_code(self, value):
        if value:
            code = value.strip().upper()
            if Consultant.objects.filter(referral_code=code).exists():
                raise serializers.ValidationError('This referral code is already in use.')
            return code
        return value

    def create(self, validated_data):
        import secrets
        import string

        full_name = validated_data.pop('full_name').strip()
        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        email = validated_data.pop('email')
        phone_number = validated_data.pop('phone_number', '')
        password = validated_data.pop('password', None)
        if not password:
            # Generate a secure 10-char default password if none provided
            chars = string.ascii_letters + string.digits + "!@#$"
            password = ''.join(secrets.choice(chars) for _ in range(10))

        # 1. Create User with role 'CONSULTANT'
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role='CONSULTANT',
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )

        # 2. Create Consultant Profile
        custom_ref = validated_data.pop('referral_code', None)
        consultant = Consultant(
            user=user,
            agency_name=validated_data.get('agency_name', ''),
            city=validated_data.get('city', ''),
            notes=validated_data.get('notes', ''),
        )
        if custom_ref:
            consultant.referral_code = custom_ref
        consultant.save()

        # Attach raw password for initial admin viewing response
        consultant.generated_password = password
        return consultant


class ConsultantLeadUpdateSerializer(serializers.Serializer):
    """Serializer for a consultant updating status and notes of their assigned lead."""
    status = serializers.ChoiceField(choices=['NEW', 'CONTACTED', 'IN_PROGRESS', 'ENROLLED', 'CLOSED'], required=False)
    counselor_notes = serializers.CharField(required=False, allow_blank=True)

