from django.db import models
from technicians.models import (
    ServiceArea as TechnicianServiceArea,
    ServiceCategory as TechnicianServiceCategory,
    ServiceListing as TechnicianServiceListing,
)


class ServiceArea(TechnicianServiceArea):
    class Meta:
        proxy = True
        verbose_name = 'service area'
        verbose_name_plural = 'service areas'


class ServiceCategory(TechnicianServiceCategory):
    class Meta:
        proxy = True
        verbose_name = 'service category'
        verbose_name_plural = 'service categories'


class ServiceListing(TechnicianServiceListing):
    class Meta:
        proxy = True
        verbose_name = 'service listing'
        verbose_name_plural = 'service listings'
