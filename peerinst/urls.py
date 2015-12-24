# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, url

from . import admin_views
from . import views

urlpatterns = [
    url(r'^$', views.AssignmentListView.as_view(), name='assignment-list'),
    url(r'^login/$', 'django.contrib.auth.views.login', { 'template_name': 'peerinst/login.html'}, name='peerinst_login'),
    url(r'^assignment/(?P<assignment_id>[^/]+)/', include([
        url(r'^$', views.QuestionListView.as_view(), name='question-list'),
        url(r'(?P<question_id>\d+)/', include([
            url(r'^$', views.question, name='question'),
        ])),
    ])),
    url(r'^admin/$', admin_views.AdminIndexView.as_view(), name='admin-index'),
    url(r'^admin/peerinst/', include([
        url(r'^assignment_results/(?P<assignment_id>[^/]+)/', include([
            url(r'^$', admin_views.AssignmentResultsView.as_view(), name='assignment-results'),
        ])),
        url(r'^question_preview/(?P<question_id>[^/]+)$',
            admin_views.QuestionPreviewView.as_view(), name='question-preview'),
        url(r'^fake_usernames/$', admin_views.FakeUsernames.as_view(), name='fake-usernames'),
        url(r'^fake_countries/$', admin_views.FakeCountries.as_view(), name='fake-countries'),
        url(r'^attribution_analysis/$', admin_views.AttributionAnalysis.as_view(),
            name='attribution-analysis'),
    ])),
]
