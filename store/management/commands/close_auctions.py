"""
store/management/commands/close_auctions.py

Closes all auctions whose end_time has passed and status is still 'live'.
Run every minute via cron or a process manager.

Cron example (runs every minute):
  * * * * * cd /srv/mnventures && venv/bin/python manage.py close_auctions >> logs/cron.log 2>&1

Systemd timer or Supervisor can also be used — see README.
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from store.models import AuctionItem

log = logging.getLogger('store.auctions')


class Command(BaseCommand):
    help = 'Close expired live auctions and open upcoming ones whose start time has passed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be changed without writing to the database'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now     = timezone.now()
        changed = 0

        # ── Open upcoming auctions ────────────────────────
        to_open = AuctionItem.objects.filter(status='upcoming', start_time__lte=now)
        for auction in to_open:
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would OPEN: {auction}')
            else:
                auction.status = 'live'
                auction.save(update_fields=['status'])
                log.info('Cron OPENED auction | id=%s product="%s"', auction.pk, auction.product.name)
                self.stdout.write(self.style.SUCCESS(f'Opened: {auction}'))
            changed += 1

        # ── Close expired live auctions ───────────────────
        to_close = AuctionItem.objects.filter(status='live', end_time__lte=now)
        for auction in to_close:
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would CLOSE: {auction}')
            else:
                auction.status = 'closed'
                auction._finalise()
                auction.save(update_fields=['status', 'winner', 'winning_bid'])
                log.info('Cron CLOSED auction | id=%s winner=%s amount=%s',
                         auction.pk,
                         auction.winner.phone if auction.winner else 'none',
                         auction.winning_bid or 0)
                self.stdout.write(self.style.SUCCESS(f'Closed: {auction} → winner: {auction.winner or "none"}'))
            changed += 1

        if changed == 0:
            self.stdout.write('No auction status changes needed.')
        else:
            self.stdout.write(f'Done — {changed} auction(s) updated.')
