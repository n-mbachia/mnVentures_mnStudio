# 🛋️ MN Ventures — Furniture Store Website

A full-stack furniture e-commerce website for **MN Ventures**, a premium furniture business based in **Nairobi, Kenya**. Customers browse the product catalogue and place orders directly via **WhatsApp**.

---

## 🌟 Features

- **Product Gallery** — Browse all furniture with category filtering (Living Room, Bedroom, Dining, Office)
- **WhatsApp Ordering** — Every product has a direct "Order on WhatsApp" button pre-filled with the product name and price
- **Product Detail Pages** — Full descriptions, pricing in Kenya Shillings (KSh), related products
- **Enquiry Form** — AJAX-powered contact form, submissions stored in the database
- **Admin Panel** — Manage products, categories, and enquiries via Django Admin
- **Responsive Design** — Mobile-first layout using Tailwind CSS
- **PostgreSQL Database** — Robust, production-ready database
- **Pagination** — Product grid paginated (9 per page)
- **Sample Data** — 8 sample furniture products across 4 categories pre-loaded

---

## 🏗️ Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Django 4.2 (Python)               |
| Frontend   | Tailwind CSS (CDN) + Vanilla JS   |
| Database   | PostgreSQL                        |
| Media      | Pillow (image handling)           |
| Config     | python-decouple (.env)            |
| Static     | WhiteNoise (static file serving)  |
| Production | Gunicorn (WSGI server)            |

---

## 📁 Project Structure

```
mnventures/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── mnventures/                  # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── store/                       # Main app
│   ├── models.py                # Category, Product, Enquiry models
│   ├── views.py                 # Home, product detail, enquiry, JSON API
│   ├── urls.py                  # URL routes
│   ├── admin.py                 # Admin customisation
│   ├── forms.py                 # EnquiryForm
│   ├── context_processors.py   # Global business settings in templates
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── 0002_sample_data.py  # Pre-loads 8 sample products
│   └── templates/store/
│       ├── base.html            # Navbar, footer, Tailwind config
│       ├── home.html            # Hero, product grid, contact section
│       ├── product_detail.html  # Individual product page
│       ├── about.html           # About page
│       └── enquiry_success.html
│
├── static/store/css/
│   └── custom.css               # Animations, scrollbar styles
│
└── media/                       # Uploaded product images (auto-created)
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip

---

### Step 1 — Clone / Download the project

```bash
cd your-projects-folder
# (place the mnventures folder here)
cd mnventures
```

---

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# Activate it:
# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Set up PostgreSQL database

Open the PostgreSQL shell (psql) and run:

```sql
CREATE DATABASE mnventures_db;
CREATE USER mnventures_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE mnventures_db TO mnventures_user;
\q
```

---

### Step 5 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```ini
SECRET_KEY=your-very-secret-key-here-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=mnventures_db
DB_USER=mnventures_user
DB_PASSWORD=your_strong_password
DB_HOST=localhost
DB_PORT=5432
```

> **Generate a secret key:**
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

---

### Step 6 — Run migrations

```bash
python manage.py migrate
```

This will:
- Create all database tables
- Load 8 sample furniture products across 4 categories

---

### Step 7 — Create a superuser (admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

---

### Step 8 — Collect static files (optional in dev)

```bash
python manage.py collectstatic
```

---

### Step 9 — Run the development server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

Admin panel: **http://127.0.0.1:8000/admin/**

---

## 🛍️ Managing Products (Admin Panel)

1. Go to **http://127.0.0.1:8000/admin/**
2. Log in with your superuser credentials
3. Under **Store**, click **Products → Add Product**
4. Fill in: Name, Category, Description, Price (in KSh), Image, Badge
5. Check **Is available** and **Is featured** as needed
6. Save — the product will appear on the website immediately

### Adding Product Images
- In the admin, scroll to **Pricing & Media**
- Upload a JPG or PNG image
- Images are stored in `media/products/`
- Recommended size: **800×600px** or **4:3 ratio**

---

## 📱 WhatsApp Ordering Flow

When a customer clicks **"Order on WhatsApp"**:

1. WhatsApp opens (app or web) with a pre-filled message:
   > *"Hello MN Ventures! 🛋️ I'm interested in ordering the **Savanna Sofa Set** (KSh 85,000). Could you please provide more details and availability?"*
2. The customer sends the message
3. You respond and close the sale

**WhatsApp Number:** `+254 715 741 222`

To update the number, edit `mnventures/settings.py`:
```python
WHATSAPP_NUMBER = '+254715741222'
```

---

## 🌍 Deployment (Production)

### Environment changes

Update `.env` for production:

```ini
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your-production-secret-key
```

### Run with Gunicorn

```bash
gunicorn mnventures.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Recommended Stack
- **Server:** Ubuntu 22.04 VPS (e.g., DigitalOcean, Hetzner)
- **Reverse Proxy:** Nginx
- **Process Manager:** Supervisor or systemd
- **SSL:** Let's Encrypt (Certbot)
- **Database:** Managed PostgreSQL or self-hosted

