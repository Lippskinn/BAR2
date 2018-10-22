from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import Borrower, Lender

UserAdmin.add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name'),
    }
     ),
)
# Add is_staff and id columns to admin page
UserAdmin.list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
UserAdmin.list_display_links = ('id', 'username')
UserAdmin.search_fields = ('username', 'first_name', 'last_name')

admin.site.register(Borrower)
admin.site.register(Lender)
