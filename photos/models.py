from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from sorl.thumbnail import ImageField
from utils import int_to_base32

def get_upload_to(instance, filename):
    return 'photos/%s/%s/%s' % (instance.content_type, instance.object_id, filename)

class PhotoManager(models.Manager):
    def get_query_set(self):
        return super(PhotoManager, self).get_query_set().filter(is_visible=True)

class Photo(models.Model):
    is_visible = models.BooleanField(default=True)

    title = models.CharField(max_length=255)
    photo = ImageField('Photograph', upload_to = get_upload_to, max_length = 255)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = PhotoManager()

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('photo-view', (), { 'photo_id': int_to_base32(self.id) })

    def get_attached(self):
        return self.content_object

