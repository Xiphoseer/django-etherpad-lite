import string
import random
import urllib

from django.db import models
from django.db.models.signals import pre_delete
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from mptt.models import MPTTModel, TreeForeignKey

from py_etherpad import EtherpadLiteClient

from .backend.etherpadlite import EtherpadLiteBackend
from .backend.hackmd import HackMDBackend


class PadServer(models.Model):
    """Schema and methods for etherpad-lite servers
    """
    title = models.CharField(max_length=256)
    url = models.URLField(
        max_length=256,
        verbose_name=_('URL'),
        help_text="must have trailing /"
    )
    apikey = models.CharField(max_length=256, verbose_name=_('API key'))
    notes = models.TextField(_('description'), blank=True)

    ETHERPADLITE = 'EPL'
    DJANGOPAD = 'DJP'
    HACKMD = 'HMD'

    BACKEND_CHOICES = (
        (ETHERPADLITE, 'EtherpadLite'),
        (DJANGOPAD, 'DjangoPad'),
        (HACKMD, 'HackMD'),
    )

    backend = models.CharField(max_length=3, choices=BACKEND_CHOICES, verbose_name=_('backend'), default=DJANGOPAD)

    class Meta:
        verbose_name = _('server')
        verbose_name_plural = _('servers')

    def __str__(self):
        return self.title

    def backend_name(self):
        return [b for a,b in PadServer.BACKEND_CHOICES if a == self.backend][0]

    @property
    def client(self):
        if self.backend == PadServer.ETHERPADLITE:
            return EtherpadLiteBackend(self.apikey, self.url)
        elif self.backend == PadServer.HACKMD:
            return HackMDBackend(self.apikey, self.url)
        else:
            return BaseBackend()


class PadCategory(MPTTModel):
    """Nested hierarchie for pad groups
    """
    name = models.CharField(max_length=256)
    parent = TreeForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    slug = models.SlugField(null=True, unique=True)
    show_non_leaf = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')


class PadGroup(models.Model):
    """Schema and methods for etherpad-lite groups
    """
    group_mapper = models.SlugField(max_length=256)

    groupID = models.CharField(max_length=256, null=True, blank=True)
    server = models.ForeignKey(PadServer, on_delete=models.CASCADE)

    name = models.CharField(max_length=256, null=True, blank=True)
    parent = models.ForeignKey(PadCategory, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        unique_together = (
            ('group_mapper', 'server'),
        )

    def __str__(self):
        return self.title

    @property
    def title(self):
        return "{0} - {1}".format(self.name if self.name else self.parent.name, self.server.title)

    @property
    def top_category(self):
        cat = self.parent
        while cat and cat.parent:
            cat = cat.parent
        return cat

    @property
    def full_path(self):
        path = [self.title]
        cat = self.parent
        while cat:
            path = [cat.name] + path
            cat = cat.parent
        return path

    @property
    def authors(self):
        groups = self.parent.groups.all()
        users = get_user_model().objects.filter(groups__in=groups)
        return PadAuthor.objects.all().filter(server=self.server, user__in=users);

    def _create(self):
        self.groupID = self.server.client.get_or_create_group(self.group_mapper)

    def _destroy(self):
        # First find and delete all associated pads
        Pad.objects.filter(group=self).delete()
        return self.server.client.delete_group(self.groupID)

    def save(self, *args, **kwargs):
        if not self.pk:
            self._create()
        super().save(*args, **kwargs)

    def unknown_pads(self):
        try:
            return self.server.client.list_group_pads(self.groupID)
        except:
            return []


def padGroupDel(sender, **kwargs):
    """Make sure groups are purged from etherpad when deleted
    """
    grp = kwargs['instance']
    grp._destroy()

pre_delete.connect(padGroupDel, sender=PadGroup)


def groupDel(sender, **kwargs):
    """Make sure our groups are destroyed properly when auth groups are deleted
    """
    grp = kwargs['instance']
    # Make shure auth groups without a pad group can be deleted, too.
    try:
        padGrp = PadGroup.objects.get(group=grp)
        padGrp._destroy()
    except Exception:
        pass

pre_delete.connect(groupDel, sender=Group)


class PadAuthorManager(models.Manager):

    def current(self, server, user):
        if user.is_authenticated:
            author, created = self.get_or_create(user=user, server=server)
            return author
        else:
            return None


class PadAuthor(models.Model):
    """Schema and methods for etherpad-lite authors
    """
    objects = PadAuthorManager()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    authorID = models.CharField(max_length=256, blank=True)
    server = models.ForeignKey(PadServer, models.CASCADE)

    class Meta:
        verbose_name = _('author')
        verbose_name_plural = _('authors')

    def __str__(self):
        return str(self.user)

    def _create(self):
        self.authorID = self.server.client.create_user(str(self.user.id), name=str(self))

    @property
    def groups(self):
        return PadGroup.objects.filter(server=self.server, parent__groups__in=self.user.groups.all())

    def save(self, *args, **kwargs):
        if not self.pk:
            self._create()
        super().save(*args, **kwargs)


class PadManager(models.Manager):

    def templates(self, category):
        """Given a category, returns all templates for that category
        """
        return self.filter(group__parent=category, is_template=True)

class Pad(models.Model):
    """Schema and methods for etherpad-lite pads
    """

    # Custom manager
    objects = PadManager()

    # The name of the pad
    name = models.CharField(max_length=256)

    # The server for this pad
    server = models.ForeignKey(PadServer, on_delete=models.CASCADE)

    # The group that has access to this pad
    group = models.ForeignKey(PadGroup, on_delete=models.PROTECT)

    # The padid, which is only set after the pad was created on the server
    padid = models.CharField(max_length=256, null=True, blank=True)

    # An optional password
    password = models.CharField(max_length=100, null=True, blank=True)

    # An optional shortlink
    slug = models.CharField(max_length=100, null=True, blank=True, unique=True)

    # Whether the pad is public
    is_public = models.BooleanField(default=False)

    # Whether this pad is a template
    is_template = models.BooleanField(default=False)

    # Template Settings
    template_is_public = models.BooleanField(default=False)
    template_password = models.CharField(max_length=256, blank=True)
    template_padname = models.CharField(max_length=256, blank=True)
    template_slug = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.name if len(self.name) < 90 else "".join([self.name[0:90],"..."])

    def _create(self, **kwargs):
        self.padid = self.server.client.create_group_pad(self.group.groupID, self.name, **kwargs)

    def _update(self):
        if self.password:
            public_status = self.server.client.set_password(self.padid, self.password)
        self.server.client.set_public_status(self.padid, self.is_public)

    def _destroy(self):
        self.server.client.delete_pad(self.padid)

    def link(self, user_id):
        return self.server.client.get_pad_link(self.padid, user_id)

    def save(self, *args, **kwargs):
        if not self.padid:
            self._create(**kwargs)
        self._update()
        # Clear text setter
        kwargs.pop('text',None)
        super(Pad, self).save(*args, **kwargs)


def padDel(sender, instance, **kwargs):
    """Make sure pads are purged from the etherpad-lite server on deletion
    """
    instance._destroy()

def groupDel(sender, instance, **kwargs):
    instance._destroy()

pre_delete.connect(padDel, sender=Pad)
pre_delete.connect(groupDel, sender=Group)
