from django.views.generic import TemplateView
from unfold.views import UnfoldSiteViewMixin


class AdminPageView(UnfoldSiteViewMixin, TemplateView):
    """Custom admin page registered through `UNFOLD["SITE_VIEWS"]`."""

    permission_required = ()
