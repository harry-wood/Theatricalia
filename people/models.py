from django.db import models
from utils import int_to_base32
from django.contrib.contenttypes import generic
from django.template.defaultfilters import slugify
from fields import ApproximateDateField
from photos.models import Photo
from sounds.metaphone import dm

class Person(models.Model):
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    first_name_metaphone = models.CharField(max_length=50, editable=False)
    first_name_metaphone_alt = models.CharField(max_length=50, editable=False)
    last_name_metaphone = models.CharField(max_length=50, editable=False)
    last_name_metaphone_alt = models.CharField(max_length=50, editable=False)
    slug = models.SlugField(max_length=100)
    bio = models.TextField(blank=True, verbose_name='Biography')
    dob = ApproximateDateField(blank=True, verbose_name='Date of birth')
    imdb = models.URLField(blank=True, verbose_name='IMDb URL')
    wikipedia = models.URLField(blank=True, verbose_name='Wikipedia URL')
    web = models.URLField(blank=True, verbose_name='Personal website')
    photos = generic.GenericRelation(Photo)

    def __unicode__(self):
        if self.first_name and self.last_name:
            return '%s %s' % (self.first_name, self.last_name)
        elif self.last_name:
            return self.last_name
        else:
            return u'Unknown'

    def name(self):
        return unicode(self)

    @models.permalink
    def get_absolute_url(self):
            return ('person', [int_to_base32(self.id), self.slug])

    @models.permalink
    def get_edit_url(self):
            return ('person-edit', [int_to_base32(self.id), self.slug])

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'people'

    def save(self, **kwargs):
        self.slug = slugify(self.name())
        first_name_metaphone = dm(self.first_name)
        last_name_metaphone = dm(self.last_name)
        self.first_name_metaphone = first_name_metaphone[0]
        self.first_name_metaphone_alt = first_name_metaphone[1] or ''
        self.last_name_metaphone = last_name_metaphone[0]
        self.last_name_metaphone_alt = last_name_metaphone[1] or ''
        super(Person, self).save(**kwargs)

def first_letters():
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('SELECT DISTINCT SUBSTRING(last_name, 1, 1) FROM people_person')
    return cursor.fetchall()

