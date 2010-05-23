import re
import urllib

from django.core import serializers
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory, inlineformset_factory
from django.db import IntegrityError
from django.contrib.comments.views.comments import post_comment
from django.http import Http404, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.utils import simplejson
from django.conf import settings

from reversion.models import Version
from utils import base32_to_int
from shortcuts import render, check_url, UnmatchingSlugException
from models import Production, Part, Place as ProductionPlace, Visit, ProductionCompany
from forms import ProductionForm, ProductionFormNoJS, PartForm, PlaceForm, PlaceFormNoJS, ProductionCompanyForm
from common.models import Alert
from plays.models import Play
from places.models import Place
from photos.forms import PhotoForm
from people.models import Person
from objshow import productions_list, productions_for

def check_parameters(play_id, play, production_id):
    production = check_url(Production, production_id)
    try:
        play = check_url(Play, play_id, play)
    except UnmatchingSlugException, e:
        raise UnmatchingSlugException(production)
    if play != production.play:
        raise Http404()
    return production

def production_short_url(request, production_id):
    try:
        production = check_url(Production, production_id)
    except UnmatchingSlugException, e:
        production = e.args[0]
    return HttpResponsePermanentRedirect(production.get_absolute_url())

def production_company_short_url(request, company_id):
    try:
        company = check_url(ProductionCompany, company_id)
    except UnmatchingSlugException, e:
        company = e.args[0]
    return HttpResponsePermanentRedirect(company.get_absolute_url())

def production_corrected(request, play_id, play, production_id):
    return production(request, play_id, play, production_id, okay=True)

def production(request, play_id, play, production_id, okay=False):
    try:
        production = check_parameters(play_id, play, production_id)
    except UnmatchingSlugException, e:
        return HttpResponsePermanentRedirect(e.args[0].get_absolute_url())
    photo_form = PhotoForm(production)
#    production_form = ProductionForm(instance=production)
#
#    ProductionPlaceFormSet = inlineformset_factory( Production, ProductionPlace, extra=1, form=PlaceForm )
#    formset = ProductionPlaceFormSet(
#        data = request.POST or None,
#        prefix = 'place',
#        instance = production,
#    )

    try:
        fp = open(settings.OUR_ROOT + '/data/flickr/production/' + production_id)
        flickr = fp.read()
        fp.close()
        flickr = simplejson.loads(flickr)
    except:
        flickr = ''

    try:
        seen = production.visit_set.get(user=request.user)
    except:
        seen = None

    if production.source_type() == 'Birmingham Libraries' and not okay:
        # Have to use revisions, magic number, to show what it was at the start...
        # Sorting has to be done yucky, as it's all serialized. Lucky there won't be many objects to a page ever hopefully!
        def fetch_from_history(q):
            changes = Version.objects.exclude(revision=19230).filter(object_id__in=q).count()
            originals = Version.objects.filter(revision=19230, object_id__in=q)
            parts = []
            for o in originals:
                for object in serializers.deserialize('xml', o.serialized_data):
                    part = object.object
                    parts.append( (part.start_date, part.order, part.role, part.person.last_name, part.person.first_name, part) )
            parts.sort()
            parts = [ p[5] for p in parts ]
            return parts, changes
        cast, c1 = fetch_from_history( production.part_set.filter(cast=True) )
        crew, c2 = fetch_from_history( production.part_set.filter(cast=False) )
        other, c3 = fetch_from_history( production.part_set.filter(cast__isnull=True) )
        initial_only = True
        changes = c1 or c2 or c3
    else:
        cast = production.part_set.filter(cast=True).order_by('start_date', 'order', 'role', 'person__last_name', 'person__first_name')
        crew = production.part_set.filter(cast=False).order_by('start_date', 'order', 'role', 'person__last_name', 'person__first_name')
        other = production.part_set.filter(cast__isnull=True).order_by('start_date', 'order', 'role', 'person__last_name', 'person__first_name')
        initial_only = False
        changes = False
        
    return render(request, 'production.html', {
        'production': production,
        'places': production.place_set.order_by('start_date', 'press_date'),
#        'production_form': production_form,
#        'production_formset': formset,
        'cast': cast,
        'crew': crew,
        'other': other,
        'photo_form': photo_form,
        'seen': seen,
        'flickr': flickr,
        'initial_only': initial_only,
        'changes': changes,
    })