---

## 🔧 Customisation

### Change Currency / Business Info
Edit `mnventures/settings.py`:
```python
WHATSAPP_NUMBER = '+254715741222'
BUSINESS_NAME   = 'MN Ventures'
BUSINESS_LOCATION = 'Nairobi, Kenya'
CURRENCY_SYMBOL = 'KSh'
```

### Add a New Category
Admin → Categories → Add Category → enter name, save.

### Change Colour Theme
The amber/gold theme is set in `store/templates/store/base.html` inside the `tailwind.config` block. Change `brand` colours to your preference.

---

## 📊 Database Models

### `Category`
| Field | Type | Notes |
|-------|------|-------|
| name | CharField | e.g. "Living Room" |
| slug | SlugField | auto-generated |
| description | TextField | optional |

### `Product`
| Field | Type | Notes |
|-------|------|-------|
| name | CharField | Product name |
| category | ForeignKey | Links to Category |
| short_description | CharField | Shown on card (max 300 chars) |
| description | TextField | Full detail page description |
| price | DecimalField | In Kenya Shillings |
| image | ImageField | Uploaded to `media/products/` |
| badge | CharField | new / bestseller / sale / limited |
| is_available | BooleanField | Hides product if False |
| is_featured | BooleanField | Shown in hero featured section |

### `Enquiry`
| Field | Type | Notes |
|-------|------|-------|
| name | CharField | Customer name |
| phone | CharField | Customer phone |
| email | EmailField | Optional |
| message | TextField | Customer message |
| product | ForeignKey | Product enquired about (optional) |
| status | CharField | new / contacted / closed |

---

## 🐛 Troubleshooting

**`psycopg2` install error:**
```bash
pip install psycopg2-binary
```

**Static files not loading:**
```bash
python manage.py collectstatic --noinput
```

**Database connection refused:**
- Make sure PostgreSQL is running: `sudo service postgresql start`
- Check `.env` credentials match your PostgreSQL user

**Images not displaying:**
- Ensure `MEDIA_URL` and `MEDIA_ROOT` are set in `settings.py`
- In development, `urls.py` already serves media files automatically

---

## 📞 Support

**MN Ventures**
📍 Nairobi, Kenya
📱 +254 715 741 222 (WhatsApp)

---

*Built with Django, Tailwind CSS & PostgreSQL*

---

## 🔨 Auction Feature

### Overview

MN Ventures includes a full **live auction system** for new arrivals and exclusive pieces.

| Feature | Description |
|---------|-------------|
| Live countdown timer | Real-time countdown per auction, auto-closes at end time |
| Bid history | Live-updating feed of all bids (polled every 10s) |
| No login required | Bidders register with name + phone only |
| WhatsApp winner notification | Auto-generates a WhatsApp link to contact the winner |
| Reserve price | Set a hidden minimum to protect your items |
| Bid increment | Enforce a minimum raise per bid (default KSh 500) |
| Admin control | Full auction management in Django admin |
| Status automation | upcoming → live → closed handled automatically |

### Auction Flow

1. **Admin creates an auction** — links a Product, sets starting price, bid increment, start/end time
2. **Status auto-updates** — the site checks if it's time to go live or close on every page load
3. **Bidders place bids** — name + phone + amount; no account needed
4. **Countdown hits zero** — auction closes, winner is set to the highest valid bidder
5. **Winner notification** — admin sees a WhatsApp link in the admin panel and on the auction page to contact the winner directly

### Creating an Auction (Admin Panel)

