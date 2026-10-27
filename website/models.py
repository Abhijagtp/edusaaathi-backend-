from django.db import models
from django.utils.text import slugify

class Course(models.Model):
    """
    Educational courses offered on EduSaathi website.
    Fields support full content management:
    - Course name *
    - URL slug *
    - Typical duration *
    - Fees (optional)
    - Image URL or site path (optional)
    - Image alt text (optional)
    - Short description *
    - Course description *
    - Eligibility *
    - Highlights (list of up to 12 items)
    - Admission information *
    - Published / is_active
    """
    CATEGORY_CHOICES = (
        ('COMMERCE', 'Commerce & Banking'),
        ('ENGINEERING', 'Engineering & Tech'),
        ('MANAGEMENT', 'Management & MBA'),
        ('MEDICAL', 'Medical & Healthcare'),
        ('ARTS_SCIENCE', 'Arts & Science'),
        ('ONLINE', 'Online Certifications'),
        ('GENERAL', 'General Programmes'),
    )

    name = models.CharField(max_length=255, default='', verbose_name="Course Name")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL Slug")
    duration = models.CharField(max_length=120, default='', verbose_name="Typical Duration", help_text="e.g. Typically 3 years")
    fees = models.CharField(max_length=150, blank=True, default='', verbose_name="Fees", help_text="e.g. Contact the institution")
    image = models.CharField(max_length=500, blank=True, default='', verbose_name="Image URL or Site Path", help_text="e.g. /images/course.webp")
    image_alt = models.CharField(max_length=255, blank=True, default='', verbose_name="Image Alt Text")
    short_description = models.TextField(default='', verbose_name="Short Description")
    description = models.TextField(default='', verbose_name="Course Description")
    eligibility = models.TextField(default='', verbose_name="Eligibility Criteria")
    highlights = models.JSONField(default=list, blank=True, verbose_name="Course Highlights")
    admission_info = models.TextField(default='', verbose_name="Admission Information")

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='GENERAL', blank=True)
    published = models.BooleanField(default=True, verbose_name="Published Status")
    is_featured = models.BooleanField(default=False, verbose_name="Featured")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'name']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def title(self):
        """Backward compatibility for title"""
        return self.name

    @title.setter
    def title(self, value):
        self.name = value

    @property
    def is_active(self):
        """Backward compatibility for is_active"""
        return self.published

    @is_active.setter
    def is_active(self, value):
        self.published = value


class IndianCity(models.Model):
    """List of Indian cities for dynamic dropdown selection."""
    name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100, blank=True)
    tier = models.PositiveSmallIntegerField(default=1, help_text="1: Metro/Tier 1, 2: Tier 2, 3: Other")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Indian City'
        verbose_name_plural = 'Indian Cities'

    def __str__(self):
        return f"{self.name} ({self.state})" if self.state else self.name


class Lead(models.Model):
    """
    Student inquiry / admission consultation lead.
    Supports form fields:
    - Full Name / Your Name
    - 10-digit Mobile Number
    - Interested Course (selected course or other with custom input)
    - City (Indian cities dropdown with option for other)
    """
    STATUS_CHOICES = (
        ('NEW', 'New Inquiry'),
        ('CONTACTED', 'Contacted'),
        ('IN_PROGRESS', 'Counseling In Progress'),
        ('ENROLLED', 'Enrolled'),
        ('CLOSED', 'Closed / Lost'),
    )

    full_name = models.CharField(max_length=150, verbose_name="Full Name")
    mobile_number = models.CharField(max_length=15, default='', db_index=True, verbose_name="Mobile Number")
    email = models.EmailField(blank=True, null=True, verbose_name="Email Address")

    # Course details
    course_interest = models.CharField(max_length=200, default='', verbose_name="Course Interest")
    selected_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inquiries',
        verbose_name="Selected Course"
    )
    other_course = models.CharField(max_length=200, blank=True, null=True, verbose_name="Other Course Name")

    # Location details
    city = models.CharField(max_length=100, default='', verbose_name="City")
    selected_city = models.ForeignKey(
        IndianCity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inquiries',
        verbose_name="Selected City"
    )

    # Lead Tracking & Management
    assigned_consultant = models.ForeignKey(
        'admin_app.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
        verbose_name="Assigned Consultant"
    )
    referral_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Referral Code"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', db_index=True)
    counselor_notes = models.TextField(blank=True, verbose_name="Counselor Notes")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    source = models.CharField(max_length=100, default='Website Student Form', blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Inquiry / Lead'
        verbose_name_plural = 'Student Inquiries / Leads'

    def __str__(self):
        return f"{self.full_name} - {self.mobile_number} ({self.course_interest})"


class ContactMessage(models.Model):
    """General contact form inquiries from website visitors."""
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name}: {self.subject}"


class FAQ(models.Model):
    """Frequently Asked Questions for website visitors."""
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question
