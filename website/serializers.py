import re
from rest_framework import serializers
from .models import Course, IndianCity, Lead, ContactMessage, FAQ

class CourseDropdownSerializer(serializers.ModelSerializer):
    """Clean representation of courses for frontend dynamic dropdowns."""
    class Meta:
        model = Course
        fields = ['id', 'name', 'slug', 'category', 'duration']


class IndianCitySerializer(serializers.ModelSerializer):
    """Representation of Indian cities for dropdowns and admin."""
    class Meta:
        model = IndianCity
        fields = ['id', 'name', 'state', 'tier', 'order']


class StudentFormSubmissionSerializer(serializers.Serializer):
    """
    Serializer specifically validating the Student Form submission:
    - Full name / Your name (required)
    - Mobile number: strictly 10 digits, validated for Indian mobile standards
    - Interested course: dynamic dropdown with 'Other' option + custom text
    - City: Indian cities dropdown
    """
    # Accept snake_case or camelCase from Next.js / frontend
    full_name = serializers.CharField(required=False, max_length=150)
    fullName = serializers.CharField(required=False, max_length=150)
    name = serializers.CharField(required=False, max_length=150)

    mobile_number = serializers.CharField(required=False, max_length=20)
    mobile = serializers.CharField(required=False, max_length=20)
    phone_number = serializers.CharField(required=False, max_length=20)

    course_interest = serializers.CharField(required=False, max_length=200, allow_blank=True)
    course = serializers.CharField(required=False, max_length=200, allow_blank=True)
    courseSlug = serializers.CharField(required=False, max_length=200, allow_blank=True)
    other_course = serializers.CharField(required=False, max_length=200, allow_blank=True, allow_null=True)
    otherCourse = serializers.CharField(required=False, max_length=200, allow_blank=True, allow_null=True)

    city = serializers.CharField(required=False, max_length=100, allow_blank=True)
    cityName = serializers.CharField(required=False, max_length=100, allow_blank=True)
    city_id = serializers.IntegerField(required=False, allow_null=True)

    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    source = serializers.CharField(required=False, max_length=100, default='Website Student Form')

    # Referral & Consultant Tracking
    referral_code = serializers.CharField(required=False, max_length=50, allow_blank=True, allow_null=True)
    ref = serializers.CharField(required=False, max_length=50, allow_blank=True, allow_null=True)
    ref_code = serializers.CharField(required=False, max_length=50, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        # 1. Resolve Full Name
        full_name = attrs.get('full_name') or attrs.get('fullName') or attrs.get('name')
        if not full_name or len(full_name.strip()) < 2:
            raise serializers.ValidationError({
                'full_name': 'Please enter your full name (minimum 2 characters).'
            })
        attrs['resolved_full_name'] = full_name.strip()

        # 2. Resolve & Validate 10-digit Indian Mobile Number
        raw_mobile = attrs.get('mobile_number') or attrs.get('mobile') or attrs.get('phone_number') or ''
        cleaned_mobile = re.sub(r'[\s\-\(\)]', '', str(raw_mobile))
        
        if cleaned_mobile.startswith('+91'):
            cleaned_mobile = cleaned_mobile[3:]
        elif cleaned_mobile.startswith('91') and len(cleaned_mobile) == 12:
            cleaned_mobile = cleaned_mobile[2:]
        elif cleaned_mobile.startswith('0') and len(cleaned_mobile) == 11:
            cleaned_mobile = cleaned_mobile[1:]

        if not re.match(r'^[6-9]\d{9}$', cleaned_mobile):
            raise serializers.ValidationError({
                'mobile_number': 'Please enter a valid 10-digit Indian mobile number (e.g. 9876543210).'
            })
        attrs['resolved_mobile'] = cleaned_mobile

        # 3. Resolve Interested Course (Dropdown + 'Other')
        course_input = (
            attrs.get('course_interest') or
            attrs.get('course') or
            attrs.get('courseSlug') or
            ''
        ).strip()
        other_input = (attrs.get('other_course') or attrs.get('otherCourse') or '').strip()

        selected_course_obj = None
        final_course_title = course_input

        if course_input:
            if course_input.lower() in ('other', 'other-course'):
                final_course_title = f"Other: {other_input}" if other_input else "Other Course"
            else:
                course_match = Course.objects.filter(slug__iexact=course_input).first() or \
                               Course.objects.filter(name__iexact=course_input).first()
                if course_match:
                    selected_course_obj = course_match
                    final_course_title = course_match.name
                else:
                    final_course_title = course_input
        elif other_input:
            final_course_title = f"Other: {other_input}"
        else:
            final_course_title = "General Consultation"

        attrs['resolved_selected_course'] = selected_course_obj
        attrs['resolved_course_title'] = final_course_title
        attrs['resolved_other_course'] = other_input or (course_input if course_input.lower() == 'other' else None)

        # 4. Resolve City
        city_input = (attrs.get('city') or attrs.get('cityName') or '').strip()
        city_id = attrs.get('city_id')
        selected_city_obj = None

        if city_id:
            selected_city_obj = IndianCity.objects.filter(id=city_id, is_active=True).first()
            if selected_city_obj:
                city_input = selected_city_obj.name

        if not selected_city_obj and city_input:
            selected_city_obj = IndianCity.objects.filter(name__iexact=city_input, is_active=True).first()

        attrs['resolved_city_obj'] = selected_city_obj
        attrs['resolved_city'] = city_input if city_input else (selected_city_obj.name if selected_city_obj else 'Not Specified')

        # 5. Resolve Consultant Referral Code & Linkage
        ref_input = (
            attrs.get('referral_code') or
            attrs.get('ref') or
            attrs.get('ref_code') or
            ''
        ).strip()

        request = self.context.get('request')
        if not ref_input and request:
            ref_input = request.query_params.get('ref', '').strip()

        consultant_user = None
        source_label = attrs.get('source') or 'Website Student Form'

        if ref_input:
            from admin_app.models import Consultant
            consultant = Consultant.objects.filter(referral_code__iexact=ref_input, is_active=True).select_related('user').first()
            if consultant:
                consultant_user = consultant.user
                ref_input = consultant.referral_code
                source_label = f"Referral: {consultant.user.get_full_name} ({consultant.referral_code})"

        attrs['resolved_consultant'] = consultant_user
        attrs['resolved_referral_code'] = ref_input if ref_input else None
        attrs['resolved_source'] = source_label

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        ip = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

        lead = Lead.objects.create(
            full_name=validated_data['resolved_full_name'],
            mobile_number=validated_data['resolved_mobile'],
            email=validated_data.get('email') or None,
            course_interest=validated_data['resolved_course_title'],
            selected_course=validated_data['resolved_selected_course'],
            other_course=validated_data['resolved_other_course'],
            city=validated_data['resolved_city'],
            selected_city=validated_data['resolved_city_obj'],
            assigned_consultant=validated_data.get('resolved_consultant'),
            referral_code=validated_data.get('resolved_referral_code'),
            source=validated_data.get('resolved_source', 'Website Student Form'),
            ip_address=ip,
            status='NEW',
        )
        return lead


class LeadSerializer(serializers.ModelSerializer):
    """Detailed read representation of a student inquiry lead."""
    course_name = serializers.CharField(source='course_interest', read_only=True)
    city_name = serializers.CharField(source='city', read_only=True)
    consultant_name = serializers.CharField(source='assigned_consultant.get_full_name', read_only=True)
    consultant_email = serializers.EmailField(source='assigned_consultant.email', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'full_name', 'mobile_number', 'email', 'course_interest',
            'course_name', 'selected_course', 'other_course', 'city',
            'city_name', 'selected_city', 'assigned_consultant', 'consultant_name',
            'consultant_email', 'referral_code', 'status', 'counselor_notes',
            'source', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'counselor_notes', 'created_at', 'updated_at']


class LeadAdminSerializer(serializers.ModelSerializer):
    """Full admin serializer with status updates and counselor notes."""
    consultant_name = serializers.CharField(source='assigned_consultant.get_full_name', read_only=True)
    consultant_email = serializers.EmailField(source='assigned_consultant.email', read_only=True)

    class Meta:
        model = Lead
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for Course content management.
    Supports both camelCase (Next.js frontend) and snake_case (DRF standard)
    for all course fields.
    """
    # Accept camelCase inputs
    shortDescription = serializers.CharField(required=False, write_only=True, allow_blank=True)
    admissionInfo = serializers.CharField(required=False, write_only=True, allow_blank=True)
    imageAlt = serializers.CharField(required=False, write_only=True, allow_blank=True)
    highlightsText = serializers.CharField(required=False, write_only=True, allow_blank=True)
    title = serializers.CharField(required=False, write_only=True, allow_blank=True)
    is_active = serializers.BooleanField(required=False, write_only=True)

    # Provide frontend camelCase outputs alongside standard fields
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'slug', 'duration', 'fees', 'image', 'image_alt',
            'short_description', 'description', 'eligibility', 'highlights',
            'admission_info', 'category', 'published', 'is_featured',
            'created_at', 'updated_at',
            # write-only alias inputs
            'shortDescription', 'admissionInfo', 'imageAlt', 'highlightsText',
            'title', 'is_active',
        ]
        extra_kwargs = {
            'name': {'required': False},
            'slug': {'required': False},
            'duration': {'required': False},
            'short_description': {'required': False},
            'description': {'required': False},
            'eligibility': {'required': False},
            'admission_info': {'required': False},
        }

    def validate(self, attrs):
        # Resolve course name
        if 'title' in attrs and not attrs.get('name'):
            attrs['name'] = attrs.pop('title')
        elif not attrs.get('name') and self.instance is None:
            raise serializers.ValidationError({'name': 'Course name is required.'})

        # Resolve slug
        if not attrs.get('slug'):
            if self.instance is None:
                from django.utils.text import slugify
                attrs['slug'] = slugify(attrs.get('name', ''))
            else:
                attrs['slug'] = self.instance.slug

        # Resolve camelCase mappings
        if 'shortDescription' in attrs:
            attrs['short_description'] = attrs.pop('shortDescription')
        if 'admissionInfo' in attrs:
            attrs['admission_info'] = attrs.pop('admissionInfo')
        if 'imageAlt' in attrs:
            attrs['image_alt'] = attrs.pop('imageAlt')
        if 'is_active' in attrs:
            attrs['published'] = attrs.pop('is_active')

        # Resolve highlights (can be passed as a list of strings OR multiline highlightsText)
        if 'highlightsText' in attrs:
            raw_text = attrs.pop('highlightsText')
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            attrs['highlights'] = lines[:12]
        elif 'highlights' in attrs:
            hl = attrs.get('highlights')
            if isinstance(hl, list):
                attrs['highlights'] = [str(item).strip() for item in hl if str(item).strip()][:12]

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Mirror camelCase properties for complete Next.js frontend alignment
        data['shortDescription'] = instance.short_description
        data['admissionInfo'] = instance.admission_info
        data['imageAlt'] = instance.image_alt
        data['title'] = instance.name
        data['is_active'] = instance.published
        return data


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']


class ContactMessageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
