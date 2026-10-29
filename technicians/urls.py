
from django.urls import path
from . import views


app_name = "technicians"

urlpatterns = [

    # creating a service(technician only)
    path(
        "services/create/",
        views.create_service_listing,
        name="create_service_listing",
    ),

    # editing a service(technician only)
    path(
    "services/<int:service_id>/edit/",
    views.edit_service,
    name="edit_service"
    ),  

    # deleting a service(technician only)
    path(
        "services/<int:service_id>/delete/",
        views.delete_service,
        name="delete_service"
    ),

    # pausing a service(technician only)
    path(
        "services/<int:service_id>/toggle-status/",
        views.toggle_service_status,
        name="toggle_service_status"
    ),

    # service detail(public)
    path(
    "services/<int:service_id>/",
    views.service_detail,
    name="service_detail",
    ),

    # list of all active services(public)
    path(
        "services/",
        views.service_list,
        name="service_list",
    ),
    # list of all user's services(technician only)
    path(
        "my-services/",
        views.my_services,
        name="my_services",
    ),

    # creating a technician profile
    path(
        "technician-setup/",
        views.technician_setup,
        name="technician_setup",
    ),

    # viewing  your technician profile(technician only) 
    path(
    "my-technician-profile/",
    views.my_technician_profile,
    name="my_technician_profile",
    ),

    # editing  your technician profile(technician only) 
    path(
    "my-technician-profile/edit/",
    views.edit_technician_profile,
    name="edit_technician_profile",
    ),
    
    path(
        "technician/<str:username>/",
        views.technician_public_profile,
        name="technician_public_profile",
    ),

]
