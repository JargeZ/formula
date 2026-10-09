AGENTIC_LAYER_APP = "django_unfold_agentic_layer"


class AgenticLayerRouter:
    """Read-only demo: OAuth clients and tokens go to the writable copy, the rest stays read-only."""

    def db_for_read(self, model, **hints):
        return "agentic_layer" if model._meta.app_label == AGENTIC_LAYER_APP else None

    db_for_write = db_for_read

    def allow_relation(self, obj1, obj2, **hints):
        # The copy has the same users, so a token may point at a user read from default.
        return True
