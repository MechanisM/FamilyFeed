import json

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render

from profiles.forms import ChildForm, RegistrationForm
from profiles.models import Child, FacebookSource
from sources import youtube, facebook

from utils.json import ObjectEncoder
from utils.fb import facebook_callback, request_facebook_permissions


def start(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('timeline.views.timeline'))
    else:
        return render(request, 'profiles/start.html')


def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(username=user.username,
                                password=form.cleaned_data['password'])
            auth_login(request, user)
            return HttpResponseRedirect(reverse('profiles.views.add_child'))
    else:
        form = RegistrationForm()
    return render(request, 'profiles/registration.html', {'form': form})


@login_required
def add_child(request):
    if request.method == 'POST':
        form = ChildForm(request.POST, user=request.user)
        if form.is_valid():
            child = form.save()
            messages.success(request, u'%s, nice to meet you!' % child.name)
            url = reverse(
                'profiles.views.edit_child',
                args=[request.user.username, child.slug])
            return HttpResponseRedirect(url)
    else:
        form = ChildForm()
    return render(request,
                  'profiles/add_child.html',
                  {'is_add': True,
                   'form': form})


@login_required
def edit_child(request, username, child_slug):
    user = get_object_or_404(User, username=username)
    child = get_object_or_404(Child, user=user, slug=child_slug)
    return render(request, 'profiles/edit_child.html', {'child': child})


def youtube_feed(request):
    username = request.GET['username']
    return HttpResponse(json.dumps(youtube.list_videos(username),
                                   cls=ObjectEncoder))


def facebook_feed(request):
    token = 'TODO'
    username = request.GET['username']
    return HttpResponse(json.dumps(facebook.list_posts(username, token)))


@facebook_callback
def facebook_login_done(request, access_token):
    return HttpResponse(access_token)


@login_required
def add_facebook_profile(request, username, child_slug):
    permissions = ['offline_access', 'user_status', 'user_videos',
        'user_photos', 'user_notes']
    url = reverse(add_facebook_profile_done, args=[username, child_slug])
    return request_facebook_permissions(request, permissions, url)


@login_required
@facebook_callback
def add_facebook_profile_done(request, access_token, username, child_slug):
    import facebook as fb_sdk
    fb_data = fb_sdk.GraphAPI(access_token).get_object('me')
    facebook_uid = fb_data['id']

    name = fb_data['first_name']
    if 'last_name' in fb_data:
        name += ' ' + fb_data['last_name']

    child = get_object_or_404(Child, user__username=username, slug=child_slug)

    try:
        source = FacebookSource.objects.get(child=child, uid=facebook_uid)
        source.access_token = access_token
        source.name = name
        source.save()
    except FacebookSource.DoesNotExist:
        source = FacebookSource.objects.create(child=child,
                                               uid=facebook_uid,
                                               name=name,
                                               access_token=access_token)

    return render(request, 'profiles/add_facebook_profile_done.html')
