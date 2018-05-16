from django.db import models
from django.db.models.signals import pre_delete
from django.contrib.auth.models import  Group
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from py_etherpad import EtherpadLiteClient

import string
import random
import urllib

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

    class Meta:
        verbose_name = _('server')
        verbose_name_plural = _('servers')

    def __str__(self):
        return self.url

    #TODO: validate url has trailing / or amend code elsewhere to add it if missing

    @property
    def apiurl(self):
        if self.url[-1:] == '/':
            return "%sapi" % self.url
        else:
            return "%s/api" % self.url

    @property
    def epclient(self):
        return EtherpadLiteClient(self.apikey, self.apiurl)


class PadCategory(models.Model):
    """Nested hierarchie for pad groups
    """
    name = models.CharField(max_length=256)
    parent = models.ForeignKey("self", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')


class PadGroup(models.Model):
    """Schema and methods for etherpad-lite groups
    """
    group = models.ForeignKey(Group)
    group_mapper = models.SlugField(max_length=256, unique=True)

    groupID = models.CharField(max_length=256, null=True, blank=True)
    server = models.ForeignKey(PadServer)

    name = models.CharField(max_length=256, null=True, blank=True)
    parent = models.ForeignKey(PadCategory, null=True, blank=True)

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def __str__(self):
        return self.title

    @property
    def title(self):
        if self.name:
            return self.name
        return str(self.group)

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
        return PadAuthor.objects.all().filter(server=self.server, user__in=self.group.user_set.all());

    @property
    def templates(self):
        return Pad.objects.all().filter(group=self, is_template=True)

    @property
    def epclient(self):
        return self.server.epclient

    def EtherMap(self):
        result = self.epclient.createGroupIfNotExistsFor(self.group_mapper)
        self.groupID = result['groupID']
        return result

    def save(self, *args, **kwargs):
        if not self.id:
            self.EtherMap()
        super(PadGroup, self).save(*args, **kwargs)

    def Destroy(self):
        # First find and delete all associated pads
        Pad.objects.filter(group=self).delete()
        return self.epclient.deleteGroup(self.groupID)


def padGroupDel(sender, **kwargs):
    """Make sure groups are purged from etherpad when deleted
    """
    grp = kwargs['instance']
    grp.Destroy()
pre_delete.connect(padGroupDel, sender=PadGroup)


def groupDel(sender, **kwargs):
    """Make sure our groups are destroyed properly when auth groups are deleted
    """
    grp = kwargs['instance']
    # Make shure auth groups without a pad group can be deleted, too.
    try:
        padGrp = PadGroup.objects.get(group=grp)
        padGrp.Destroy()
    except Exception:
        pass
pre_delete.connect(groupDel, sender=Group)


class PadAuthor(models.Model):
    """Schema and methods for etherpad-lite authors
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    authorID = models.CharField(max_length=256, blank=True)
    server = models.ForeignKey(PadServer)

    class Meta:
        verbose_name = _('author')
        verbose_name_plural = _('authors')

    def __str__(self):
        return self.user.__str__()

    def EtherMap(self):
        epclient = self.server.epclient
        result = epclient.createAuthorIfNotExistsFor(
            self.user.id.__str__(),
            name=self.__str__()
        )
        self.authorID = result['authorID']
        return result

    @property
    def groups(self):
        return PadGroup.objects.all().filter(server=self.server, group__in=self.user.groups.all())

    @property
    def group(self): # Backwards compatibility
        return self.groups

    def save(self, *args, **kwargs):
        self.EtherMap()
        super(PadAuthor, self).save(*args, **kwargs)


class Pad(models.Model):
    """Schema and methods for etherpad-lite pads
    """
    
    # The name of the pad
    name = models.CharField(max_length=256)

    # The server for this pad
    server = models.ForeignKey(PadServer)

    # The group that has access to this pad
    group = models.ForeignKey(PadGroup)

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
        return self.name

    @property
    def epclient(self):
        return EtherpadLiteClient(self.server.apikey, self.server.apiurl)

    def Create(self):
        self.epclient.createGroupPad(self.group.groupID, self.name)
        self.padid = "%s$%s" % (self.group.groupID, urllib.parse.quote_plus(self.name.replace(" ", "_")))

    def Update(self):
        if self.password:
            self.epclient.setPassword(self.padid,self.password)
        self.epclient.setPublicStatus(self.padid,"true" if self.is_public else "false") # Sigh, pyEtherpadLite
        print(self.epclient.getPublicStatus(self.padid))

    def Destroy(self):
        try:
            res = self.epclient.deletePad(self.padid)
        except ValueError:
            pass

    def isPublic(self):
        result = self.epclient.getPublicStatus(self.padid)
        return result['publicStatus']

    def ReadOnly(self):
        return self.epclient.getReadOnlyID(self.padid)

    def save(self, *args, **kwargs):
        if not self.padid:
            self.Create()
        self.Update()
        super(Pad, self).save(*args, **kwargs)


def padDel(sender, **kwargs):
    """Make sure pads are purged from the etherpad-lite server on deletion
    """
    pad = kwargs['instance']
    pad.Destroy()
pre_delete.connect(padDel, sender=Pad)
