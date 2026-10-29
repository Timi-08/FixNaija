from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ServiceListingForm, TechnicianProfileForm, TechnicianVerificationRequestForm
from .models import TechnicianProfile, ServiceListing, ServiceCategory, ServiceArea, TechnicianVerificationRequest
from django.db.models import Q, Case, When, Value, IntegerField
from .search_utils import extract_search_terms, normalize_query, find_related_phrases
from decimal import Decimal, InvalidOperation
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404

# Create your views here.

# Creating a technician profile
@login_required
def technician_setup(request):
    # Check if the user already has a technician profile
    technician = TechnicianProfile.objects.filter(
        user=request.user
    ).first()

    if technician:
        return redirect('technicians:my_services')

    if request.method == 'POST':
        form = TechnicianProfileForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            technician = form.save(commit=False)
            technician.user = request.user
            technician.save()

            return redirect('technicians:my_services')
    else:
        form = TechnicianProfileForm()

    return render(
        request,
        'technicians/technician_setup.html',
        {'form': form}
    )

# technician profile view
@login_required
def my_technician_profile(request):
    technician = get_object_or_404(
        TechnicianProfile.objects.select_related('user'),
        user=request.user
    )

    listings = technician.service_listings.filter(
        is_active=True,
        is_deleted=False
    ).select_related(
        'category'
    ).prefetch_related(
        'service_areas'
    )

    # Search by service title or description
    search_query = request.GET.get('q', '').strip()

    if search_query:
        listings = listings.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Filter by category
    category_id = request.GET.get('category', '')

    if category_id.isdigit():
        listings = listings.filter(category_id=category_id)
    else:
        category_id = ''

    categories = ServiceCategory.objects.filter(
        is_active=True,
        service_listings__technician=technician,
        service_listings__is_active=True,
        service_listings__is_deleted=False
    ).distinct()

    # Show 10 services per page
    paginator = Paginator(listings, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'technicians/my_technician_profile.html',
        {
            'technician': technician,
            'listings': page_obj,
            'page_obj': page_obj,
            'categories': categories,
            'search_query': search_query,
            'selected_category': category_id,
        }
    )

# editing technician profile
@login_required
def edit_technician_profile(request):
    technician = get_object_or_404(
        TechnicianProfile,
        user=request.user
    )

    if request.method == 'POST':
        form = TechnicianProfileForm(
            request.POST,
            request.FILES,
            instance=technician
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Your technician profile was updated successfully.'
            )
            return redirect('technicians:my_technician_profile')
    else:
        form = TechnicianProfileForm(instance=technician)

    return render(
        request,
        'technicians/edit_technician_profile.html',
        {'form': form, 'technician': technician}
    )

# Public technician profile
def technician_public_profile(request, username):
    technician = get_object_or_404(
        TechnicianProfile.objects.select_related('user'),
        user__username=username,
        user__is_active=True
    )

    listings = ServiceListing.objects.filter(
        technician=technician,
        is_active=True,
        is_deleted=False,
        category__is_active=True
    ).select_related(
        'category'
    ).prefetch_related(
        'service_areas'
    ).order_by('-created_at')

    # Show 10 services per page
    paginator = Paginator(listings, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'technicians/technician_public_profile.html',
        {
            'technician': technician,
            'listings': page_obj,
            'page_obj': page_obj,
        }
    )

# technician verification rquest
@login_required
def submit_verification_request(request):
    technician = TechnicianProfile.objects.filter(
        user=request.user
    ).first()

    if technician is None:
        messages.error(
            request,
            "You need a technician profile before requesting verification."
        )
        return redirect("technicians:technician_setup")

    if technician.is_verified:
        return render(
            request,
            "technicians/verification_request.html",
            {
                "technician": technician,
                "pending_request": None,
                "latest_request": None,
                "form": None,
                "already_verified": True,
            },
        )

    pending_request = TechnicianVerificationRequest.objects.filter(
        technician=technician,
        status=TechnicianVerificationRequest.Status.PENDING,
    ).first()

    if pending_request:
        return render(
            request,
            "technicians/verification_request.html",
            {
                "technician": technician,
                "pending_request": pending_request,
                "form": None,
            },
        )

    if request.method == "POST":
        form = TechnicianVerificationRequestForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            verification_request = form.save(commit=False)
            verification_request.technician = technician
            verification_request.status = (
                TechnicianVerificationRequest.Status.PENDING
            )
            verification_request.save()

            messages.success(
                request,
                "Your verification request has been submitted for review."
            )
            return redirect("technicians:submit_verification_request")
    else:
        form = TechnicianVerificationRequestForm()

    latest_request = TechnicianVerificationRequest.objects.filter(
        technician=technician
    ).order_by("-submitted_at").first()

    return render(
        request,
        "technicians/verification_request.html",
        {
            "technician": technician,
            "form": form,
            "pending_request": None,
            "latest_request": latest_request,
        },
    )

# viewing private verification document
@staff_member_required
def view_verification_document(request, request_id, document_type):
    verification_request = get_object_or_404(
        TechnicianVerificationRequest,
        pk=request_id,
    )

    if document_type == "identity":
        document = verification_request.identity_document
    elif document_type == "qualification":
        document = verification_request.qualification_document
    else:
        raise Http404("Document not found.")

    if not document:
        raise Http404("Document not found.")

    try:
        document.open("rb")
        response = FileResponse(document, as_attachment=False)
        response["X-Content-Type-Options"] = "nosniff"
        return response
    except (OSError, ValueError):
        raise Http404("Document could not be opened.")

