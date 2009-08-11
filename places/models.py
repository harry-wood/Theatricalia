from django.db import models
from django.contrib.contenttypes import generic
from photos.models import Photo
from utils import int_to_base32, unique_slugify

class Place(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    address = models.CharField(blank=True, max_length=200)
    town = models.CharField(blank=True, max_length=50)
    postcode = models.CharField(blank=True, max_length=10)
    type = models.CharField(blank=True, max_length=100, choices=(('proscenium', 'Proscenium Arch'), ('thrust', 'Thrust'), ('multiple', 'Multiple'), ('other', 'Other')))
    size = models.CharField(blank=True, max_length=100)
    opening_date = models.DateField(blank=True, null=True)
    url = models.URLField('URL', blank=True)
    wikipedia = models.URLField(blank=True)
    photos = generic.GenericRelation(Photo)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        out = self.name
        if self.town: out += ", " + self.town
        return out

    def save(self):
        self.slug = unique_slugify(Place, '%s %s' % (self.name, self.town), self)
        super(Place, self).save()

    @models.permalink
    def get_absolute_url(self):
        return ('place', (), { 'place_id': int_to_base32(self.id), 'place': self.slug })

    @models.permalink
    def get_edit_url(self):
        return ('place-edit', (), { 'place_id': int_to_base32(self.id), 'place': self.slug })

    @models.permalink
    def get_add_production_url(self):
        return ('place-production-add', (), { 'place_id': int_to_base32(self.id), 'place': self.slug })

    def get_past_url(self):
        return '%s/past' % self.get_absolute_url()

    def get_future_url(self):
        return '%s/future' % self.get_absolute_url()

    def get_feed_url(self):
        return '%s/feed' % self.get_absolute_url()

def first_letters():
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('SELECT DISTINCT SUBSTRING(name, 1, 1) FROM places_place')
    return cursor.fetchall()

