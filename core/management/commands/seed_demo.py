"""
Fill FixNaija with demo data.

    python manage.py seed_demo

Replaces all technician profiles and their related listings, bookings, and
reviews with 20 demo technicians across 8 categories and all Lagos LGAs. It
also creates customers and completed jobs with reviews so ratings show up.
Safe to run more than once.
All demo users have the password: fixnaija123
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import UserProfile
from bookings.models import Booking
from reviews.models import Review
from technicians.models import (
    ServiceArea, ServiceCategory, ServiceListing, TechnicianProfile,
    TechnicianVerificationRequest,
)
from technicians.location_data import LAGOS_LGAS

PASSWORD = "fixnaija123"

AREAS = list(dict.fromkeys([
    "Ajah", "Sangotedo", "Lekki", "Ikeja", "Yaba", "Surulere",
    "Victoria Island", *LAGOS_LGAS,
]))

# category -> list of (title, description, min price, max price or None)
SERVICES = {
    "Electrician": [
        ("Wiring and fault finding", "Full house wiring, tracing power faults, tripping breakers and socket problems.", 4000, 30000),
        ("Socket and light installation", "Installation of sockets, switches, ceiling lights and distribution boards.", 2500, 12000),
    ],
    "Plumber": [
        ("Leak and pipe repair", "Fixing leaking pipes, taps, toilets and water heaters quickly and cleanly.", 3500, 15000),
        ("Borehole and tank connection", "Connecting overhead tanks, pumps and borehole lines to your building.", 8000, 45000),
    ],
    "Phone and laptop repair": [
        ("Screen replacement", "Cracked or broken screen replacement for phones and laptops, with warranty.", 6000, 55000),
        ("Charging and battery repair", "Charging port repair, battery replacement and software fixes for slow devices.", 3000, 20000),
    ],
    "Mechanic": [
        ("Car servicing and diagnosis", "Engine diagnosis, oil change, brake service and full car inspection.", 5000, 60000),
        ("Brake and suspension repair", "Replacement of brake pads, shocks and suspension parts on most car brands.", 8000, 70000),
    ],
    "Tailor": [
        ("Dress alterations", "Alterations, hemming and resizing for dresses, trousers, shirts and native wear.", 1500, 8000),
        ("Custom outfits made to measure", "Native wear, suits and event outfits sewn to your measurements and style.", 12000, 80000),
    ],
    "AC technician": [
        ("AC repair and servicing", "Inspection, gas refill, cleaning and servicing for split and window units.", 5000, 25000),
        ("AC installation", "Supply-side installation and relocation of split units, including piping and mounting.", 15000, 60000),
    ],
    "Painter": [
        ("Interior painting", "Interior walls and ceilings painted neatly, with surface preparation included.", 25000, 250000),
        ("Exterior and fence painting", "Weather-proof exterior painting for buildings, gates and fences.", 40000, 400000),
    ],
    "Carpenter": [
        ("Furniture repair and assembly", "Repair of chairs, tables and wardrobes, and assembly of flat-pack furniture.", 3000, 25000),
        ("Custom wardrobes and doors", "Built-to-measure wardrobes, kitchen cabinets and doors in quality wood.", 40000, 350000),
    ],
}

# (username, first, last, category, about, base location, status, areas, how many services, price factor)
# status: V verified, P pending request, R rejected request, N never asked for verification
TECHS = [
    ("emeka",   "Emeka",   "Nwosu",    "Electrician", "Licensed electrician with 10 years of experience in homes and small offices.", "Ikeja", "V", ["Ikeja", "Yaba"], 2, 1.0),
    ("chinedu", "Chinedu", "Okoro",    "Electrician", "Wiring and inverter installation specialist. Neat work and fair prices.", "Surulere", "V", ["Surulere", "Yaba", "Ikeja"], 2, 1.1),
    ("tunde",   "Tunde",   "Bello",    "Electrician", "Electrician covering the Lagos mainland. New on the platform.", "Ikeja", "P", ["Ikeja"], 1, 0.9),
    ("ngozi",   "Ngozi",   "Eze",      "Plumber",     "Plumber with 8 years of experience in leaks, drainage and bathroom fittings.", "Yaba", "V", ["Yaba", "Surulere"], 2, 1.0),
    ("bayo",    "Bayo",    "Adeleke",  "Plumber",     "Plumbing and borehole connection for homes and estates across the island.", "Lekki", "V", ["Lekki", "Ajah", "Victoria Island"], 2, 1.2),
    ("sola",    "Sola",    "Ibitoye",  "Plumber",     "General plumbing repairs. Verification documents were incomplete.", "Sangotedo", "R", ["Sangotedo", "Ajah"], 1, 0.8),
    ("femi",    "Femi",    "Ogunleye", "Phone and laptop repair", "Phone and laptop repair shop owner. Same-day screen and battery replacement.", "Ikeja", "V", ["Ikeja", "Yaba"], 2, 1.0),
    ("amaka",   "Amaka",   "Obi",      "Phone and laptop repair", "Laptop technician. Hardware upgrades, data recovery and software fixes.", "Lekki", "V", ["Lekki", "Victoria Island", "Ajah"], 2, 1.15),
    ("ibrahim", "Ibrahim", "Sanni",    "Mechanic",    "Auto mechanic with 12 years on Toyota, Honda and Lexus models.", "Ikeja", "V", ["Ikeja", "Surulere"], 2, 1.0),
    ("uche",    "Uche",    "Anyanwu",  "Mechanic",    "Mobile mechanic who comes to you for servicing and brake repairs.", "Ajah", "V", ["Ajah", "Sangotedo", "Lekki"], 2, 1.1),
    ("segun",   "Segun",   "Balogun",  "Mechanic",    "Engine and gearbox specialist. Applied for verification, waiting for review.", "Yaba", "P", ["Yaba", "Surulere"], 1, 1.0),
    ("bisi",    "Bisi",   "Adebayo",   "Tailor",      "Custom tailoring and alterations for native wear and corporate outfits.", "Lekki", "V", ["Lekki", "Victoria Island"], 2, 1.0),
    ("folake",  "Folake", "Coker",     "Tailor",      "Ankara and lace specialist. Quick turnaround on event outfits.", "Surulere", "P", ["Surulere", "Yaba"], 2, 0.95),
    ("kudus",   "Kudus",  "Adeyemi",   "AC technician", "AC repair and maintenance, 7 years of experience on all major brands.", "Ajah", "V", ["Ajah", "Lekki"], 2, 1.0),
    ("rotimi",  "Rotimi", "Salami",    "AC technician", "AC installation and gas refill for homes and offices on the island.", "Victoria Island", "V", ["Victoria Island", "Lekki", "Ajah"], 2, 1.2),
    ("hassan",  "Hassan", "Yusuf",     "AC technician", "Refrigeration and AC repair. Has not requested verification yet.", "Ikeja", "N", ["Ikeja", "Yaba"], 1, 0.9),
    ("dayo",    "Dayo",   "Fashola",   "Painter",     "Interior and exterior painter with a small trained crew.", "Sangotedo", "V", ["Sangotedo", "Ajah", "Lekki"], 2, 1.0),
    ("kelechi", "Kelechi", "Nnadi",    "Painter",     "Painting and POP finishing. Verification request is under review.", "Yaba", "P", ["Yaba", "Surulere", "Ikeja"], 2, 0.9),
    ("musa",    "Musa",   "Garba",     "Carpenter",   "Carpenter for doors, wardrobes and furniture repair. 15 years in the trade.", "Surulere", "V", ["Surulere", "Yaba", "Ikeja"], 2, 1.0),
    ("tobi",    "Tobi",   "Akande",    "Carpenter",   "Custom wardrobes and kitchen cabinets made to measure.", "Lekki", "V", ["Lekki", "Ajah", "Victoria Island"], 2, 1.25),
]

CUSTOMERS = [
    ("adaobi", "Adaobi", "Umeh"), ("chika", "Chika", "Madu"), ("yusuf", "Yusuf", "Lawal"),
    ("tola", "Tola", "Ajayi"), ("ify", "Ifeoma", "Okeke"), ("david", "David", "Eyo"),
]

COMMENTS = {
    5: ["Excellent work and very professional.", "Arrived on time and fixed it the same day.", "Great price and neat finish. Will book again."],
    4: ["Good job overall. Took a little longer than expected.", "Solid work and polite. Would recommend."],
    3: ["Job was done but I had to follow up a few times."],
}

# rating pattern per technician, so averages differ
RATING_PATTERNS = [(5, 5, 4), (5, 4), (5, 5, 5, 4), (4, 4, 3), (5,), (5, 4, 4), (5, 5), (4, 3)]


class Command(BaseCommand):
    help = "Replace technician demo data and create customers, jobs and reviews."

    @transaction.atomic
    def handle(self, *args, **options):
        Booking.objects.filter(technician__in=TechnicianProfile.objects.all()).delete()
        TechnicianProfile.objects.all().delete()

        User = get_user_model()
        cats = {n: ServiceCategory.objects.get_or_create(name=n)[0] for n in SERVICES}
        areas = {n: ServiceArea.objects.get_or_create(name=n)[0] for n in AREAS}

        def get_user(username, first, last):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last,
                          "email": f"{username}@example.com"})
            if created:
                user.set_password(PASSWORD)
                user.save()
            elif (user.first_name, user.last_name) != (first, last):
                user.first_name, user.last_name = first, last
                user.save(update_fields=["first_name", "last_name"])
            UserProfile.objects.get_or_create(user=user)
            return user

        customers = [get_user(*c) for c in CUSTOMERS]
        technicians = []

        for i, (username, first, last, cat, about, base, status, area_names, n_services, factor) in enumerate(TECHS):
            user = get_user(username, first, last)
            tech = TechnicianProfile.objects.create(
                user=user, professional_info=about,
                is_verified=status == "V")
            tech.categories.add(cats[cat])
            tech.base_locations.set([areas[name] for name in area_names])
            for title, desc, lo, hi in SERVICES[cat][:n_services]:
                listing = ServiceListing.objects.create(
                    technician=tech, category=cats[cat], title=title, description=desc,
                    min_price=self._round(lo * factor), max_price=self._round(hi * factor))
                listing.service_areas.set([areas[a] for a in area_names])
            self._verification_request(tech, status)
            technicians.append((tech, status, i))

        made = 0
        for tech, status, i in technicians:
            if status != "V":
                continue
            service = tech.service_listings.first()
            area = service.service_areas.first()
            pattern = RATING_PATTERNS[i % len(RATING_PATTERNS)]
            for j, rating in enumerate(pattern):
                customer = customers[(i + j) % len(customers)]
                booking = Booking.objects.create(
                    customer=customer, technician=tech, service=service, area=area,
                    address=f"{10 + j} {area.name} Road, {area.name}",
                    description="Needs attention as soon as possible.",
                    status=Booking.COMPLETED)
                comments = COMMENTS[rating]
                Review.objects.create(
                    booking=booking, reviewer=customer, technician=tech, rating=rating,
                    comment=comments[(i + j) % len(comments)])
                made += 1

        total = TechnicianProfile.objects.filter(user__username__in=[t[0] for t in TECHS]).count()
        verified = TechnicianProfile.objects.filter(
            user__username__in=[t[0] for t in TECHS], is_verified=True).count()
        self.stdout.write(self.style.SUCCESS(
            f"Done. {total} technicians ({verified} verified = {round(100 * verified / total)}%), "
            f"{len(SERVICES)} categories, {len(AREAS)} areas, {made} new reviews."))
        self.stdout.write(f"Log in as any technician or customer. Password: {PASSWORD}")

    @staticmethod
    def _round(value):
        return Decimal(int(round(value / 500.0)) * 500)

    @staticmethod
    def _verification_request(tech, status):
        if status in ("P", "R"):
            request = TechnicianVerificationRequest(
                technician=tech,
                status="pending" if status == "P" else "rejected",
                review_notes="" if status == "P" else
                "The identity document was unclear. Please upload a clearer photo.",
            )
            if status == "R":
                request.reviewed_at = timezone.now()
            request.identity_document.save(
                f"{tech.user.username}-id.txt", ContentFile(b"demo document"), save=False)
            request.save()
