# -*- coding: utf-8 -*-

# Python imports
import datetime
import time
import urllib.request, urllib.parse, urllib.error
from urllib.parse import urlparse

# Framework imports
from django.shortcuts import render_to_response, render, get_object_or_404

from django.http import HttpResponseRedirect
from django.template import RequestContext, Template, Context
#from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

# additional imports
from py_etherpad import EtherpadLiteClient

# local imports
from etherpadlite.models import *
from etherpadlite import forms
from etherpadlite import config


LOGIN_URL = reverse_lazy('etherpadlite:login')

def update_request(request):
    """Updates the session to reflect the users group membership
    """

    # Get Author and groups
    author = PadAuthor.objects.get(user=request.user)
    epclient = author.server.epclient
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
            result = epclient.createSession(
                group.groupID,
                author.authorID,
                str(time.mktime(new_expires.timetuple()))
            )
            new_sessions[group.groupID] = {
                'sessionID': result["sessionID"],
            }
            if group.groupID in sessions:
                sessions.pop(group.groupID)
        elif group.groupID in sessions:
            new_sessions[group.groupID] = sessions.pop(group.groupID)

    # Invalidate remaining sessions
    for session in sessions:
        if session not in ('expires', 'domain'):
            epclient.deleteSession(session.sessionID)

    # Update session
    request.session['etherpad'] = new_sessions

def update_response(request, response):
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


@login_required(login_url=LOGIN_URL)
@csrf_protect
@session_wrapper
def padCreate(request, pk):
    """Create a named pad for the given group
    """
    group = get_object_or_404(PadGroup, pk=pk)

    if request.method == 'POST':  # Process the form
        form = forms.PadCreate(request.POST)
        if form.is_valid():
            pad = Pad(
                name=form.cleaned_data['name'],
                server=group.server,
                group=group
            )
            pad.save()
            return HttpResponseRedirect(reverse_lazy("etherpadlite:group", args=[group.pk]))
    else:  # No form to process so create a fresh one
        form = forms.PadCreate({'group': group.groupID})

    con = {
        'form': form,
        'submit': _("Create"),
        'title': _("Create Pad"),
        'pk': pk,
        'title': _('Create pad in %(grp)s') % {'grp': group.__str__()}
    }
    #con.update(csrf(request))
    return render(request, 'etherpad-lite/padCreate.html', con)


@login_required(login_url=LOGIN_URL)
@csrf_protect
@session_wrapper
def padDelete(request, pk):
    """Delete a given pad
    """
    pad = get_object_or_404(Pad, pk=pk)
    group = pad.group

    # Any form submissions will send us back to the profile
    if request.method == 'POST':
        if 'confirm' in request.POST:
            pad.delete()
        return HttpResponseRedirect(reverse_lazy('etherpadlite:group', args=[group.pk]))

    con = {
        'action': reverse_lazy('etherpadlite:delete', args=[pk]),
        'question': _('Really delete this pad?'),
        'title': _('Deleting %(pad)s') % {'pad': pad.__str__()}
    }
    #con.update(csrf(request))
    return render(request, 'etherpad-lite/confirm.html', con)


@login_required(login_url=LOGIN_URL)
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
    return render(request, 'etherpad-lite/search.html', con)


@login_required(login_url=LOGIN_URL)
@csrf_protect
def groupSearch(request, group):
    group = get_object_or_404(PadGroup, group_mapper=group)
    pads = []

    query = request.GET.get("query","");
    if query:
        result = group.server.epclient.call("search", {
            "query": query,
            "groupID": group.groupID,
        })
        pads = [{
            "pad": Pad.objects.filter(padid=pad.get("pad")).first(),
            "matches": pad.get("matches"),
        } for pad in result.get("pads")]

    con = {
        'pads': pads,
        'query': query,
    }
    return render(request, 'etherpad-lite/group-search.html', con)

@login_required(login_url=LOGIN_URL)
@csrf_protect
@session_wrapper
def groupCreate(request):
    """ Create a new Group
    """
    message = ""
    if request.method == 'POST':  # Process the form
        form = forms.GroupCreate(request.POST)
        if form.is_valid():
            group = form.save()
            return HttpResponseRedirect(reverse_lazy("etherpadlite:groupmapper", args=[group.group_mapper]))
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
    return render(request, 'etherpad-lite/groupCreate.html', con)


@login_required(login_url=LOGIN_URL)
def groupDelete(request, pk):
    """
    """
    pass


@login_required(login_url=LOGIN_URL)
def profile(request):
    """Display a user profile containing etherpad groups and associated pads
    """
    name = request.user.__str__()

    try:  # Retrieve the corresponding padauthor object
        author = PadAuthor.objects.get(user=request.user)
    except PadAuthor.DoesNotExist:  # None exists, so create one
        author = PadAuthor(
            user=request.user,
            server=PadServer.objects.get(id=1)
        )
        author.save()

    groups = {}
    for g in author.group.all():
        groups[g.__str__()] = {
            'group': g,
            'pads': Pad.objects.filter(group=g)
        }

    return render(
        request,
        'etherpad-lite/profile.html',
        {
            'name': name,
            'author': author,
            'groups': groups
        }
    )


