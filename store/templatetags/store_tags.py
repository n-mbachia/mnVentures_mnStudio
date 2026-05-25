"""
store/templatetags/store_tags.py
Custom template tags and filters for MN Ventures.
"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def product_image(product, css_class='w-full aspect-[4/3] object-cover'):
    """
    Render a product image or a branded SVG placeholder.
    Usage: {% product_image product css_class="..." %}
    """
    if product.image:
        try:
            url = product.image.url
            return format_html(
                '<img src="{}" alt="{}" class="{}" loading="lazy">',
                url, product.name, css_class
            )
        except Exception:
            pass
    # SVG placeholder with MN brand colours
    return format_html(
        '''<div class="{}  bg-gradient-to-br from-stone-800 to-stone-900
                    flex flex-col items-center justify-center gap-2 text-stone-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 opacity-30"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10
                       a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0
                       011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            <span class="text-xs uppercase tracking-widest opacity-40">No Image</span>
          </div>''',
        css_class
    )


@register.filter
def kes(value):
    """Format a number as KSh with thousands separator. {{ product.price|kes }}"""
    try:
        return f"KSh {float(value):,.0f}"
    except (ValueError, TypeError):
        return value


@register.filter
def phone_wa(phone):
    """Strip phone to WhatsApp-ready digits. {{ bidder.phone|phone_wa }}"""
    return phone.replace('+', '').replace(' ', '').replace('-', '')


@register.simple_tag
def wa_link(phone, message='Hello MN Ventures!'):
    """Generate a WhatsApp link. {% wa_link phone message %}"""
    import urllib.parse
    clean = phone.replace('+', '').replace(' ', '')
    return f"https://wa.me/{clean}?text={urllib.parse.quote(message)}"


@register.inclusion_tag('store/_whatsapp_btn.html')
def whatsapp_button(phone, message='Hello MN Ventures!', label='Chat on WhatsApp', size='md'):
    import urllib.parse
    clean = phone.replace('+', '').replace(' ', '')
    return {
        'href': f"https://wa.me/{clean}?text={urllib.parse.quote(message)}",
        'label': label,
        'size': size,
    }


@register.simple_tag(takes_context=True)
def canonical_url(context):
    """Return the full canonical URL for the current page."""
    request = context.get('request')
    if request:
        return request.build_absolute_uri(request.path)
    return ''
