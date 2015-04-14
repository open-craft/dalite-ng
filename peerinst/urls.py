from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.AssignmentListView.as_view(), name='assignment-list'),
    url(r'^assignment/(?P<assignment_id>[^/]+)/', include([
        url(r'^$', views.question, name='start-assignment'),
        url(r'(?P<question_index>\d+)/', include([
            url(r'^$', views.question, name='start-question'),
            url(r'^review$', views.review_answer, name='review-answer'),
            url(r'^summary$', views.answer_summary, name='answer-summary'),
        ])),
    ])),
]