@session_wrapper
def pad_provider(request, pad):
    """Create and session and display an embedded pad
    """

    # Initialize some needed values
    padLink = pad.server.url + 'p/' + pad.padid
    server = urlparse(pad.server.url)
    
    author = PadAuthor.objects.get(user=request.user)
    if author not in pad.group.authors.all():
        response = render(
            request,
            'etherpad-lite/pad.html',
            {
                'pad': pad,
                'link': padLink,
                'server': server,
                'uname': author.user.__str__(),
                'error': _('You are not allowed to view or edit this pad')
            }
        )
        return response

    # Set up the response
    response = render(
        request,
        'etherpad-lite/pad.html',
        {
            'pad': pad,
            'link': padLink,
            'server': server,
            'uname': author.user.__str__(),
            'error': False
        }
    )

    session = request.session.get("etherpad")
    expires = datetime.datetime.fromtimestamp(session.get('expires'))
    sessionID = session.get(pad.group.groupID).get('sessionID')

    response.set_cookie(
        'padSessionID',
        value=sessionID,
        expires=expires,
        httponly=False
    )
    return response


@login_required(login_url=LOGIN_URL)
def pad(request, pk):
    pad_instance = get_object_or_404(Pad, pk=pk)
    return pad_provider(request, pad_instance)

def padShortLink(request, slug):
    pad_instance = get_object_or_404(Pad, slug=slug)
    return pad_provider(request, pad_instance)

@login_required(login_url=LOGIN_URL)
def padMapper(request, group, show):
    name = show.replace("_", " ")
    pad_instance = get_object_or_404(Pad, group__group_mapper=group, name=name)
    return pad_provider(request, pad_instance)


@login_required(login_url=LOGIN_URL)
@csrf_protect
@session_wrapper
def padIndex(request):
    con = {
        'categories': PadCategory.objects.all().filter(parent=None),
        'groups': PadGroup.objects.all().filter(parent=None),
    }
    return render(request, 'etherpad-lite/index.html', con)


@session_wrapper
@csrf_protect
def group_provide(request, group):

    pads = group.pad_set.all()
    if "query" in request.GET:
        pads = pads.filter(name__contains=request.GET.get("query"))

    con = {
        'current': group,
        'pads': pads,
        'create_form': forms.PadCreate({'group': group.groupID}),
        'categories': PadCategory.objects.all().filter(parent=None),
        'groups': PadGroup.objects.all().filter(parent=None),
    }
    return render(request, 'etherpad-lite/index.html', con)


@login_required(login_url=LOGIN_URL)
def padGroup(request, pk):
    group = get_object_or_404(PadGroup, pk=pk)
    return group_provide(request, group)


@login_required(login_url=LOGIN_URL)
def groupMapper(request, group):
    group = get_object_or_404(PadGroup, group_mapper=group)
    return group_provide(request, group)


@login_required(login_url=LOGIN_URL)
@csrf_protect
@session_wrapper
def groupSettings(request, group):
    group = get_object_or_404(PadGroup, group_mapper=group)
    message = ""

    if request.method == 'POST':  # Process the form
        form = forms.GroupSettingsForm(request.POST, instance=group)
        if form.is_valid():
            group = form.save()
            return HttpResponseRedirect(reverse_lazy("etherpadlite:group", args=[group.pk]))
        else:
            message = _("This Groupname is already in use or invalid.")
    else:
        form = forms.GroupSettingsForm(instance=group)
    
    con = {
        'group': group,
        'form': form,
        'title': _("group settings"),
        'submit': _("save"),
    }
    return render(request, 'etherpad-lite/group-settings.html', con)


@login_required(login_url=LOGIN_URL)
@csrf_protect
@session_wrapper
def padSettings(request, pk):
    
    message = None
    pad = get_object_or_404(Pad, pk=pk)
    
    if request.method == 'POST':
        form = forms.SettingsForm(request.POST, instance=pad)
        if form.is_valid():
            pad = form.save()
    else:
        form = forms.SettingsForm(instance=pad)
    
    return render(
        request,
        'etherpad-lite/pad-settings.html',
        {
            'title': _("pad settings"),
            'submit': _("save"),
            'form': form,
            'message': message
        }
    )

@login_required(login_url=LOGIN_URL)
@csrf_protect
@session_wrapper
def padDuplicate(request, pk):
    pad = get_object_or_404(Pad, pk=pk)
    date = datetime.datetime.now()
    
    text = pad.epclient.getText(pad.padid).get("text")
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

    new_pad = Pad()
    new_pad.group = pad.group
    new_pad.name = padname
    new_pad.slug = slug
    new_pad.server = pad.server
    new_pad.password = password
    new_pad.is_public = pad.template_is_public
    new_pad.save()

    new_pad.epclient.setText(new_pad.padid, new_text)

    return HttpResponseRedirect(reverse_lazy('etherpadlite:pad', args=[new_pad.pk]))


def login_view(request):
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(request.GET['next'])
            else:
                message = _("Wrong credentials")
        else:
            message = _("Invalid form data")
        return render(
            request,
            'etherpad-lite/login.html',
            {
                'form': form,
                'message': message
            }
        )
    else:
        form = forms.LoginForm()
        return render(request, 'etherpad-lite/login.html', {'form': form})
    
        
def logout_view(request):
    logout(request)
    return render(request, 'etherpad-lite/logout.html')