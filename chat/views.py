from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import CustomUser, Channel, Message, ChannelMembership
from .forms import CustomUserCreationForm, CustomUserUpdateForm, CustomPasswordChangeForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Failed to update profile.')
    else:
        form = CustomUserUpdateForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Failed to change password. Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {'form': form})
@login_required
def home_view(request):
    message_user_ids = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).values_list('sender', 'recipient')

    # Flatten and remove duplicates & self
    user_ids = set()
    for sender_id, recipient_id in message_user_ids:
        if sender_id != request.user.id:
            user_ids.add(sender_id)
        if recipient_id != request.user.id:
            user_ids.add(recipient_id)

    users = CustomUser.objects.filter(id__in=user_ids)

    channels = request.user.channels.all()
    for user in users:
        user.unread_count = user.unread_messages_count(request.user)
    for channel in channels:
        channel.unread_count = channel.unread_messages_count(request.user)
    return render(request, 'home.html', {'users': users, 'channels': channels})

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from .models import CustomUser  # adjust if your user model import is different

@login_required
def search_view(request):
    query = request.GET.get('q', '').strip()
    users = []
    channels = []

    if query:
        # Match username, email or phone exactly (case-insensitive)
        users = CustomUser.objects.filter(
            Q(username__iexact=query) |
            Q(email__iexact=query) |
            Q(phone_number__iexact=query)
        ).exclude(id=request.user.id)

        channels = request.user.channels.filter(name__icontains=query)

        # Optional: attach unread count
        for user in users:
            user.unread_count = user.unread_messages_count(request.user)

        for channel in channels:
            channel.unread_count = channel.unread_messages_count(request.user)

    return render(request, 'home.html', {
        'users': users,
        'channels': channels,
        'query': query,
    })

@login_required
def private_chat_view(request, user_id):
    recipient = CustomUser.objects.get(id=user_id)
    messages = Message.objects.filter(
        Q(sender=request.user, recipient=recipient) | Q(sender=recipient, recipient=request.user)
    ).order_by('timestamp')
    Message.objects.filter(sender=recipient, recipient=request.user, read=False).update(read=True)
    return render(request, 'chat.html', {'recipient': recipient, 'messages': messages})

@login_required
def channel_chat_view(request, channel_id):
    channel = Channel.objects.get(id=channel_id)
    messages = Message.objects.filter(channel=channel).order_by('timestamp')
    Message.objects.filter(channel=channel, read=False).exclude(sender=request.user).update(read=True)
    return render(request, 'chat.html', {'channel': channel, 'messages': messages})

@login_required
def create_channel_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        is_group_chat = request.POST.get('is_group_chat') == 'on'
        max_file_size = request.POST.get('max_file_size', 10)
        channel = Channel.objects.create(name=name, created_by=request.user, is_group_chat=is_group_chat, max_file_size=max_file_size)
        ChannelMembership.objects.create(user=request.user, channel=channel, can_send_messages=True)
        if request.FILES.get('channel_image'):
            channel.channel_image = request.FILES.get('channel_image')
            channel.save()
        return redirect('channel_chat', channel_id=channel.id)
    return render(request, 'create_channel.html')

@login_required
def add_channel_member_view(request, channel_id):
    channel = Channel.objects.get(id=channel_id)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = CustomUser.objects.get(id=user_id)
        ChannelMembership.objects.create(user=user, channel=channel, can_send_messages=False)
        return redirect('channel_chat', channel_id=channel.id)
    users = CustomUser.objects.exclude(id__in=channel.members.all())
    return render(request, 'add_member.html', {'channel': channel, 'users': users})

@login_required
def send_message_view(request):
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        file = request.FILES.get('file', None)
        channel_id = request.POST.get('channel_id')
        recipient_id = request.POST.get('recipient_id')

        if not content and not file:
            messages.error(request, 'Please enter a message or select a file.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        try:
            message = Message(sender=request.user)
            if content:
                message.content = content
            if file:
                if channel_id:
                    channel = Channel.objects.get(id=channel_id)
                    file_size_mb = file.size / (1024 * 1024)
                    if file_size_mb > channel.max_file_size:
                        messages.error(request, f'File size exceeds channel limit of {channel.max_file_size}MB.')
                        return redirect(request.META.get('HTTP_REFERER', 'home'))
                message.file = file
            if channel_id:
                channel = Channel.objects.get(id=channel_id)
                if not (request.user.is_superuser or ChannelMembership.objects.filter(user=request.user, channel=channel, can_send_messages=True).exists()):
                    messages.error(request, 'You do not have permission to send messages in this channel.')
                    return redirect(request.META.get('HTTP_REFERER', 'home'))
                message.channel = channel
            elif recipient_id:
                message.recipient = CustomUser.objects.get(id=recipient_id)
            else:
                messages.error(request, 'Invalid chat context.')
                return redirect('home')
            message.save()
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect('home')

@login_required
def get_messages_view(request):
    channel_id = request.GET.get('channel_id')
    recipient_id = request.GET.get('recipient_id')
    last_message_id = request.GET.get('last_message_id', 0)

    try:
        messages = []
        if channel_id:
            channel = Channel.objects.get(id=channel_id)
            messages = Message.objects.filter(channel=channel, id__gt=last_message_id).order_by('timestamp')
        elif recipient_id:
            recipient = CustomUser.objects.get(id=recipient_id)
            messages = Message.objects.filter(
                Q(sender=request.user, recipient=recipient) | Q(sender=recipient, recipient=request.user),
                id__gt=last_message_id
            ).order_by('timestamp')
        else:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        message_data = [
            {
                'id': msg.id,
                'sender': msg.sender.get_full_name() or msg.sender.username,
                'sender_profile_image': msg.sender.get_profile_image(),
                'content': msg.content or '',
                'file_url': msg.file.url if msg.file else '',
                'file_type': (
                    'image' if msg.file and msg.file.name.lower().endswith(('.jpg', '.png', '.jpeg', '.gif')) else
                    'video' if msg.file and msg.file.name.lower().endswith(('.mp4', '.webm')) else
                    'audio' if msg.file and msg.file.name.lower().endswith(('.mp3', '.wav')) else
                    'file'
                ),
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M'),
                'is_sent': msg.sender == request.user,
                'read': msg.read
            }
            for msg in messages
        ]
        if channel_id:
            Message.objects.filter(channel=channel, read=False).exclude(sender=request.user).update(read=True)
        elif recipient_id:
            Message.objects.filter(sender=recipient, recipient=request.user, read=False).update(read=True)
        return JsonResponse({'messages': message_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_unread_counts(request):
    try:
        users = CustomUser.objects.exclude(id=request.user.id)
        channels = request.user.channels.all()
        user_data = [
            {'id': user.id, 'unread_count': user.unread_messages_count(request.user)}
            for user in users
        ]
        channel_data = [
            {'id': channel.id, 'unread_count': channel.unread_messages_count(request.user)}
            for channel in channels
        ]
        return JsonResponse({
            'users': user_data,
            'channels': channel_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)