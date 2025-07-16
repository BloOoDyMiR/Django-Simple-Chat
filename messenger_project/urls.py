"""
URL configuration for messenger_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from chat import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('', views.home_view, name='home'),
    path('search/', views.search_view, name='search'),
    path('chat/private/<int:user_id>/', views.private_chat_view, name='private_chat'),
    path('chat/channel/<int:channel_id>/', views.channel_chat_view, name='channel_chat'),
    path('channel/create/', views.create_channel_view, name='create_channel'),
    path('channel/<int:channel_id>/add_member/', views.add_channel_member_view, name='add_channel_member'),
    path('chat/send/', views.send_message_view, name='send_message'),
    path('chat/messages/', views.get_messages_view, name='get_messages'),
    path('chat/unread_counts/', views.get_unread_counts, name='get_unread_counts'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)