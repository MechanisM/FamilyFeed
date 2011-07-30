import json

from django.contrib.auth import authenticate, login as auth_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

import json

from profiles.forms import RegistrationForm
from sources import youtube
from utils.fb import facebook_callback

class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        return dict((k, v) for k, v in obj.__dict__.items() if not k.startswith("_"))


def start(request):
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


def add_child(request):
    return HttpResponse('add child')


def youtube_feed(request):
    username = request.GET['username']
    return HttpResponse(json.dumps(youtube.list_videos(username), cls=ObjectEncoder))


@facebook_callback
def facebook_login_done(request, access_token):
    return HttpResponse(access_token)


# def facebook_login_done(request):
#     code = request.GET['code']
#     return HttpResponse(code)
