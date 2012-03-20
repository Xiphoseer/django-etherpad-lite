Etherpad Lite for Django
========================

__This app is in a pre-alpha state - some assembly is required.__

This Django app provides a basic integration with etherpad lite. It presently allows django users created by the django.contrib.auth app to be mapped to etherpad users and groups, the creation of pads and secure sessions.

Patches, forks, questions and suggestions are always welcome.

Installation
------------

For now installation is all manual.

First you will need to [install etherpad-lite](http://github.com/Pita/etherpad-lite/blob/master/README.md), or have the server url and apikey of an existing etherpad-lite instance.

Lets assume if you are looking at this you already know how to [install Django](https://docs.djangoproject.com/en/1.3/intro/install/) and [start new Django projects](https://docs.djangoproject.com/en/1.3/intro/tutorial01/). 

You will need to clone this repo into your Django project, and add `etherpadlite` to the `INSTALLED_APPS` in your `settings.py`.

Finally you will need to add lines to your `urls.py` file. You can either add this line:

     url(r'^', include('etherpadlite.urls')),

Or, if you are already serving your home page via a different app, these lines:

     url(r'^etherpad', include('etherpadlite.urls')),
     url(r'^accounts/profile/$', include('etherpadlite.urls')),
     url(r'^logout$', include('etherpadlite.urls')),

Once you have done this, you will need to, at minimum, create a group and add a first etherpad-lite server via the django admin interface in order to take full advantage of this modules functionality:

1. Add a group: `admin/auth/group/add/`
2. Add an etherpad server: `admin/etherpadlite/padserver/add/`
3. Add an etherpad group corresponding to the auth group: `admin/etherpadlite/padgroup/add/`

At this point, any users you add to the django project who are members of an etherpad enabled group will be able to take full advantage of the modules features.

Support
-------

Some documentation exists in the [github wiki](https://github.com/sfyn/django-etherpad-lite/wiki).

Report issues to the [issue queue](https://github.com/sfyn/django-etherpad-lite/issues).

A note on multi-server support
------------------------------

I intend to support multiple etherpad-lite services with this App. At present this functionality is untested. Use it at your own risk.

Licensing
---------

Copyright 2012 Sofian Benaissa.

Etherpad Lite for Django is free software: you can redistribute it and/or modify it under the terms of the [GNU General Public License](http://www.gnu.org/licenses/) as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
