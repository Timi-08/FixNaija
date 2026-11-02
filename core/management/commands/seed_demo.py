from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from bookings.models import Booking
from reviews.models import Review
from technicians.models import (
    ServiceArea, ServiceCategory, ServiceListing, TechnicianProfile,
)

CATEGORIES = [
    "Electrician", "Plumber", "Phone and laptop repair", "Mechanic",
    "Tailor", "AC technician", "Painter", "Carpenter",
]
AREAS = ["Ajah", "Sangotedo", "Lekki", "Ikeja", "Yaba", "Surulere", "Victoria Island"]


class Command(BaseCommand):
    help = "Create demo categories, areas, users, services and one reviewed job."

    def handle(self, *args, **options):
        User = get_user_model()
        cats = {n: ServiceCategory.objects.get_or_create(name=n)[0] for n in CATEGORIES}
        areas = {n: ServiceArea.objects.get_or_create(name=n)[0] for n in AREAS}

        def user(username):
            u, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@example.com"}
            )
            if created:
                u.set_password("fixnaija123")
                u.save()
            UserProfile.objects.get_or_create(user=u)
            return u

        def tech(username, info, place, verified, services):
            t, created = TechnicianProfile.objects.get_or_create(
                user=user(username),
                defaults={"professional_info": info, "base_location": place,
                          "is_verified": verified},
            )
            if created:
                for cat, title, desc, lo, hi, where in services:
                    s = ServiceListing.objects.create(
                        technician=t, category=cats[cat], title=title,
                        description=desc, min_price=lo, max_price=hi)
                    s.service_areas.set([areas[a] for a in where])
            return t

        kudus = tech("kudus", "AC repair and maintenance, 7 years experience.", "Ajah", True,
                     [("AC technician", "AC repair and servicing",
                       "Inspection, gas refill and servicing for split and window units.",
                       5000, 25000, ["Ajah", "Lekki"])])
        tech("ngozi", "Plumber covering the mainland.", "Yaba", True,
             [("Plumber", "Leak and pipe repair",
               "Fixing leaking pipes, taps, toilets and water heaters quickly.",
               3500, 15000, ["Yaba", "Surulere"])])
        tech("tunde", "Licensed electrician.", "Ikeja", False,
             [("Electrician", "Wiring and fault finding",
               "Full house wiring, socket installation and fault finding.",
               4000, None, ["Ikeja"])])
        bisi_tech = tech("bisi", "Custom tailoring and alterations.", "Lekki", True,
                         [("Tailor", "Dress alterations",
                           "Alterations, hemming and custom outfits made to measure.",
                           6000, 30000, ["Lekki", "Victoria Island"])])

        bisi = bisi_tech.user
        if not Booking.objects.filter(customer=bisi, technician=kudus).exists():
            b = Booking.objects.create(
                customer=bisi, technician=kudus, service=kudus.service_listings.first(),
                area=areas["Ajah"], address="12 Admiralty Way, Ajah",
                description="AC not cooling.", status=Booking.COMPLETED)
            Review.objects.create(booking=b, reviewer=bisi, technician=kudus,
                                  rating=5, comment="Fixed my AC the same day.")
        self.stdout.write(self.style.SUCCESS(
            "Demo data ready. Logins: kudus, ngozi, tunde, bisi. Password: fixnaija123"))
