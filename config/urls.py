from django.contrib import admin
from django.urls import path
from todo import views as todo_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', todo_views.index, name='index'),
    path('<int:task_id>/', todo_views.detail, name='detail'),
    path('<int:task_id>/delete', todo_views.delete, name='delete'),
]
