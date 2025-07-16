from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Channel, Message, ChannelMembership
from .forms import CustomUserCreationForm, CustomUserUpdateForm
from django.contrib import admin
from .models import ChannelMembership

class ChannelMembershipInline(admin.TabularInline):
    model = ChannelMembership
    extra = 1  # how many empty forms to show


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserUpdateForm
    model = CustomUser
    list_display = ['username', 'email', 'phone_number', 'is_staff', 'is_superuser']
    list_filter = ['is_staff', 'is_superuser']
    search_fields = ['username', 'email']

    # Fields for editing existing users
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_image')}),
        ('Permissions', {'fields': ('is_active',)}),
    )

    # Fields for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        # Only superusers can edit is_staff and is_superuser
        if request.user.is_superuser and obj:
            return (
                (None, {'fields': ('username', 'email', 'password')}),
                ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_image')}),
                ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
            )
        return super().get_fieldsets(request, obj)

    def has_change_permission(self, request, obj=None):
        # Allow superuser to edit all users, others can't edit is_staff/is_superuser
        return request.user.is_superuser


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_group_chat', 'max_file_size']
    list_filter = ['is_group_chat']
    search_fields = ['name']
    inlines = [ChannelMembershipInline]  # ✅ use inline instead of filter_horizontal



@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'channel', 'can_send_messages']
    list_filter = ['can_send_messages']
    search_fields = ['user__username', 'channel__name']
    actions = ['allow_sending_messages', 'disallow_sending_messages']

    def allow_sending_messages(self, request, queryset):
        queryset.update(can_send_messages=True)

    allow_sending_messages.short_description = "Allow selected users to send messages"

    def disallow_sending_messages(self, request, queryset):
        queryset.update(can_send_messages=False)

    disallow_sending_messages.short_description = "Disallow selected users from sending messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'channel', 'content', 'timestamp', 'read']
    list_filter = ['read', 'timestamp']
    search_fields = ['sender__username']

    def masked_content(self, obj):
        return '•••••••••' if obj.content else '(empty)'
    masked_content.short_description = 'Content (hidden)'

    exclude = ('content',)



