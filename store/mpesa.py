"""
store/mpesa.py — Safaricom Daraja API integration
Paybill: 247247 | Account Number: 741222

Implements:
  - OAuth token fetch
  - STK Push (Lipa Na M-Pesa Online)
  - Callback processing
  - Invoice generation
"""
import base64
import logging
import uuid
from datetime import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.utils import timezone

from .models import MpesaPayment, Invoice, VAT_RATE

log = logging.getLogger('store.payments')


class MpesaError(Exception):
    pass


class DarajaClient:
    """
    Thin wrapper around the Safaricom Daraja v1 API.
    Credentials are read from Django settings / .env
    """

    SANDBOX_BASE  = 'https://sandbox.safaricom.co.ke'
    PROD_BASE     = 'https://api.safaricom.co.ke'

    def __init__(self):
        self.consumer_key    = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.passkey         = settings.MPESA_PASSKEY
        self.shortcode       = settings.MPESA_SHORTCODE       # 247247
        self.account_number  = settings.MPESA_ACCOUNT_NUMBER  # 741222
        self.callback_url    = settings.MPESA_CALLBACK_URL
        self.sandbox         = getattr(settings, 'MPESA_SANDBOX', True)
        self.base            = self.SANDBOX_BASE if self.sandbox else self.PROD_BASE
        self._token          = None
        self._token_expires  = None

    # ── Auth ──────────────────────────────────────────────

    def _get_token(self) -> str:
        """Fetch or return cached OAuth token."""
        now = datetime.now()
        if self._token and self._token_expires and now < self._token_expires:
            return self._token

        creds = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()

        resp = requests.get(
            f"{self.base}/oauth/v1/generate?grant_type=client_credentials",
            headers={'Authorization': f'Basic {creds}'},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        self._token = data['access_token']
        from datetime import timedelta
        self._token_expires = now + timedelta(seconds=int(data.get('expires_in', 3599)) - 60)
        return self._token

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self._get_token()}',
            'Content-Type':  'application/json',
        }

    # ── STK Push ──────────────────────────────────────────

    def stk_push(self, phone: str, amount: Decimal, account_ref: str, description: str) -> dict:
        """
        Initiate Lipa Na M-Pesa Online (STK Push).

        phone       — 254XXXXXXXXX format
        amount      — KSh amount (will be rounded to int)
        account_ref — e.g. auction slug or invoice number
        description — shown on the M-Pesa prompt
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password  = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()

        payload = {
            'BusinessShortCode': self.shortcode,
            'Password':          password,
            'Timestamp':         timestamp,
            'TransactionType':   'CustomerPayBillOnline',
            'Amount':            int(amount),
            'PartyA':            phone,
            'PartyB':            self.shortcode,
            'PhoneNumber':       phone,
            'CallBackURL':       self.callback_url,
            'AccountReference':  self.account_number,   # always 741222
            'TransactionDesc':   description[:13],       # Daraja limit
        }

        log.info('STK Push initiated | phone=%s amount=%s ref=%s', phone, amount, account_ref)

        resp = requests.post(
            f"{self.base}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=self._headers(),
            timeout=15,
        )

        data = resp.json()

        if resp.status_code != 200 or data.get('ResponseCode') != '0':
            log.error('STK Push failed | %s', data)
            raise MpesaError(data.get('errorMessage') or data.get('ResponseDescription', 'STK push failed'))

        log.info('STK Push queued | CheckoutRequestID=%s', data.get('CheckoutRequestID'))
        return data

    def query_stk(self, checkout_request_id: str) -> dict:
        """Query the status of a pending STK push."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password  = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()
        resp = requests.post(
            f"{self.base}/mpesa/stkpushquery/v1/query",
            json={
                'BusinessShortCode': self.shortcode,
                'Password':          password,
                'Timestamp':         timestamp,
                'CheckoutRequestID': checkout_request_id,
            },
            headers=self._headers(),
            timeout=10,
        )
        return resp.json()


