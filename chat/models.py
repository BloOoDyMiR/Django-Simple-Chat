from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True, default='profiles/default.jpg')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

    def get_profile_image(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return '/media/profiles/default.jpg'

    def unread_messages_count(self, user):
        return Message.objects.filter(sender=self, recipient=user, read=False).count()

class Channel(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_channels')
    members = models.ManyToManyField(CustomUser, through='ChannelMembership', related_name='channels')
    created_at = models.DateTimeField(auto_now_add=True)
    is_group_chat = models.BooleanField(default=False)
    channel_image = models.ImageField(upload_to='channels/', blank=True, null=True, default='channels/default_channel.jpg')
    max_file_size = models.PositiveIntegerField(default=10, help_text='Maximum file size in MB')

    def __str__(self):
        return self.name

    def get_channel_image(self):
        if self.channel_image and hasattr(self.channel_image, 'url'):
            return self.channel_image.url
        return '/media/channels/default_channel.jpg'

    def unread_messages_count(self, user):
        return Message.objects.filter(channel=self, read=False).exclude(sender=user).count()

class ChannelMembership(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    can_send_messages = models.BooleanField(default=False, help_text='Allow this user to send messages in the channel')

    class Meta:
        unique_together = ('user', 'channel')

    def __str__(self):
        return f"{self.user.username} in {self.channel.name}"

class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, blank=True)
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='received_messages')
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='messages/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} to {self.recipient or self.channel}: {self.content[:50] if self.content else 'File message'}"