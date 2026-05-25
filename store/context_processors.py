from django.conf import settings


def site_settings(request):
    """Make business settings available in all templates."""
    return {
        'BUSINESS_NAME': settings.BUSINESS_NAME,
        'WHATSAPP_NUMBER': settings.WHATSAPP_NUMBER,
        'WHATSAPP_NUMBER_CLEAN': settings.WHATSAPP_NUMBER.replace('+', '').replace(' ', ''),
        'BUSINESS_LOCATION': settings.BUSINESS_LOCATION,
        'CURRENCY_SYMBOL': settings.CURRENCY_SYMBOL,
    }
