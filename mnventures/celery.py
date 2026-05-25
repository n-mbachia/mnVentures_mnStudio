"""
mnventures/celery.py
Celery application for background tasks:
  - Closing auctions reliably (even without page visits)
  - Sending outbid / winner notifications
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mnventures.settings')

app = Celery('mnventures')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ── Periodic tasks ────────────────────────────────────────
app.conf.beat_schedule = {
    # Close expired auctions every 60 seconds
    'close-expired-auctions': {
        'task':     'store.tasks.close_expired_auctions',
        'schedule': 60.0,
    },
    # Open upcoming auctions every 60 seconds
    'open-upcoming-auctions': {
        'task':     'store.tasks.open_upcoming_auctions',
        'schedule': 60.0,
    },
}
app.conf.timezone = 'Africa/Nairobi'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
