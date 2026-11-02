from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from technicians.models import ServiceArea, ServiceCategory, ServiceListing, TechnicianProfile

from .models import Booking

User = get_user_model()
PW = "pw12345!pw"


def make_world():
    tech_user = User.objects.create_user("kudus", password=PW)
    customer = User.objects.create_user("bisi", password=PW)
    stranger = User.objects.create_user("stranger", password=PW)
    cat = ServiceCategory.objects.create(name="AC technician")
    area = ServiceArea.objects.create(name="Ajah")
    far = ServiceArea.objects.create(name="Ikeja")
    tech = TechnicianProfile.objects.create(
        user=tech_user, professional_info="AC pro", base_location="Ajah")
    service = ServiceListing.objects.create(
        technician=tech, category=cat, title="AC repair",
        description="Inspection and servicing for split units, all brands.",
        min_price=5000)
    service.service_areas.add(area)
    return tech_user, customer, stranger, tech, service, area, far


class BookingWorkflowTests(TestCase):
    def setUp(self):
        (self.tech_user, self.customer, self.stranger,
         self.tech, self.service, self.area, self.far) = make_world()
        self.booking = Booking.objects.create(
            customer=self.customer, technician=self.tech, service=self.service,
            area=self.area, address="12 Admiralty Way, Ajah")

    def test_starts_requested(self):
        self.assertEqual(self.booking.status, Booking.REQUESTED)

    def test_happy_path(self):
        for status in (Booking.ACCEPTED, Booking.IN_PROGRESS, Booking.COMPLETED):
            self.booking.change_status(status, self.tech_user)
        self.assertEqual(self.booking.status, Booking.COMPLETED)

    def test_reject(self):
        self.booking.change_status(Booking.REJECTED, self.tech_user)
        self.assertEqual(self.booking.status, Booking.REJECTED)

    def test_customer_cannot_accept(self):
        with self.assertRaises(ValidationError):
            self.booking.change_status(Booking.ACCEPTED, self.customer)

    def test_stranger_cannot_change(self):
        with self.assertRaises(ValidationError):
            self.booking.change_status(Booking.ACCEPTED, self.stranger)

    def test_cannot_skip_steps(self):
        for target in (Booking.COMPLETED, Booking.IN_PROGRESS):
            with self.assertRaises(ValidationError):
                self.booking.change_status(target, self.tech_user)

    def test_either_party_can_cancel_after_accept(self):
        self.booking.change_status(Booking.ACCEPTED, self.tech_user)
        self.booking.change_status(Booking.CANCELLED, self.customer)
        self.assertEqual(self.booking.status, Booking.CANCELLED)

    def test_cannot_cancel_while_only_requested(self):
        with self.assertRaises(ValidationError):
            self.booking.change_status(Booking.CANCELLED, self.customer)

    def test_final_states_are_final(self):
        self.booking.change_status(Booking.REJECTED, self.tech_user)
        with self.assertRaises(ValidationError):
            self.booking.change_status(Booking.ACCEPTED, self.tech_user)

    def test_cannot_book_yourself(self):
        b = Booking(customer=self.tech_user, technician=self.tech, service=self.service,
                    area=self.area, address="somewhere long enough")
        with self.assertRaises(ValidationError):
            b.full_clean()

    def test_area_must_be_offered_for_that_service(self):
        b = Booking(customer=self.customer, technician=self.tech, service=self.service,
                    area=self.far, address="somewhere long enough")
        with self.assertRaises(ValidationError):
            b.full_clean()


class BookingViewTests(TestCase):
    def setUp(self):
        (self.tech_user, self.customer, self.stranger,
         self.tech, self.service, self.area, self.far) = make_world()

    def book(self):
        return self.client.post(
            reverse("bookings:book", args=[self.service.pk]),
            {"area": self.area.pk, "address": "12 Admiralty Way, Ajah",
             "description": "AC broken"})

    def test_login_required(self):
        resp = self.client.get(reverse("bookings:book", args=[self.service.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_customer_can_book(self):
        self.client.login(username="bisi", password=PW)
        self.assertEqual(self.book().status_code, 302)
        self.assertEqual(Booking.objects.count(), 1)

    def test_technician_cannot_book_own_service(self):
        self.client.login(username="kudus", password=PW)
        self.book()
        self.assertEqual(Booking.objects.count(), 0)

    def test_paused_service_cannot_be_booked(self):
        self.service.is_active = False
        self.service.save()
        self.client.login(username="bisi", password=PW)
        self.assertEqual(self.book().status_code, 404)
        self.assertEqual(Booking.objects.count(), 0)

    def test_status_change_needs_post_and_right_person(self):
        self.client.login(username="bisi", password=PW)
        self.book()
        b = Booking.objects.get()
        url = reverse("bookings:change_status", args=[b.pk, "accepted"])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)  # customer is not allowed to accept
        b.refresh_from_db()
        self.assertEqual(b.status, Booking.REQUESTED)
        self.client.logout()
        self.client.login(username="kudus", password=PW)
        self.client.post(url)
        b.refresh_from_db()
        self.assertEqual(b.status, Booking.ACCEPTED)

    def test_stranger_cannot_open_booking(self):
        b = Booking.objects.create(customer=self.customer, technician=self.tech,
                                   service=self.service, area=self.area,
                                   address="12 Admiralty Way")
        self.client.login(username="stranger", password=PW)
        self.assertEqual(self.client.get(b.get_absolute_url()).status_code, 403)

    def test_incoming_requires_technician_profile(self):
        self.client.login(username="bisi", password=PW)
        resp = self.client.get(reverse("bookings:incoming"))
        self.assertEqual(resp.status_code, 302)
