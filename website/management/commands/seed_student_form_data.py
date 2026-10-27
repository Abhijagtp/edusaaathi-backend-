from django.core.management.base import BaseCommand
from website.models import Course, IndianCity

class Command(BaseCommand):
    help = 'Seeds initial Indian cities and educational courses for student inquiry dropdowns'

    def handle(self, *args, **options):
        # 1. Seed Indian Cities
        cities_data = [
            # Metros / Tier 1
            {"name": "Delhi NCR", "state": "Delhi / NCR", "tier": 1, "order": 1},
            {"name": "Mumbai", "state": "Maharashtra", "tier": 1, "order": 2},
            {"name": "Bengaluru", "state": "Karnataka", "tier": 1, "order": 3},
            {"name": "Hyderabad", "state": "Telangana", "tier": 1, "order": 4},
            {"name": "Chennai", "state": "Tamil Nadu", "tier": 1, "order": 5},
            {"name": "Kolkata", "state": "West Bengal", "tier": 1, "order": 6},
            {"name": "Pune", "state": "Maharashtra", "tier": 1, "order": 7},
            {"name": "Ahmedabad", "state": "Gujarat", "tier": 1, "order": 8},
            # Tier 2 & Key Student Hubs
            {"name": "Jaipur", "state": "Rajasthan", "tier": 2, "order": 9},
            {"name": "Lucknow", "state": "Uttar Pradesh", "tier": 2, "order": 10},
            {"name": "Chandigarh", "state": "Punjab / Haryana", "tier": 2, "order": 11},
            {"name": "Indore", "state": "Madhya Pradesh", "tier": 2, "order": 12},
            {"name": "Bhopal", "state": "Madhya Pradesh", "tier": 2, "order": 13},
            {"name": "Patna", "state": "Bihar", "tier": 2, "order": 14},
            {"name": "Surat", "state": "Gujarat", "tier": 2, "order": 15},
            {"name": "Vadodara", "state": "Gujarat", "tier": 2, "order": 16},
            {"name": "Kochi", "state": "Kerala", "tier": 2, "order": 17},
            {"name": "Coimbatore", "state": "Tamil Nadu", "tier": 2, "order": 18},
            {"name": "Nagpur", "state": "Maharashtra", "tier": 2, "order": 19},
            {"name": "Visakhapatnam", "state": "Andhra Pradesh", "tier": 2, "order": 20},
            {"name": "Dehradun", "state": "Uttarakhand", "tier": 2, "order": 21},
            {"name": "Varanasi", "state": "Uttar Pradesh", "tier": 2, "order": 22},
            {"name": "Agra", "state": "Uttar Pradesh", "tier": 2, "order": 23},
            {"name": "Kanpur", "state": "Uttar Pradesh", "tier": 2, "order": 24},
            {"name": "Ranchi", "state": "Jharkhand", "tier": 2, "order": 25},
            {"name": "Guwahati", "state": "Assam", "tier": 2, "order": 26},
            {"name": "Bhubaneswar", "state": "Odisha", "tier": 2, "order": 27},
            {"name": "Ludhiana", "state": "Punjab", "tier": 2, "order": 28},
            {"name": "Amritsar", "state": "Punjab", "tier": 2, "order": 29},
            {"name": "Raipur", "state": "Chhattisgarh", "tier": 2, "order": 30},
            {"name": "Jodhpur", "state": "Rajasthan", "tier": 2, "order": 31},
            {"name": "Goa", "state": "Goa", "tier": 2, "order": 32},
            {"name": "Other City", "state": "India", "tier": 3, "order": 999},
        ]

        cities_created = 0
        for item in cities_data:
            _, created = IndianCity.objects.get_or_create(
                name=item["name"],
                defaults={
                    "state": item["state"],
                    "tier": item["tier"],
                    "order": item["order"],
                    "is_active": True,
                }
            )
            if created:
                cities_created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {cities_created} new Indian cities."))

        # 2. Seed Initial Popular Courses if none exist
        courses_data = [
            {"title": "B.Tech - Computer Science & Engineering", "category": "ENGINEERING", "duration": "4 Years"},
            {"title": "B.Tech - Artificial Intelligence & Data Science", "category": "ENGINEERING", "duration": "4 Years"},
            {"title": "MBA - Master of Business Administration", "category": "MANAGEMENT", "duration": "2 Years"},
            {"title": "BBA - Bachelor of Business Administration", "category": "MANAGEMENT", "duration": "3 Years"},
            {"title": "BCA - Bachelor of Computer Applications", "category": "ENGINEERING", "duration": "3 Years"},
            {"title": "MCA - Master of Computer Applications", "category": "ENGINEERING", "duration": "2 Years"},
            {"title": "MBBS - Medicine & Surgery", "category": "MEDICAL", "duration": "5.5 Years"},
            {"title": "B.Sc - Nursing & Healthcare", "category": "MEDICAL", "duration": "4 Years"},
            {"title": "Digital Marketing & Analytics Certification", "category": "ONLINE", "duration": "6 Months"},
            {"title": "Full Stack Web & Software Development", "category": "ONLINE", "duration": "6 Months"},
        ]

        courses_created = 0
        for c in courses_data:
            _, created = Course.objects.get_or_create(
                title=c["title"],
                defaults={
                    "category": c["category"],
                    "duration": c["duration"],
                    "short_description": f"Comprehensive {c['title']} program with top placement assistance.",
                    "is_active": True,
                    "is_featured": True,
                }
            )
            if created:
                courses_created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {courses_created} new courses."))
