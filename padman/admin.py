# -*- coding: utf-8 -*-

from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from . import models


@admin.register(models.PadAuthor)
class PadAuthorAdmin(admin.ModelAdmin):
    list_display = ('__str__',)

@admin.register(models.Pad)
class PadAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'server')

@admin.register(models.PadServer)
class PadServerAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'backend')

@admin.register(models.PadCategory)
class PadCategoryAdmin(DraggableMPTTAdmin):
    list_display=(
        'tree_actions',
        'indented_title',
    )
    list_display_links=(
        'indented_title',
    )

admin.site.register(models.PadGroup)
