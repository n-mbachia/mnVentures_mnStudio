from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Product, Enquiry, AuctionItem, Bid, BidderProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price_display', 'badge', 'is_available', 'is_featured', 'image_preview', 'created_at']
    list_filter = ['category', 'badge', 'is_available', 'is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_available', 'is_featured']
    readonly_fields = ['image_preview']

    # To choose if proce does display or not. 
    def price_display(self, obj):
        if obj.show_price:
            return format_html('<span style="color:#16a34a;font-weight:600;">{}</span>', obj.formatted_price())
        return format_html('<span style="color:#9ca3af;font-style:italic;">Hidden</span>')
    price_display.short_description = 'Price'

    # route for image as determined by mnventure/settings.py
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" style="border-radius:6px;" />', obj.image.url)
        return '—'
    image_preview.short_description = 'Preview'


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    readonly_fields = ['bidder', 'amount', 'placed_at', 'ip_address', 'is_valid', 'is_winning']
    can_delete = False
    ordering = ['-amount']


@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'status_badge', 'current_price_display', 'bid_count_display',
                    'start_time', 'end_time', 'winner']
    list_filter = ['status']
    search_fields = ['product__name']
    prepopulated_fields = {'slug': ('product',)}
    readonly_fields = ['status', 'winner', 'winning_bid', 'views_count', 'current_price_display', 'bid_count_display']
    inlines = [BidInline]

    fieldsets = (
        ('Product', {'fields': ('product', 'slug', 'description')}),
        ('Pricing', {'fields': ('starting_price', 'reserve_price', 'bid_increment')}),
        ('Schedule', {'fields': ('start_time', 'end_time')}),
        ('Live Info (read-only)', {'fields': ('status', 'current_price_display', 'bid_count_display', 'views_count', 'winner', 'winning_bid')}),
    )

    def status_badge(self, obj):
        colours = {'live': '#22c55e', 'upcoming': '#f59e0b', 'closed': '#6b7280', 'cancelled': '#ef4444'}
        colour = colours.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;">{}</span>',
            colour, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def current_price_display(self, obj):
        return obj.formatted_price()
    current_price_display.short_description = 'Current Price'

    def bid_count_display(self, obj):
        return obj.bid_count
    bid_count_display.short_description = 'Bids'

    def save_model(self, request, obj, form, change):
        # Don't overwrite slug if already set
        if not obj.slug and obj.product_id:
            from django.utils.text import slugify
            obj.slug = slugify(obj.product.name) + '-auction'
        super().save_model(request, obj, form, change)


@admin.register(BidderProfile)
class BidderProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'bid_count', 'created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at']

    def bid_count(self, obj):
        return obj.bids.count()
    bid_count.short_description = 'Bids Placed'


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['bidder', 'auction', 'amount_display', 'is_valid', 'is_winning', 'placed_at']
    list_filter = ['is_valid', 'is_winning', 'auction']
    search_fields = ['bidder__name', 'bidder__phone']
    readonly_fields = ['placed_at', 'ip_address']
    list_editable = ['is_valid']

    def amount_display(self, obj):
        return f"KSh {obj.amount:,.0f}"
    amount_display.short_description = 'Amount'


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'product', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'phone', 'email']
    list_editable = ['status']
    readonly_fields = ['name', 'phone', 'email', 'product', 'message', 'created_at']

    def has_add_permission(self, request):
        return False


admin.site.site_header = 'MN Ventures Admin'
admin.site.site_title = 'MN Ventures'
admin.site.index_title = 'Store Management'
