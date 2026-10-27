from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# Create your models here.
# Categories under which services fall
class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True, help_text="URL slugs are created automatically, but you can add a custom one")
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "service categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# Technician profile of the user connected to the main user account(model)
class TechnicianProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    professional_info = models.TextField()
    base_location = models.CharField(max_length=100)
    profile_picture = models.ImageField(
        upload_to="technician_profiles/",
        null=True,
        blank=True
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - Technician"

# Area which services can be delivered
class ServiceArea(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name    

# Details of a service
class ServiceListing(models.Model):
    technician = models.ForeignKey(
        TechnicianProfile,
        on_delete=models.CASCADE,
        related_name="service_listings"
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="service_listings"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=1000)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    service_areas = models.ManyToManyField(
        ServiceArea,
        related_name="service_listings"
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if (
            self.max_price is not None
            and self.max_price < self.min_price
        ):
            raise ValidationError({
                "max_price": "Maximum price cannot be lower than minimum price."
            })

        if not self.description or len(self.description.strip()) < 30:
            raise ValidationError({
                "description": "Description must contain at least 30 characters."
            })

        if len(self.description) > 1000:
            raise ValidationError({
                "description": "Description cannot exceed 1,000 characters."
            })

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title