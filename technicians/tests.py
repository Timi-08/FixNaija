from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import UserProfile

from .models import (
    TechnicianProfile,
    ServiceListing,
    ServiceCategory,
    ServiceArea,
)
from .location_data import LAGOS_LGAS


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
        )
        self.other_profile = TechnicianProfile.objects.create(
            user=self.other_technician,
            professional_info="Laptop repair technician",
        )

        # Create a category and service area
        self.category = ServiceCategory.objects.create(
            name="Phone Repair",
            slug="phone-repair",
        )
        self.area, _ = ServiceArea.objects.get_or_create(
            name="Lekki",
        )
        self.owner_profile.base_locations.add(self.area)
        self.other_profile.base_locations.add(
            ServiceArea.objects.get(name="Ikeja")
        )
        self.owner_profile.categories.add(self.category)
        self.other_profile.categories.add(self.category)

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


class TechnicianSetupFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="new_technician",
            email="tech@example.com",
            password="Strong-pass-583!",
        )
        self.category = ServiceCategory.objects.create(name="Plumbing")
        self.ajah, _ = ServiceArea.objects.get_or_create(name="Ajah")
        self.ikeja = ServiceArea.objects.get(name="Ikeja")
        self.client.force_login(self.user)
        self.setup_url = reverse("technicians:technician_setup")

    def setup_data(self, **overrides):
        data = {
            "phone": "+2348000000000",
            "categories": [str(self.category.pk)],
            "base_locations": [str(self.ajah.pk), str(self.ikeja.pk)],
            "professional_info": "Experienced plumbing repairs and installation.",
        }
        data.update(overrides)
        return data

    def test_setup_shows_account_details_and_two_step_guidance(self):
        response = self.client.get(self.setup_url)

        self.assertContains(response, "new_technician")
        self.assertContains(response, "tech@example.com")
        self.assertContains(response, "Step 1 of 2")
        self.assertContains(response, "Continue to step 2: add services")

    def test_edit_profile_uses_removable_multi_selects(self):
        technician = TechnicianProfile.objects.create(
            user=self.user,
            professional_info="Experienced plumbing repairs and installation.",
        )
        technician.categories.add(self.category)
        technician.base_locations.add(self.ajah, self.ikeja)

        response = self.client.get(
            reverse("technicians:edit_technician_profile")
        )

        self.assertContains(response, "id_categories")
        self.assertContains(response, "id_base_locations")
        self.assertContains(response, "tom-select.complete.min.js")
        self.assertContains(response, "plugins: ['remove_button']")
        self.assertContains(response, 'value="%s" selected' % self.category.pk)
        self.assertContains(response, 'value="%s" selected' % self.ajah.pk)
        self.assertContains(response, 'value="%s" selected' % self.ikeja.pk)

    def test_setup_saves_phone_category_and_multiple_locations(self):
        response = self.client.post(self.setup_url, self.setup_data())

        technician = TechnicianProfile.objects.get(user=self.user)
        self.assertRedirects(
            response,
            reverse("technicians:create_service_listing"),
        )
        self.assertEqual(self.user.profile.phone, "+2348000000000")
        self.assertEqual(list(technician.categories.all()), [self.category])
        self.assertEqual(
            set(technician.base_locations.values_list("pk", flat=True)),
            {self.ajah.pk, self.ikeja.pk},
        )

    def test_setup_requires_phone(self):
        response = self.client.post(self.setup_url, self.setup_data(phone=""))

        self.assertEqual(
            response.context["form"].errors["phone"],
            ["This field is required."],
        )
        self.assertFalse(TechnicianProfile.objects.filter(user=self.user).exists())

    def test_lagos_lgas_are_available_once(self):
        areas = list(
            ServiceArea.objects.filter(name__in=LAGOS_LGAS)
            .values_list("name", flat=True)
        )

        self.assertEqual(set(areas), set(LAGOS_LGAS))
        self.assertEqual(len(areas), len(set(areas)))


class TechnicianAdminNavigationTests(TestCase):
    def test_technician_admin_page_shows_related_records_together(self):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Strong-pass-583!",
        )
        technician = TechnicianProfile.objects.create(
            user=User.objects.create_user(
                username="tech",
                email="tech@example.com",
                password="Strong-pass-583!",
            ),
            professional_info="Plumbing and repair services.",
        )
        category = ServiceCategory.objects.create(name="Plumbing")
        technician.categories.add(category)
        service = ServiceListing.objects.create(
            technician=technician,
            category=category,
            title="Pipe repair",
            description="Repair leaking pipes, taps and water lines.",
            min_price=5000,
        )
        service.service_areas.add(ServiceArea.objects.get(name="Ikeja"))
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "admin:technicians_technicianprofile_change",
                args=[technician.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pipe repair")
