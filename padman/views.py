# -*- coding: utf-8 -*-

# Python imports
import datetime
import time
import urllib.request, urllib.parse, urllib.error
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError

# Framework imports
from django.shortcuts import render_to_response, render, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext, Template, Context
from django.views.generic import DetailView, UpdateView
from django.views.generic.edit import FormView
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout, login, authenticate
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy

# additional imports
from py_etherpad import EtherpadLiteClient

# local imports
from . import models, forms, config

LOGIN_URL = reverse_lazy('padman:login')

def update_request(request, pad_server):
    """Updates the session to reflect the users group membership
    """

    author = models.PadAuthor.objects.current(pad_server, request.user)
    if author and pad_server.client.is_online():

        server = urlparse(author.server.url)
        groups = author.groups

        now = datetime.datetime.utcnow()
        expires = now + datetime.timedelta(seconds=config.SESSION_LENGTH)

        sessions = request.session.get("etherpad",{
            'expires': 0,
            'domain': server.hostname,
        })

        old_expires = datetime.datetime.fromtimestamp(sessions.get('expires'))
        new_expires = (expires if old_expires < now else old_expires)
        new_sessions = {'expires': new_expires.timestamp(), 'domain': server.hostname }

        # Provide valid sessions for all groups
        for group in groups:
            if group.groupID not in sessions or old_expires < now:
                group_session_expires = time.mktime(new_expires.timetuple())
                group_session_id = pad_server.client.create_session(group.groupID, author.authorID, group_session_expires)

                if group_session_id:
                    new_sessions[group.groupID] = {
                        'sessionID': group_session_id,
                    }
                if group.groupID in sessions:
                    sessions.pop(group.groupID)
            elif group.groupID in sessions:
                new_sessions[group.groupID] = sessions.pop(group.groupID)

        # Invalidate remaining sessions
        for group in sessions.keys():
            if group not in ('expires', 'domain'):
                pad_server.client.delete_session(sessions[group]['sessionID'])

        # Update session
        request.session['etherpad'] = new_sessions

def update_response(request, response):
    if request.user.is_authenticated:
        sessions = request.session.get("etherpad",{})
        #response.delete_cookie('sessionID', sessions.get('domain'))
        response.set_cookie(
            'sessionID',
            value='%2C'.join(s['sessionID'] for g,s in sessions.items() if g not in ('expires', 'domain')),
            expires=sessions.get('expires'),
            domain=sessions.get('domain'),
            httponly=False
        )
    return response

# Lazily evaluate session only on etherpad viewss
def session_wrapper(function):
  def wrap(request, *args, **kwargs):
    update_request(request)
    return update_response(request, function(request, *args, **kwargs))

  wrap.__doc__=function.__doc__
  wrap.__name__=function.__name__
  return wrap


class PadCreateView(LoginRequiredMixin, DetailView, FormView):
    template_name = 'padman/padCreate.html'
    form_class = forms.PadCreate

    def get_success_url(self):
        return reverse_lazy('padman:category-slug', args=[self.category.slug])

    def get_object(self):
        kwargs = self.request.resolver_match.kwargs
        self.category = get_object_or_404(models.PadCategory, slug=kwargs['category'])
        return self.category

    def get_initial(self):
        if not hasattr(self, 'category'):
            self.object = self.get_object()
        return {'category': self.category.slug }

    def form_valid(self, form):
        category = self.object
        server = form.cleaned_data['server']
        name = form.cleaned_data['name']

        group, created = models.PadGroup.objects.get_or_create(
            server=server,
            parent=category,
        )

        if created:
            group.group_mapper = category.slug
            group.name = category.name
            group.save()

        pad = models.Pad(
            name=form.cleaned_data['name'],
            server=group.server,
            group=group
        )
        pad.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'submit': _("Create"),
            'title': _("Create Pad"),
            'pk': self.object.pk,
            'title': _('Create pad in %(grp)s') % {'grp': group.__str__()}
        })
        return context


@login_required
@csrf_protect
def padDelete(request, pk):
    """Delete a given pad
    """
    pad = get_object_or_404(models.Pad, pk=pk)
    group = pad.group

    # Any form submissions will send us back to the profile
    if request.method == 'POST':
        if 'confirm' in request.POST:
            pad.delete()
        return HttpResponseRedirect(reverse_lazy('padman:category-slug', args=[group.group_mapper]))

    con = {
        'action': reverse_lazy('padman:delete', args=[pk]),
        'question': _('Really delete this pad?'),
        'title': _('Deleting %(pad)s') % {'pad': pad.__str__()}
    }
    #con.update(csrf(request))
    return render(request, 'padman/confirm.html', con)