@login_required
def production_seen(request, play_id, play, production_id, type):
    production = check_parameters(play_id, play, production_id)
    if type == 'add':
        alert = Visit(user=request.user, production=production)
        try:
            alert.save()
        except IntegrityError, e:
            if e.args[0] != 1062: # Duplicate
                raise
        request.user.message_set.create(message=u"Your visit has been recorded.")
    elif type == 'remove':
        Visit.objects.get(user=request.user, production=production).delete()
        request.user.message_set.create(message=u"Your visit has been removed.")

    return HttpResponseRedirect(production.get_absolute_url())


def company(request, company_id, company):
    try:
        company = check_url(ProductionCompany, company_id, company)
    except UnmatchingSlugException, e:
        return HttpResponsePermanentRedirect(e.args[0].get_absolute_url())

    alert = company.alerts.filter(user=request.user)
    past, future = productions_for(company)
    return render(request, 'productions/company.html', {
        'company': company,
        'past': past,
        'future': future,
        'alert': alert,
    })

def company_productions(request, company_id, company, type):
    try:
        company = check_url(ProductionCompany, company_id, company)
    except UnmatchingSlugException, e:
        return HttpResponsePermanentRedirect(e.args[0].get_absolute_url())
    return productions_list(request, company, type, 'productions/company_production_list.html')

@login_required
def company_edit(request, company_id, company):
    try:
        company = check_url(ProductionCompany, company_id, company)
    except UnmatchingSlugException, e:
        return HttpResponsePermanentRedirect(e.args[0].get_absolute_url())

    form = ProductionCompanyForm(request.POST or None, instance=company)
    if request.method == 'POST':
        if request.POST.get('disregard'):
            request.user.message_set.create(message=u"All right, we\u2019ve ignored any changes you made.")
            return HttpResponseRedirect(company.get_absolute_url())
        if form.is_valid():
            form.save()
            request.user.message_set.create(message="Your changes have been stored; thank you.")
            return HttpResponseRedirect(company.get_absolute_url())

    return render(request, 'productions/company_edit.html', {
        'company': company,
        'form': form,
    })

@login_required
def company_alert(request, company_id, company, type):
    try:
        company = check_url(ProductionCompany, company_id, company)
    except UnmatchingSlugException, e:
        return HttpResponsePermanentRedirect(e.args[0].get_absolute_url())

    if type == 'add':
        alert = Alert(user=request.user, content_object=company)
        try:
            alert.save()
        except IntegrityError, e:
            if e.args[0] != 1062: # Duplicate
                raise
        request.user.message_set.create(message=u"Your alert has been added.")
    elif type == 'remove':
        company.alerts.filter(user=request.user).delete()
        request.user.message_set.create(message=u"Your alert has been removed.")

    return HttpResponseRedirect(company.get_absolute_url())

@login_required
def part_edit(request, play_id, play, production_id, part_id):
    production = check_parameters(play_id, play, production_id)

    part = get_object_or_404(Part, id=part_id)
    if part.production != production:
        raise Http404()

    part_form = PartForm(
        data = request.POST or None,
        editing = True,
        instance = part,
        initial = { 'person': part.person } # To make form have name rather than ID
    )

    if request.method == 'POST':
        if request.POST.get('disregard'):
            request.user.message_set.create(message=u"All right, we\u2019ve ignored any changes you made.")
            return HttpResponseRedirect(production.get_edit_cast_url())
        if part_form.is_valid():
            if part_form.cleaned_data.get('person_choice') == 'new':
                part_form.cleaned_data['person'] = Person.objects.create_from_name(part_form.cleaned_data['person'])
            part_form.save()
            request.user.message_set.create(message="Your changes have been stored; thank you.")
            return HttpResponseRedirect(production.get_edit_cast_url())

    return render(request, 'productions/edit-part.html', {
        'id': part_id,
        'form': part_form,
        'production': production,
        'places': production.place_set.order_by('start_date', 'press_date'),
    })

