from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase


class AdminNavigationTests(TestCase):
    def test_service_catalog_is_separate_from_technicians_and_auth(self):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Strong-pass-583!",
        )
        request = RequestFactory().get("/admin/")
        request.user = user

        apps = admin.site.get_app_list(request)
        apps_by_label = {app["app_label"]: app for app in apps}
        catalog_models = {
            model["object_name"]
            for model in apps_by_label["core"]["models"]
        }
        technician_models = {
            model["object_name"]
            for model in apps_by_label["technicians"]["models"]
        }

        self.assertEqual(apps_by_label["core"]["name"], "Service catalog")
        self.assertEqual(
            catalog_models,
            {"ServiceArea", "ServiceCategory", "ServiceListing"},
        )
        self.assertEqual(
            technician_models,
            {"TechnicianProfile", "TechnicianVerificationRequest"},
        )
        self.assertIn("accounts", apps_by_label)
        self.assertIn("auth", apps_by_label)
