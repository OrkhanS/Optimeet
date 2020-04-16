from django.contrib import admin
from APP.models import *
from APP.models import Matches
# Register your models here.

admin.site.register(User)
admin.site.register(Matches)
admin.site.register(BriddgyCities)
admin.site.register(Messages)
admin.site.register(Pictures)
admin.site.register(Posts)