@login_required
def production_edit(request, play_id, play, production_id):
    try:
        production = check_parameters(play_id, play, production_id)
    except UnmatchingSlugException, e:
        return HttpResponsePermanentRedirect(e.args[0].get_edit_url())

    if request.GET.get('js', '1')=='1':
        production_form = ProductionForm
        place_form = PlaceForm
    else:
        production_form = ProductionFormNoJS
        place_form = PlaceFormNoJS

    production_form = production_form(data=request.POST or None, instance=production)

    ProductionPlaceFormSet = inlineformset_factory( Production, ProductionPlace, extra=1, form=place_form )
    formset = ProductionPlaceFormSet(
        data = request.POST or None,
        prefix = 'place',
        instance = production,
    )

    if request.method == 'POST':
        if request.POST.get('disregard'):
            request.user.message_set.create(message=u"All right, we\u2019ve ignored any changes you made.")
            return HttpResponseRedirect(production.get_absolute_url())
        if production_form.is_valid() and formset.is_valid():
            production_form.save()
            formset.save()
            request.user.message_set.create(message="Your changes have been stored; thank you.")
            return HttpResponseRedirect(production.get_absolute_url())

    return render(request, 'productions/edit.html', {
        'form': production_form,
        'formset': formset,
        'production': production,
        'places': production.place_set.order_by('start_date', 'press_date'),
    })

@login_required
def production_edit_cast(request, play_id, play, production_id):
    """For picking someone to edit, or adding a new Part"""
    try:
        production = check_parameters(play_id, play, production_id)
    except UnmatchingSlugException, e:
        return HttpResponsePermanentRedirect(e.args[0].get_edit_cast_url())
    initial = {}
    if request.GET.get('person'):
        initial['person'] = Person.objects.get(id=base32_to_int(request.GET.get('person')))
    part_form = PartForm(data=request.POST or None, editing=False, initial=initial)

    if request.method == 'POST':
        if part_form.is_valid():
            if part_form.cleaned_data.get('person_choice') == 'new':
                part_form.cleaned_data['person'] = Person.objects.create_from_name(part_form.cleaned_data['person'])
            part_form.cleaned_data['production'] = production
            part_form.save()
            request.user.message_set.create(message="Your new part has been added; thank you.")
            return HttpResponseRedirect(production.get_edit_cast_url())

    return render(request, 'productions/edit-parts.html', {
        'production': production,
        'places': production.place_set.order_by('start_date', 'press_date'),
        'form': part_form,
        'parts': production.part_set.order_by('-cast', 'order', 'role', 'person__last_name', 'person__first_name'),
    })

@login_required
def production_add(request, play=None, place=None, company=None):

    initial = {}
    if play: initial['play'] = play.id
    if company: initial['company'] = company.id

    if request.GET.get('js', '1')=='1':
        production_form = ProductionForm
        place_form = PlaceForm
    else:
        production_form = ProductionFormNoJS
        place_form = PlaceFormNoJS

    production_form = production_form(data=request.POST or None, initial=initial)

    ProductionPlaceFormSet = modelformset_factory( ProductionPlace, form=place_form )
    formset = ProductionPlaceFormSet(
        data = request.POST or None,
        prefix = 'place',
        queryset = ProductionPlace.objects.none()
    )

    # Yucky, but no way to pass initial to a model formset XXX
    if place:
        formset.forms[0].initial['place'] = place.id

    if request.method == 'POST':
        if request.POST.get('disregard'):
            request.user.message_set.create(message=u"All right, we\u2019ve ignored what you had done.")
            if play: return HttpResponseRedirect(play.get_absolute_url())
            if company: return HttpResponseRedirect(company.get_absolute_url())
            if place: return HttpResponseRedirect(place.get_absolute_url())
        if production_form.is_valid() and formset.is_valid():
            production = production_form.save()
            for form in formset.forms:
                form.cleaned_data['production'] = production
            formset.save()
            request.user.message_set.create(message="Your addition has been stored; thank you. If you know members of the cast or crew, please feel free to add them now.")
            url = production.get_edit_cast_url()
            if request.POST.get('initial_person'):
                url += '?person=' + request.POST.get('initial_person')
            return HttpResponseRedirect(url)

    return render(request, 'productions/add.html', {
        'place': place,
        'formset': formset,
        'play': play,
        'company': company,
        'form': production_form,
    })

@login_required
def add_from_play(request, play_id, play):
    try:
        play = check_url(Play, play_id, play)
    except UnmatchingSlugException, e:
        return HttpResponsePermanentRedirect(e.args[0].get_absolute_url())
    return production_add(request, play=play)

@login_required
def add_from_place(request, place_id, place):
    place = check_url(Place, place_id, place)
    return production_add(request, place=place)

@login_required
def add_from_company(request, company_id, company):
    company = check_url(ProductionCompany, company_id, company)
    return production_add(request, company=company)

def post_comment_wrapper(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/tickets')
    return post_comment(request)