1. First, create or find a **Product** and mark it as available
2. Go to **Admin → Auction Items → Add**
3. Select the product, set:
   - **Starting Price** — opening bid (KSh)
   - **Reserve Price** — optional minimum sell price (hidden from public)
   - **Bid Increment** — minimum raise per bid (e.g. KSh 500)
   - **Start Time / End Time** — schedule the auction window
4. Save — the auction will auto-activate at start time

### New Models

- **`AuctionItem`** — links a Product to an auction with pricing, schedule, and winner
- **`BidderProfile`** — lightweight bidder record (name + phone, no login)
- **`Bid`** — individual bids with amount, timestamp, and validity flag

### New URLs

| URL | View | Description |
|-----|------|-------------|
| `/auctions/` | `auction_list` | All live, upcoming, past auctions |
| `/auctions/<slug>/` | `auction_detail` | Bidding page with live countdown |
| `/auctions/<slug>/bid/` | `place_bid` | AJAX POST endpoint |
| `/auctions/<slug>/status/` | `auction_status` | JSON polling endpoint (every 10s) |


---

## 🎨 Tailwind CSS Build Pipeline

The frontend uses a **proper compiled Tailwind CSS setup** — not the CDN. This means only the utility classes actually used in the templates are included in the final CSS file (~5–15 KB instead of ~350 KB).

### File structure

```
mnventures/
├── static/
│   ├── src/
│   │   └── main.css          ← SOURCE — edit this file
│   └── store/css/
│       ├── tailwind.css      ← COMPILED — auto-generated, do not edit
│       └── custom.css        ← Hand-written extras (noise overlay, Firefox scrollbar)
├── tailwind.config.js        ← Tailwind theme, content paths, plugins
├── postcss.config.js         ← PostCSS pipeline (Tailwind + Autoprefixer)
└── package.json              ← npm scripts
```

### First-time install

```bash
# From the project root (mnventures/)
npm install
```

This installs:
- `tailwindcss` — the compiler
- `@tailwindcss/forms` — better default form styles
- `@tailwindcss/typography` — rich text (prose) styles
- `autoprefixer` — vendor-prefixes for older browsers

### Build commands

| Command | What it does |
|---------|-------------|
| `npm run dev` | Watches templates for changes and rebuilds CSS automatically |
| `npm run build` | One-time **minified** build for production |
| `npm run build:dev` | One-time **unminified** build (easier to inspect) |

### Development workflow

Run both the Django server and the Tailwind watcher simultaneously:

```bash
# Terminal 1 — Tailwind watcher
npm run dev

# Terminal 2 — Django dev server
python manage.py runserver
```

Or use the Makefile shortcut which starts both in parallel:

```bash
make dev
```

### Makefile shortcuts

```bash
make install      # pip install + npm install
make setup        # full first-time setup
make dev          # Django server + Tailwind watcher (parallel)
make build        # minified production CSS
make migrate      # run database migrations
make collect      # collectstatic
make clean        # delete compiled CSS and staticfiles/
make help         # list all commands
```

### Adding new styles

1. **Use Tailwind classes directly in templates** — Tailwind scans all files listed in `tailwind.config.js → content` and includes only those classes.
2. **Add reusable patterns** to `static/src/main.css` under `@layer components` (e.g. `.btn-primary`, `.card`).
3. **Never edit** `static/store/css/tailwind.css` — it is overwritten on every build.
4. **Hand-crafted CSS** that Tailwind cannot express (complex pseudo-elements, Firefox scrollbars) goes in `static/store/css/custom.css`.

### Customising the theme

Edit `tailwind.config.js → theme.extend` to change:
- **Brand colours** — `colors.brand.*`
- **Fonts** — `fontFamily.serif / .sans`
- **Animations** — `keyframes` and `animation`
- **Shadows** — `boxShadow`

After any change to `tailwind.config.js` or `main.css`, run `npm run build` (or let `npm run dev` rebuild automatically).

### Production deployment