# Creating a service (by a technician)
@login_required
def create_service_listing(request):
    technician = TechnicianProfile.objects.filter(
        user=request.user
    ).first()

    if not technician:
        return redirect('technicians:technician_setup')

    if request.method == 'POST':
        form = ServiceListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.technician = technician
            listing.save()
            form.save_m2m()
            return redirect('technicians:my_services')
    else:
        form = ServiceListingForm()

    return render(
        request,
        'technicians/create_service_listing.html',
        {'form': form}
    )

# list of services(available to all users)
def service_list(request):
    listings = ServiceListing.objects.filter(
        is_active=True,
        is_deleted=False,
        technician__user__is_active=True
    ).select_related('technician__user', 'category')

    categories = ServiceCategory.objects.filter(is_active=True)
    areas = ServiceArea.objects.filter(is_active=True)

    category_id = request.GET.get('category')
    area_id = request.GET.get('area')
    search_query = request.GET.get('q', '').strip()
    budget = request.GET.get('budget', '').strip()


    if category_id:
        listings = listings.filter(category_id=category_id)

    if area_id:
        listings = listings.filter(service_areas__id=area_id)


    if budget:
        try:
            budget = Decimal(budget)

            listings = listings.filter(
                Q(min_price__lte=budget) &
                (Q(max_price__gte=budget) | Q(max_price__isnull=True))
            )
        except (ValueError, InvalidOperation):
            budget = ''

    # search feature xoxoxoxoxoxoxoxoxoxoxoxoxoxoxo xoxoxoxoxoxoxoxoxoxoxoxoxo
   
    if search_query:
        normalized_query = normalize_query(search_query)
        search_terms = extract_search_terms(normalized_query)
        related_phrases = find_related_phrases(normalized_query)

        search_filter = Q()

        for term in search_terms:
            search_filter |= (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(category__name__icontains=term) |
                Q(technician__user__username__icontains=term) |
                Q(technician__professional_info__icontains=term) |
                Q(technician__base_location__icontains=term)
            )

        for phrase in related_phrases:
            search_filter |= (
                Q(title__icontains=phrase) |
                Q(description__icontains=phrase) |
                Q(category__name__icontains=phrase)
            )

        if search_terms or related_phrases:
            listings = listings.filter(search_filter)

            listings = listings.annotate(
                relevance=(
                    Case(
                        When(title__iexact=normalized_query, then=Value(100)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                    + Case(
                        When(title__icontains=normalized_query, then=Value(50)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                    + Case(
                        When(category__name__icontains=normalized_query, then=Value(30)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                )
            ).order_by('-relevance', 'title')
        else:
            listings = listings.none()


    # Paginate public service listings
    paginator = Paginator(listings.distinct(), 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'technicians/service_list.html',
        {
            'listings': page_obj,
            'page_obj': page_obj,
            'categories': categories,
            'areas': areas,
            'selected_category': category_id,
            'selected_area': area_id,
            'search_query': search_query,
            'selected_budget': budget,
        }
    )

# service detail page
def service_detail(request, service_id):
    listing = get_object_or_404(
        ServiceListing.objects.select_related(
            'technician__user',
            'category',
        ).prefetch_related('service_areas'),
        id=service_id,
        is_active=True,
        is_deleted=False,
        technician__user__is_active=True,
    )

    return render(
        request,
        'technicians/service_detail.html',
        {'listing': listing}
    )

# Managing user's services (by a technician)
@login_required
def my_services(request):
    technician = TechnicianProfile.objects.filter(
        user=request.user
    ).first()

    if not technician:
        return render(
            request,
            'technicians/my_services.html',
            {
                'listings': [],
                'needs_profile': True
            }
        )

    listings = ServiceListing.objects.filter(
        technician=technician,
        is_deleted=False
    ).select_related('category').order_by('-created_at')

    paginator = Paginator(listings, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'technicians/my_services.html',
        {
            'listings': page_obj,
            'page_obj': page_obj,
            'needs_profile': False
        }
    )

# editing a service
@login_required
def edit_service(request, service_id):
    technician = TechnicianProfile.objects.filter(user=request.user).first()

    if not technician:
        return redirect('technicians:technician_setup')

    listing = get_object_or_404(
        ServiceListing,
        id=service_id,
        technician=technician,
        is_deleted=False
    )

    if request.method == 'POST':
        form = ServiceListingForm(request.POST, instance=listing)

        if form.is_valid():
            form.save()
            return redirect('technicians:my_services')
    else:
        form = ServiceListingForm(instance=listing)

    return render(
        request,
        'technicians/edit_service.html',
        {'form': form, 'listing': listing}
    )

#  deleting a service
@login_required
def delete_service(request, service_id):
    technician = TechnicianProfile.objects.filter(user=request.user).first()

    if not technician:
        return redirect('technicians:technician_setup')

    listing = get_object_or_404(
        ServiceListing,
        id=service_id,
        technician=technician,
        is_deleted=False
    )

    if request.method == 'POST':
        listing.is_deleted = True
        listing.save()
        return redirect('technicians:my_services')

    return render(
        request,
        'technicians/delete_service.html',
        {'listing': listing}
    )

# Pause/Reactivate Service
@login_required
def toggle_service_status(request, service_id):
    if request.method != 'POST':
        return redirect('technicians:my_services')

    technician = TechnicianProfile.objects.filter(user=request.user).first()

    if not technician:
        return redirect('technicians:technician_setup')

    listing = get_object_or_404(
        ServiceListing,
        id=service_id,
        technician=technician,
        is_deleted=False
    )

    listing.is_active = not listing.is_active
    listing.save(update_fields=['is_active'])

    return redirect('technicians:my_services')
