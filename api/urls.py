from django.urls import path
from . import views

urlpatterns = [
    path('send-line-message/', views.send_line_message, name='send_line_message'),
]