@login_required
@csrf_protect
def padSearch(request):
    message = ""
    pads = []

    if request.method == 'POST':
        form = forms.SearchForm(request.POST)
        if form.is_valid():
            server = form.cleaned_data['server']
            result = server.epclient.call("search", {
                "query": form.cleaned_data['query'],
                "groupID": form.cleaned_data['group'].groupID,
            })
            pads = result.get("pads")
        else:
            message = _("Something went wrong!")
    else:
        form = forms.SearchForm()

    con = {
        'pads': pads,
        'form': form,
        'submit': _('search'),
        'title': _('search'),
        'message': message,
    }
    return render(request, 'padman/search.html', con)


@login_required
@csrf_protect
def groupSearch(request, group):
    group = get_object_or_404(models.PadGroup, group_mapper=group)
    pads = []

    query = request.GET.get("query","");
    if query:
        result = group.server.epclient.call("search", {
            "query": query,
            "groupID": group.groupID,
        })
        pads = [{
            "pad": models.Pad.objects.filter(padid=pad.get("pad")).first(),
            "matches": pad.get("matches"),
        } for pad in result.get("pads")]

    con = {
        'pads': pads,
        'query': query,
    }
    return render(request, 'padman/group-search.html', con)

@login_required
@csrf_protect
def groupCreate(request):
    """ Create a new Group
    """
    message = ""
    if request.method == 'POST':  # Process the form
        form = forms.GroupCreate(request.POST)
        if form.is_valid():
            group = form.save()
            return HttpResponseRedirect(reverse_lazy("padman:groupmapper", args=[group.group_mapper]))
        else:
            message = _("This Groupname is already in use or invalid.")
    else:  # No form to process so create a fresh one
        form = forms.GroupCreate()
    con = {
        'form': form,
        'submit': _('Create'),
        'title': _('Create a new Group'),
        'message': message,
    }
    return render(request, 'padman/groupCreate.html', con)

class GroupPadImportView(LoginRequiredMixin, FormView):

    template_name='padman/groupPadImport.html'
    form_class=forms.GroupPadImportForm

    def get_success_url(self):
        kwargs = self.request.resolver_match.kwargs
        return reverse_lazy('padman:category-slug', **kwargs)

    def form_valid(self, form):
        kwargs = self.request.resolver_match.kwargs
        group = get_object_or_404(models.PadGroup, group_mapper=kwargs['category'])
        form.import_unknown_pads(group)
        super().form_valid(form);

    def get_context_data(self):
        context = super().get_context_data()

        a = dir(self.request)
        kwargs = self.request.resolver_match.kwargs
        groups = models.PadGroup.objects.filter(group_mapper=kwargs['category'])

        context["groups"] = groups
        return context

@login_required()
def groupDelete(request, pk):
    """
    """
    pass

class RawPadView(DetailView):
    template_name = 'padman/raw.html'
    model = models.Pad

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pad = self.object
        context.update({'text': pad.server.client.get_text(pad.padid)})
        return context

class PadView(DetailView):
    template_name = 'padman/pad.html'
    model = models.Pad

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        for cookie in self.response_cookies:
            response.set_cookie(**cookie)
        response = update_response(self.request, response)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pad = self.object
        update_request(self.request, pad.server)

        self.response_cookies = []

        # Initialize some needed values
        server = urlparse(pad.server.url)
        context.update({
            'pad': pad,
            'server': server,
        })

        author = models.PadAuthor.objects.current(pad.server, self.request.user)
        if author:
            if author not in pad.group.authors.all():
                context.update({
                    'link': pad.link(str(author.user)),
                    'error': _('You are not allowed to view or edit this pad')
                })
                return context
            uname = author.user.__str__()
        else:
            uname = ''

        # Set up the response
        context.update({
            'link': pad.link(None),
            'error': False
        })

        if author:
            session = self.request.session.get("etherpad")
            if not session:
                raise RuntimeError("PadServer not available")
            expires = datetime.datetime.fromtimestamp(session.get('expires'))

            group_session = session.get(pad.group.groupID)
            if group_session:
                sessionID = group_session.get('sessionID')
                self.response_cookies += [{
                    'key': 'padSessionID',
                    'value': sessionID,
                    'expires': expires,
                    'httponly': False
                }]

        return context

