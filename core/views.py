from django.shortcuts import render

from technicians.models import ServiceArea, ServiceCategory


def home(request):
    return render(
        request,
        "core/index.html",
        {
            "categories": ServiceCategory.objects.filter(is_active=True),
            "areas": ServiceArea.objects.filter(is_active=True),
        },
    )
