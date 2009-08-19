import re # , difflib
import urllib
from django.utils import simplejson
from django.db.models import Q
from shortcuts import render
from people.models import Person
from places.models import Place
from plays.models import Play
from sounds.metaphone import dm
from sounds.jarowpy import jarow
#from levenshtein import damerau, qnum

distance = jarow
threshold = 0.8

def search_people(search, force_similar=False, use_distance=True):
    sounds_people = 0
    names = search.split(None, 3)
    if len(names)==1:
        if force_similar:
            people = Person.objects.exclude(first_name__icontains=names[0]).exclude(last_name__iexact=names[0])
        else:
            people = Person.objects.filter(Q(first_name__icontains=names[0]) | Q(last_name__iexact=names[0]))
            print people
        if force_similar:
            sounds_people = 2
            dm_, dm_alt = dm(names[0])
            people = people.filter(
                Q(first_name_metaphone=dm_) | Q(last_name_metaphone=dm_)
            )
        elif not people:
            sounds_people = 1
            dm_, dm_alt = dm(names[0])
            people = Person.objects.filter(
                Q(first_name_metaphone=dm_) | Q(last_name_metaphone=dm_)
                #Q(first_name_metaphone=dm_alt) | #Q(first_name_metaphone_alt=dm_) |
                #Q(last_name_metaphone_alt=dm_) | #Q(last_name_metaphone=dm_alt)
            )
        #if not people:
        #    allnames = []
        #    for p in Person.objects.all():
        #        allnames.extend((p.first_name, p.last_name))
        #    people = difflib.get_close_matches(names[0], allnames)
        #    people = Person.objects.filter(Q(first_name__in=people) | Q(last_name__in=people))
        if not people and use_distance:
            people = []
            for p in Person.objects.all():
                sim = distance(names[0].lower(), p.first_name.lower())
                sim2 = distance(names[0].lower(), p.last_name.lower())
                if sim >= threshold or sim2 >= threshold:
                    people.append((1-max(sim, sim2), p))
            people.sort()
            people = [ person for _, person in people ]
    elif len(names)==2:
        people = Person.objects.filter(first_name__icontains=names[0], last_name__iexact=names[1])
        if not people or force_similar:
            sounds_people = 1
            dm_first, dm_first_alt = dm(names[0])
            dm_last, dm_last_alt = dm(names[1])
            people = Person.objects.filter(
                # First name homophone, Last name match
                Q(first_name_metaphone=dm_first,     last_name__iexact=names[1]) |
                Q(first_name_metaphone=dm_first_alt, last_name__iexact=names[1]) |
                Q(first_name_metaphone_alt=dm_first, last_name__iexact=names[1]) |
                # First name match, last name homophone
                Q(first_name__icontains=names[0],    last_name_metaphone=dm_last) |
                Q(first_name__icontains=names[0],    last_name_metaphone_alt=dm_last) |
                Q(first_name__icontains=names[0],    last_name_metaphone=dm_last_alt) |
                # Both names homophones
                Q(first_name_metaphone=dm_first, last_name_metaphone=dm_last) |
                Q(first_name_metaphone=dm_first, last_name_metaphone_alt=dm_last) |
                Q(first_name_metaphone=dm_first, last_name_metaphone=dm_last_alt) |
                Q(first_name_metaphone=dm_first_alt, last_name_metaphone=dm_last) |
                Q(first_name_metaphone=dm_first_alt, last_name_metaphone_alt=dm_last) |
                Q(first_name_metaphone=dm_first_alt, last_name_metaphone=dm_last_alt) |
                Q(first_name_metaphone_alt=dm_first, last_name_metaphone=dm_last) |
                Q(first_name_metaphone_alt=dm_first, last_name_metaphone_alt=dm_last) |
                Q(first_name_metaphone_alt=dm_first, last_name_metaphone=dm_last_alt)
            )
        if not people and use_distance:
            people = []
            people2 = []
            people3 = []
            for p in Person.objects.all():
                sim = distance(names[0].lower(), p.first_name.lower())
                sim2 = distance(names[1].lower(), p.last_name.lower())
                simB = distance(' '.join(names).lower(), ('%s %s' % (p.first_name, p.last_name)).lower())
                if names[1].lower() == p.last_name.lower() and sim >= threshold:
                    people.append((1-sim, p))
                elif re.search(names[0], p.first_name, re.I) and sim2 >= threshold:
                    people2.append((1-sim2, p))
                elif simB >= threshold:
                    people3.append((1-simB, p))
                elif sim >= threshold and sim2 >= threshold:
                    people3.append((1-max(sim, sim2), p))
            people.sort()
            people2.sort()
            people3.sort()
            people = people + people2 + people3
            people = [ person for _, person in people ]
    elif len(names)==3:
        people = Person.objects.filter(
            Q(first_name__icontains=' '.join(names[0:2]), last_name__iexact=names[2]) |
            Q(first_name__icontains=names[0], last_name__iexact=' '.join(names[1:3]))
        )
    return people, sounds_people

def search_near(s):
    r = urllib.urlopen('http://ws.geonames.org/searchJSON?isNameRequired=true&style=LONG&q=' + s + '&maxRows=10').read()
    r = simplejson.loads(r)
    return r

def search(request):
    search = request.GET.get('q', '')
    people = plays = places = near = []
    sounds_people = 0
    if search:
        people, sounds_people = search_people(search, force_similar=request.GET.get('similar'), use_distance=False)
        near = search_near(search)
        places = Place.objects.filter(Q(name__icontains=search) | Q(town__icontains=search))
        plays = Play.objects.filter(title__icontains=search)
        # Search for characters

    return render(request, 'search.html', {
        'people': people,
        'plays': plays,
        'places': places,
        'near': near,
        'sounds_people': sounds_people,
        'search': search,
    })