class PadSlugView(PadView):

    def get_object(self):
        kwargs = self.request.resolver_match.kwargs
        return get_object_or_404(models.Pad, **kwargs)

class PadMapperView(PadView):

    def get_object(self):
        kwargs = self.request.resolver_match.kwargs
        return get_object_or_404(models.Pad, group__group_mapper=kwargs['group'], name=kwargs['show'])


class BaseCategoryView(LoginRequiredMixin, DetailView):
    model = models.PadCategory
    context_object_name = 'root'
    template_name = 'padman/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'current': self.current})
        context.update({'create_form': forms.PadCreate(initial={'category': self.current.slug})})
        context.update({'pads': models.Pad.objects.filter(group__parent=self.current)})
        context.update({'templates': models.Pad.objects.templates(self.current)})
        context.update({'pad_settings_form': forms.SettingsForm()})
        return context

class IndexView(BaseCategoryView):

    def get_object(self):
        self.root = models.PadCategory.objects.root_nodes().first()
        self.current = self.root.get_descendants().first()
        return self.root

class CategoryView(BaseCategoryView):

    def get_object(self):
        kwargs = self.request.resolver_match.kwargs
        self.current = get_object_or_404(models.PadCategory, slug=kwargs['category'])
        self.root = self.current.get_root()
        return self.root

class PadGroupView(LoginRequiredMixin, DetailView):
    model = models.Pad
    template_name = 'padman/index.html'
    context_object_name = 'current'

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset(**kwargs)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object

        pads = group.pad_set.all()
        if "query" in self.request.GET:
            pads = pads.filter(name__contains=self.request.GET.get("query"))

        context.update({
            'pads': pads,
            'create_form': forms.PadCreate({'group': group.groupID}),
            'categories': models.PadCategory.objects.all().filter(parent=None),
            'groups': models.PadGroup.objects.all().filter(parent=None),
        })
        return context


class PadGroupMapperView(PadGroupView):

    def get_object(self):
        kwargs = self.request.resolver_match.kwargs
        group = get_object_or_404(models.PadGroup, group_mapper=kwargs['group'])
        return group

class CategorySettingsView(UpdateView):
    model = models.PadCategory
    template_name = 'padman/group-settings.html'
    slug_url_kwarg = 'category'
    fields = ('name', 'parent', 'slug', 'show_non_leaf', 'groups')

    def get_success_url(self):
        return reverse_lazy('padman:category-slug', args=[self.object.slug])

    def get_context_data(self):
        context = super().get_context_data()
        context.update({'title': _('category settings')})
        context.update({'submit': _('save')})
        return context

class PadSettingsView(LoginRequiredMixin, UpdateView):
    model = models.Pad
    form_class = forms.SettingsForm
    template_name = 'padman/pad-settings.html'

    def get_success_url(self):
        return reverse_lazy('padman:category-slug', args=[self.object.group.parent.slug])

    def get_context_data(self):
        context = super().get_context_data()
        context.update({'title': _('pad settings')})
        context.update({'submit': _('save')})
        return context


@login_required()
@csrf_protect
def padDuplicate(request, pk):
    pad = get_object_or_404(models.Pad, pk=pk)
    date = datetime.datetime.now()

    client = pad.server.client
    text = client.get_text(pad.padid)
    text_template = Template(text)

    pass_template = Template(pad.template_password)
    password = pass_template.render(Context({}))
    name_template = Template(pad.template_padname)
    padname = name_template.render(Context({"date": date }))
    slug_template = Template(pad.template_slug)
    slug = slug_template.render(Context({"date": date }))

    new_text = text_template.render(Context({
        "password": password,
        "date": date,
        "name": padname,
        "slug": slug
    }))

    new_pad = models.Pad()
    new_pad.group = pad.group
    new_pad.name = padname
    new_pad.slug = slug
    new_pad.server = pad.server
    new_pad.password = password
    new_pad.is_public = pad.template_is_public
    new_pad.save(text=new_text)

    return HttpResponseRedirect(reverse_lazy('padman:pad', args=[new_pad.pk]))