# ── Payment service functions ──────────────────────────────────────────────────

def initiate_auction_payment(auction, bidder, amount: Decimal, payment_type: str = 'deposit') -> MpesaPayment:
    """
    Create a MpesaPayment record and fire the STK push.
    Raises MpesaError on failure.
    """
    phone = bidder.phone.replace('+', '').replace(' ', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]

    payment = MpesaPayment(
        payment_type=payment_type,
        auction=auction,
        bidder=bidder,
        phone_number=phone,
        amount=amount,
    )
    payment.compute_vat()
    payment.save()

    client = DarajaClient()
    desc   = f"MNV {auction.product.name[:10]}"
    try:
        result = client.stk_push(
            phone=phone,
            amount=amount,
            account_ref=str(payment.reference)[:12],
            description=desc,
        )
        payment.merchant_request_id = result.get('MerchantRequestID', '')
        payment.checkout_request_id = result.get('CheckoutRequestID', '')
        payment.save(update_fields=['merchant_request_id', 'checkout_request_id'])
    except Exception as e:
        payment.status = 'failed'
        payment.result_desc = str(e)
        payment.save(update_fields=['status', 'result_desc'])
        raise

    return payment


def process_mpesa_callback(data: dict) -> MpesaPayment | None:
    """
    Handle the raw JSON from Safaricom's callback POST.
    Returns the updated MpesaPayment or None if unrecognised.
    """
    try:
        body      = data.get('Body', {})
        stk_cb    = body.get('stkCallback', {})
        checkout_id = stk_cb.get('CheckoutRequestID', '')
        result_code = str(stk_cb.get('ResultCode', ''))
        result_desc = stk_cb.get('ResultDesc', '')

        payment = MpesaPayment.objects.filter(checkout_request_id=checkout_id).first()
        if not payment:
            log.warning('Callback for unknown CheckoutRequestID=%s', checkout_id)
            return None

        payment.result_code = result_code
        payment.result_desc = result_desc

        if result_code == '0':
            # Success — extract items
            items = {
                i['Name']: i.get('Value')
                for i in stk_cb.get('CallbackMetadata', {}).get('Item', [])
            }
            payment.mpesa_receipt_number = str(items.get('MpesaReceiptNumber', ''))
            payment.transaction_date     = str(items.get('TransactionDate', ''))
            payment.amount               = Decimal(str(items.get('Amount', payment.amount)))
            payment.status               = 'completed'
            payment.compute_vat()
            payment.save()

            # Generate invoice
            _generate_invoice(payment)

            log.info('M-Pesa payment COMPLETED | receipt=%s amount=%s phone=%s',
                     payment.mpesa_receipt_number, payment.amount, payment.phone_number)
        else:
            payment.status = 'failed'
            payment.save(update_fields=['status', 'result_code', 'result_desc'])
            log.warning('M-Pesa payment FAILED | code=%s desc=%s phone=%s',
                        result_code, result_desc, payment.phone_number)

        return payment

    except Exception as e:
        log.exception('Error processing M-Pesa callback: %s', e)
        return None


def _generate_invoice(payment: MpesaPayment) -> Invoice:
    """Create an Invoice record after successful payment."""
    if hasattr(payment, 'invoice'):
        return payment.invoice   # already exists

    inv_num = payment.generate_invoice_number()
    bidder  = payment.bidder

    invoice = Invoice.objects.create(
        payment=payment,
        invoice_number=inv_num,
        buyer_name=bidder.name if bidder else 'Customer',
        buyer_phone=bidder.phone if bidder else payment.phone_number,
        buyer_email=bidder.email if bidder else '',
        subtotal=payment.amount_excl_vat,
        vat_amount=payment.vat_amount,
        total=payment.amount,
        notes=f"Paybill: 247247 | Account: 741222 | Receipt: {payment.mpesa_receipt_number}",
    )
    log.info('Invoice generated | %s', inv_num)
    return invoice
