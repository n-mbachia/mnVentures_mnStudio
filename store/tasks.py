"""
store/tasks.py
Celery background tasks for MN Ventures.

Tasks:
  close_expired_auctions   — runs every 60 s, closes any auction past end_time
  open_upcoming_auctions   — runs every 60 s, opens auctions whose start_time has passed
  send_outbid_notification — fires when a bidder is outbid (WhatsApp link sent to MN Ventures)
  send_winner_notification — fires when an auction closes with a winner
"""
import logging
import urllib.parse

from celery import shared_task
from django.conf import settings
from django.utils import timezone

log = logging.getLogger('store.auctions')


@shared_task(name='store.tasks.close_expired_auctions', bind=True, max_retries=3)
def close_expired_auctions(self):
    """
    Find all 'live' auctions whose end_time has passed and close them.
    This is the primary mechanism ensuring auctions close even if no user
    visits the page — resolves the reliability gap from page-based refresh_status().
    """
    from .models import AuctionItem

    now      = timezone.now()
    expired  = AuctionItem.objects.filter(status='live', end_time__lte=now)
    count    = 0

    for auction in expired:
        try:
            auction.refresh_status()   # sets status=closed and determines winner
            count += 1
            log.info('Task closed auction | id=%s product="%s"', auction.pk, auction.product.name)

            # Fire winner notification if there's a winner
            if auction.winner:
                send_winner_notification.delay(auction.pk)

        except Exception as exc:
            log.exception('Error closing auction id=%s: %s', auction.pk, exc)
            raise self.retry(exc=exc, countdown=10)

    if count:
        log.info('close_expired_auctions: closed %d auction(s)', count)
    return count


@shared_task(name='store.tasks.open_upcoming_auctions')
def open_upcoming_auctions():
    """
    Find all 'upcoming' auctions whose start_time has passed and open them.
    """
    from .models import AuctionItem

    now      = timezone.now()
    opening  = AuctionItem.objects.filter(status='upcoming', start_time__lte=now)
    count    = 0

    for auction in opening:
        try:
            auction.refresh_status()
            count += 1
            log.info('Task opened auction | id=%s product="%s"', auction.pk, auction.product.name)
        except Exception as exc:
            log.exception('Error opening auction id=%s: %s', auction.pk, exc)

    return count


@shared_task(name='store.tasks.send_outbid_notification')
def send_outbid_notification(auction_pk: int, outbid_phone: str, new_amount: float):
    """
    Log an outbid event. In production this is where you'd integrate an SMS
    gateway (Africa's Talking, Twilio) to notify the outbid bidder.

    For now: builds a WhatsApp link for MN Ventures staff to share manually,
    and logs it so it's visible in logs/auctions.log.
    """
    from .models import AuctionItem, BidderProfile

    try:
        auction = AuctionItem.objects.select_related('product').get(pk=auction_pk)
        bidder  = BidderProfile.objects.filter(phone=outbid_phone).first()
        if not bidder:
            return

        # WhatsApp message to the outbid bidder
        msg = urllib.parse.quote(
            f"Hi {bidder.name}! 😔 You've been outbid on *{auction.product.name}*.\n"
            f"New leading bid: KSh {new_amount:,.0f}\n"
            f"Bid again → {settings.SITE_URL}/auctions/{auction.slug}/"
        )
        wa_link = f"https://wa.me/{bidder.phone.replace('+','').replace(' ','')}?text={msg}"
        log.info('OUTBID notification | bidder=%s auction=%s new_amount=%s | wa_link=%s',
                 outbid_phone, auction_pk, new_amount, wa_link)

        # TODO: integrate Africa's Talking SMS:
        # import africastalking
        # africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        # sms = africastalking.SMS
        # sms.send(f"You've been outbid on {auction.product.name}. New bid: KSh {new_amount:,.0f}. "
        #          f"Bid again: {settings.SITE_URL}/auctions/{auction.slug}/",
        #          [bidder.phone])

    except Exception as exc:
        log.exception('send_outbid_notification error: %s', exc)


@shared_task(name='store.tasks.send_winner_notification')
def send_winner_notification(auction_pk: int):
    """
    Build a WhatsApp link to notify the winner and log it.
    MN Ventures staff opens the link to send the congratulations message.
    """
    from .models import AuctionItem

    try:
        auction = AuctionItem.objects.select_related('product', 'winner').get(pk=auction_pk)
        if not auction.winner:
            return

        winner = auction.winner
        msg = urllib.parse.quote(
            f"🎉 Congratulations {winner.name}! You won the MN Ventures auction for "
            f"*{auction.product.name}* with a winning bid of KSh {auction.winning_bid:,.0f}.\n\n"
            f"To complete your purchase, please send *KSh {auction.winning_bid:,.0f}* via M-Pesa:\n"
            f"  Paybill: *247247*\n"
            f"  Account: *741222*\n\n"
            f"Payment must be made within 48 hours. Reply here once paid and we will arrange delivery. "
            f"Thank you for shopping with MN Ventures! 🛋️"
        )
        wa_link = f"https://wa.me/{winner.phone.replace('+','').replace(' ','')}?text={msg}"

        log.info(
            'WINNER notification ready | auction=%s winner=%s amount=%s | Click to send: %s',
            auction_pk, winner.phone, auction.winning_bid, wa_link
        )

    except Exception as exc:
        log.exception('send_winner_notification error: %s', exc)
