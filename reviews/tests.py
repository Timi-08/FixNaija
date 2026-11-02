from django.test import TestCase
from django.urls import reverse

from bookings.models import Booking
from bookings.tests import PW, make_world

from .models import Review


class ReviewRuleTests(TestCase):
    def setUp(self):
        (self.tech_user, self.customer, self.stranger,
         self.tech, self.service, self.area, self.far) = make_world()
        self.booking = Booking.objects.create(
            customer=self.customer, technician=self.tech, service=self.service,
            area=self.area, address="12 Admiralty Way, Ajah")

    def post(self, rating=5):
        return self.client.post(reverse("reviews:leave", args=[self.booking.pk]),
                                {"rating": rating, "comment": "Great work"})

    def complete(self):
        self.booking.status = Booking.COMPLETED
        self.booking.save()

    def test_cannot_review_before_completion(self):
        self.client.login(username="bisi", password=PW)
        self.post()
        self.assertEqual(Review.objects.count(), 0)

    def test_review_once_after_completion(self):
        self.complete()
        self.client.login(username="bisi", password=PW)
        self.post(4)
        self.post(1)
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().rating, 4)

    def test_only_the_customer_can_review(self):
        self.complete()
        for name in ("kudus", "stranger"):
            self.client.login(username=name, password=PW)
            self.assertEqual(self.post().status_code, 403)
        self.assertEqual(Review.objects.count(), 0)

    def test_rating_must_be_1_to_5(self):
        self.complete()
        self.client.login(username="bisi", password=PW)
        self.post(9)
        self.assertEqual(Review.objects.count(), 0)
