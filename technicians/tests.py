from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .models import (
    TechnicianProfile,
    ServiceListing,
    ServiceCategory,
    ServiceArea,
)


class ServiceOwnershipTests(TestCase):
    def setUp(self):
        # Create two separate users
        self.owner = User.objects.create_user(
            username="technician_a",
            password="testpass123",
        )
        self.other_technician = User.objects.create_user(
            username="technician_b",
            password="testpass123",
        )

        # Give both users technician profiles
        self.owner_profile = TechnicianProfile.objects.create(
            user=self.owner,
            professional_info="Phone repair technician",
            base_location="Lekki",
        )
        self.other_profile = TechnicianProfile.objects.create(
            user=self.other_technician,
            professional_info="Laptop repair technician",
            base_location="Ikeja",
        )

        # Create a category and service area
        self.category = ServiceCategory.objects.create(
            name="Phone Repair",
            slug="phone-repair",
        )
        self.area = ServiceArea.objects.create(
            name="Lekki",
        )

        # Create a service owned by Technician A
        self.listing = ServiceListing.objects.create(
            technician=self.owner_profile,
            category=self.category,
            title="iPhone Screen Repair",
            description="Screen replacement and repair services.",
            min_price=5000,
        )
        self.listing.service_areas.add(self.area)

    def test_owner_can_access_edit_page(self):
        self.client.login(
            username="technician_a",
            password="testpass123",
        )

        response = self.client.get(
            reverse(
                "technicians:edit_service",
                args=[self.listing.id],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_other_technician_cannot_edit_service(self):
        self.client.login(
            username="technician_b",
            password="testpass123",
        )

        response = self.client.get(
            reverse(
                "technicians:edit_service",
                args=[self.listing.id],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_other_technician_cannot_delete_service(self):
        self.client.login(
            username="technician_b",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "technicians:delete_service",
                args=[self.listing.id],
            )
        )

        self.assertEqual(response.status_code, 404)
        self.listing.refresh_from_db()
        self.assertFalse(self.listing.is_deleted)

    def test_other_technician_cannot_toggle_service(self):
        self.client.login(
            username="technician_b",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "technicians:toggle_service_status",
                args=[self.listing.id],
            )
        )

        self.assertEqual(response.status_code, 404)
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)


    def test_anonymous_user_cannot_access_edit_page(self):
        response = self.client.get(
            reverse(
                "technicians:edit_service",
                args=[self.listing.id],
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_cannot_access_delete_page(self):
        response = self.client.get(
            reverse(
                "technicians:delete_service",
                args=[self.listing.id],
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_cannot_toggle_service(self):
        response = self.client.post(
            reverse(
                "technicians:toggle_service_status",
                args=[self.listing.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)
