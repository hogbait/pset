from django.contrib import admin
from main.models import *

#admin.site.register(modelname)


class ClassNumberInline(admin.StackedInline):
    model = ClassNumber
    extra = 1

class ClassAdmin(admin.ModelAdmin):
    inlines = [ClassNumberInline]


admin.site.register(UserInfo)
admin.site.register(PendingHash)
admin.site.register(Class, ClassAdmin)
admin.site.register(ClassNumber)
