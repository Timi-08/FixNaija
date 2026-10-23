
from decimal import Decimal

from technicians.models import (
    TechnicianProfile,
    ServiceCategory,
    ServiceArea,
    ServiceListing,
)


# Find the existing records we need.
category = ServiceCategory.objects.get(name="Phone Repair")

technicians = {
    technician.id: technician
    for technician in TechnicianProfile.objects.all()
}

areas = {
    area.name: area
    for area in ServiceArea.objects.filter(
        is_active=True,
        name__in=["Lekki", "Ajah", "Victoria Island"],
    )
}

required_areas = {"Lekki", "Ajah", "Victoria Island"}

if len(technicians) < 2:
    raise ValueError("At least two technician profiles are required.")

if not required_areas.issubset(areas):
    raise ValueError("One or more required service areas are missing.")

test_listings = [
    {
        "title": "Android Screen Replacement",
        "description": "Repair cracked or broken Android phone screens, including Samsung devices. We inspect display damage and test touch response after replacement.",
        "min_price": "12000",
        "max_price": "35000",
        "technician": 1,
        "areas": ["Lekki", "Ajah"],
    },
    {
        "title": "Phone Charging Port Repair",
        "description": "Fix phones that will not charge, have loose charging ports, or connect to chargers intermittently. Charging performance is checked after repair.",
        "min_price": "5000",
        "max_price": "15000",
        "technician": 2,
        "areas": ["Ajah", "Victoria Island"],
    },
    {
        "title": "Phone Battery Replacement",
        "description": "Replace weak phone batteries that drain quickly, overheat during normal use, or cause unexpected shutdowns. Device charging is tested after replacement.",
        "min_price": "8000",
        "max_price": "25000",
        "technician": 1,
        "areas": ["Lekki", "Victoria Island"],
    },
    {
        "title": "Water-Damaged Phone Repair",
        "description": "Inspect phones exposed to water or other liquids. We assess corrosion and affected components before recommending suitable repairs.",
        "min_price": "10000",
        "max_price": "40000",
        "technician": 2,
        "areas": ["Ajah", "Lekki"],
    },
    {
        "title": "Phone Speaker and Microphone Repair",
        "description": "Diagnose phone audio problems, including speakers with no sound, muffled audio, and microphones that prevent people from hearing you during calls.",
        "min_price": "5000",
        "max_price": "18000",
        "technician": 1,
        "areas": ["Victoria Island", "Lekki"],
    },
    {
        "title": "Phone Camera Repair",
        "description": "Troubleshoot blurry photos, damaged rear or front cameras, focusing problems, and camera apps that fail to open. Camera functions are tested after repair.",
        "min_price": "8000",
        "max_price": "30000",
        "technician": 2,
        "areas": ["Ajah", "Victoria Island"],
    },
    {
        "title": "Phone Software and Boot Repair",
        "description": "Diagnose phones stuck on the startup logo, caught in a boot loop, or experiencing repeated software crashes. Data preservation depends on the device condition.",
        "min_price": "5000",
        "max_price": "20000",
        "technician": 1,
        "areas": ["Lekki", "Ajah"],
    },
    {
        "title": "Phone Network and Signal Repair",
        "description": "Troubleshoot phones with no mobile signal, SIM card detection errors, or persistent network connection problems. Hardware and software causes are assessed.",
        "min_price": "5000",
        "max_price": "18000",
        "technician": 2,
        "areas": ["Victoria Island", "Lekki"],
    },
    {
        "title": "Phone Power Button Repair",
        "description": "Fix unresponsive, stuck, or damaged phone power buttons that make it difficult to switch the device on, lock the screen, or restart it.",
        "min_price": "5000",
        "max_price": "15000",
        "technician": 1,
        "areas": ["Ajah", "Victoria Island"],
    },
    {
        "title": "iPhone Face ID and Sensor Repair",
        "description": "Diagnose iPhone Face ID failures and sensor problems that affect facial recognition or screen behavior during calls. Repair options depend on the fault.",
        "min_price": "10000",
        "max_price": "45000",
        "technician": 2,
        "areas": ["Lekki", "Victoria Island"],
    },
    {
        "title": "Phone Screen and Touch Repair",
        "description": "Diagnose touchscreens that do not respond, register ghost touches, or behave erratically. We assess the display and touch components before repair.",
        "min_price": "10000",
        "max_price": "35000",
        "technician": 1,
        "areas": ["Ajah", "Lekki", "Victoria Island"],
    },
]

created = 0
skipped = 0


for item in test_listings:
    existing_listing = ServiceListing.objects.filter(
        title=item["title"]
    ).first()

    if existing_listing:
        skipped += 1
        print(f"Skipped: {item['title']}")
        continue

    listing = ServiceListing(
        technician=technicians[item["technician"]],
        category=category,
        title=item["title"],
        description=item["description"],
        min_price=Decimal(item["min_price"]),
        max_price=Decimal(item["max_price"]),
    )

    listing.full_clean()
    listing.save()
    listing.service_areas.set(
        [areas[name] for name in item["areas"]]
    )

    created += 1
    print(f"Created: {listing.title}")

print(f"\nFinished: {created} created, {skipped} skipped.")
