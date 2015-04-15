from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.AssignmentListView.as_view(), name='assignment-list'),
    url(r'^assignment/(?P<assignment_id>[^/]+)/', include([
        url(r'^$', views.QuestionStartView.as_view(), name='assignment-start'),
        url(r'(?P<question_index>\d+)/', include([
            url(r'^$', views.QuestionStartView.as_view(), name='question-start'),
            url(r'^review$', views.QuestionReviewView.as_view(), name='question-review'),
            url(r'^summary$', views.QuestionSummaryView.as_view(), name='question-summary'),
        ])),
    ])),
]
