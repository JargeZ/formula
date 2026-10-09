"""Unfold styling for third-party apps shown in the sidebar."""

from django.contrib import admin
from django.contrib.sites.admin import SiteAdmin as BaseSiteAdmin
from django.contrib.sites.models import Site
from unfold.admin import ModelAdmin
from unfold.contrib.waffle.admin import FlagAdmin
from waffle.admin import SampleAdmin as BaseSampleAdmin
from waffle.admin import SwitchAdmin as BaseSwitchAdmin
from waffle.models import Flag, Sample, Switch

for model in (Site, Flag, Switch, Sample):
    admin.site.unregister(model)

admin.site.register(Flag, FlagAdmin)


@admin.register(Switch)
class SwitchAdmin(BaseSwitchAdmin, ModelAdmin):
    pass


@admin.register(Sample)
class SampleAdmin(BaseSampleAdmin, ModelAdmin):
    pass


@admin.register(Site)
class SiteAdmin(BaseSiteAdmin, ModelAdmin):
    pass
