from django.conf import settings

def site_settings(request):
    """
    Expose site-wide settings to all templates.
    Also computes the BlueWave API docs URL from BLUEWAVE_API_BASE.
    """
    base = getattr(settings, "BLUEWAVE_API_BASE", "").rstrip("/")
    docs_url = f"{base}/docs" if base else ""

    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "BlueWave Solutions"),
        "STRIPE_PUBLISHABLE_KEY": getattr(settings, "STRIPE_PUBLISHABLE_KEY", ""),
        "BLUEWAVE_API_DOCS_URL": docs_url,
        "BLUEWAVE_API_BASE": base,
    }
