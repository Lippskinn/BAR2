from django.contrib import admin

from respool.models import Item, Image, Location, Loan, LoanAgreement, RentalFee, Category, Dimension, TimeInterval

# Register your models here.
# respool.models
admin.site.register(Item)
admin.site.register(Category)
admin.site.register(Dimension)
admin.site.register(LoanAgreement)
admin.site.register(Image)
admin.site.register(Location)
admin.site.register(Loan)
admin.site.register(RentalFee)
admin.site.register(TimeInterval)