```bash
# Build minified CSS
npm run build

# Collect all static files into staticfiles/
python manage.py collectstatic --noinput

# Serve with Gunicorn
gunicorn mnventures.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

> **Important:** Commit `static/store/css/tailwind.css` to your production server or run `npm run build` on the server before `collectstatic`. The file is in `.gitignore` by default to avoid merge conflicts — choose whichever approach fits your deployment pipeline.

---

## 🔐 Security Enhancements

| Issue | Fix Applied |
|-------|-------------|
| Rate limiting on bids | `RateLimitMiddleware` — 10 bids/60s per IP per auction |
| CSRF from cookie regex | `{% csrf_token %}` in base.html + meta tag; fetch() patched globally |
| Same-bidder multiple phones | Logged to `AuctionSecurityEvent`, admin can block |
| `DEBUG=True` default | Auto-disabled in production; HSTS, SSL redirect, XSS filter enabled |
| Security headers | `SecurityHeadersMiddleware` — CSP, Referrer-Policy, Permissions-Policy |
| Blocked bidder bypass | `BidderProfile.is_blocked` checked before every bid |
| Float manipulation | All amounts parsed as `Decimal`, not float |
| Race conditions | `SELECT FOR UPDATE` transaction on every bid |

---

## 💳 M-Pesa Integration (Paybill 247247, Account 741222)

### Setup

1. Register at [developer.safaricom.co.ke](https://developer.safaricom.co.ke)
2. Create an app and get: Consumer Key, Consumer Secret, Passkey
3. Add to `.env`:
```ini
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://yourdomain.com/payments/mpesa/callback/
MPESA_SANDBOX=False   # True for testing
```

### How it works
- Winner clicks "Pay Now" → STK push sent to their phone
- They enter M-Pesa PIN → Safaricom POSTs callback to `/payments/mpesa/callback/`
- Payment marked `completed`, Invoice generated automatically
- VAT (16%) split computed and stored on every payment

### Manual fallback
If STK push fails, the error message instructs the customer:
> "Pay manually: Paybill **247247**, Account **741222**"

---

## ⏰ Celery Background Tasks (Reliable Auction Closing)

### Why it's needed
Without Celery, auctions only close when someone visits the page. Celery closes them reliably every 60 seconds regardless of traffic.

### Setup

```bash
# Install and start Redis
sudo apt install redis-server
sudo systemctl start redis

# Install deps
pip install -r requirements.txt

# Run migrations (adds Celery beat tables)
python manage.py migrate

# Terminal 1 — Celery worker
make celery

# Terminal 2 — Celery beat (scheduler)
make beat

# Terminal 3 — Django dev server
make run
```

### Tasks

| Task | Schedule | What it does |
|------|----------|-------------|
| `close_expired_auctions` | Every 60s | Closes live auctions past end_time, sets winner |
| `open_upcoming_auctions` | Every 60s | Opens upcoming auctions past start_time |
| `send_winner_notification` | On close | Logs WhatsApp link to notify winner |
| `send_outbid_notification` | On outbid | Logs WhatsApp link to notify outbid bidder |

### No Redis? Use the management command
```bash
make close-auctions
# or set up a cron: */1 * * * * cd /path/to/mnventures && python manage.py close_auctions
```

---

## 🎨 Auction Integrity Features

| Feature | Detail |
|---------|--------|
| Anti-sniping | Bids in last 2 min extend auction by 2 min (max 5×) |
| Proxy bidding | Set a max bid; system auto-bids on your behalf |
| Bid cap | Max 20 bids per bidder per auction |
| Blocked bidders | Admin can block a phone number from bidding |
| SELECT FOR UPDATE | Race conditions prevented at DB level |
| Security event log | All suspicious activity recorded in `AuctionSecurityEvent` |

---

## 🌐 SEO & Infrastructure

- **Schema.org** structured data on every page (FurnitureStore type)
- **Open Graph** meta tags for WhatsApp/Facebook link previews
- **Twitter Card** meta tags
- **Canonical URLs** on every page
- **sitemap.xml** at `/sitemap.xml` (lists all products and auctions)
- **robots.txt** at `/robots.txt`
- **Placeholder images** — SVG shown when no product image uploaded (no broken images)

---

## 📄 New Pages

| URL | Page |
|-----|------|
| `/terms/` | Terms & Conditions (auction rules, VAT, returns) |
| `/privacy/` | Privacy Policy |
| `/my-bids/` | Bidder dashboard — look up bid history by phone |
| `/payments/invoice/<ref>/` | Print-ready VAT invoice |
| `/sitemap.xml` | XML sitemap |
| `/robots.txt` | Search engine instructions |
