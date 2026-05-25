# 🤝 MN Ventures — Partner Programme Add-on

A plug-and-play Django app that adds a full **partner/seller registration and design
submission** system to the existing MN Ventures website.

---

## 📦 What's Included

| File | Purpose |
|------|---------|
| `partners/models.py` | `PartnerApplication` + `DesignSubmission` database models |
| `partners/forms.py` | Registration and design brief forms |
| `partners/views.py` | Public + staff-only views |
| `partners/urls.py` | URL routes (namespaced `partners:`) |
| `partners/admin.py` | Customised Django admin with coloured status badges |
| `partners/migrations/` | Database migration — run once |
| `partners/templates/partners/` | 7 templates matching MN Ventures amber theme |

---

## 🚀 Installation (3 steps)

### Step 1 — Copy the app folder

Place the entire `partners/` directory alongside `store/`:

```
mnventures/
├── manage.py
├── store/            ← existing app
├── partners/         ← NEW — copy here
└── mnventures/
    ├── settings.py
    └── urls.py
```

---

### Step 2 — Register the app and wire up URLs

**`mnventures/settings.py`** — add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'store',
    'partners',          # ← add this
]
```

Also confirm these are already set (they should be from the base project):

```python
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

**`mnventures/urls.py`** — include the partner URLs:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('partners/', include('partners.urls')),   # ← add this line
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

### Step 3 — Run the migration

```bash
python manage.py migrate
```

That's it. The feature is live.

---

## 🌐 URLs Created

### Public-facing

| URL | Page |
|-----|------|
| `/partners/become-a-partner/` | Landing page + registration form |
| `/partners/become-a-partner/done/` | Application success confirmation |
| `/partners/submit-design/` | Design brief submission (approved partners only) |
| `/partners/submit-design/done/` | Submission success confirmation |

### Staff-only (requires `is_staff=True`)

| URL | Page |
|-----|------|
| `/partners/staff/partners/` | Dashboard — all applications + submissions |
| `/partners/staff/partners/application/<id>/` | Application detail + approve/reject/hold |
| `/partners/staff/partners/submission/<id>/` | Submission detail + workshop status management |

### Django Admin

`/admin/partners/` — full CRUD for both models with inline design submissions.

---

## 🔗 Link From the Main Site

Add a "Become a Partner" link to your existing `base.html` navbar:

```html
<!-- Inside the navbar in store/templates/store/base.html -->
<a href="{% url 'partners:become_partner' %}"
   class="text-amber-400 hover:text-amber-300 font-semibold transition-colors">
  Become a Partner
</a>
```

Or add a banner/section on the homepage (`home.html`):

```html
<!-- Partner CTA section — add near the bottom of home.html -->
<section class="bg-amber-900 text-white py-14 px-4 text-center">
  <h2 class="font-display text-3xl font-bold mb-3">Are You a Designer or Contractor?</h2>
  <p class="text-amber-200 mb-6 max-w-xl mx-auto">
    Join the MN Ventures Partner Programme — exclusive pricing, priority production,
    and a dedicated workshop team for your client projects.
  </p>
  <a href="{% url 'partners:become_partner' %}"
     class="inline-block bg-amber-400 hover:bg-amber-300 text-amber-900 font-bold px-8 py-3 rounded-xl transition-colors">
    Apply to Become a Partner →
  </a>
</section>
```

---

## 👷 Workflow: How It All Works

```
1. PARTNER APPLIES
   /partners/become-a-partner/
   → Submits name, business, county, town, mobile, WhatsApp, clients/month
   → Stored as PartnerApplication (status: pending)

2. ADMIN REVIEWS
   /partners/staff/partners/  (or Django admin)
   → Sees all pending applications
   → Clicks "Approve" → partner_code generated (e.g. MNV-MWA-48291)
   → Sets their discount % (default 10%)
   → Contacts partner via WhatsApp one-click link

3. PARTNER SUBMITS DESIGN
   /partners/submit-design/
   → Enters approved email to verify identity
   → Fills project title, type, site location, description
   → Sets start date, completion date, priority, budget range
   → Uploads up to 3 design files (PDF, DWG, JPG, PNG)

4. WORKSHOP ACTS
   /partners/staff/partners/submission/<id>/
   → Admin changes workshop_status: Submitted → Reviewing → Quoted → In Progress → Completed
   → Assigns to a named workshop staff member
   → Records quoted amount
   → Adds internal workshop notes
   → WhatsApp partner directly from the detail page
```

---

## 🗄️ Database Models

### `PartnerApplication`

| Field | Type | Notes |
|-------|------|-------|
| full_name | CharField | Contact person |
| business_name | CharField | Company name |
| business_type | CharField | interior_designer / contractor / architect / retailer / property_developer / other |
| email | EmailField | Unique — used to verify on design portal |
| mobile | CharField | |
| whatsapp | CharField | Optional — defaults to mobile |
| county | CharField | Kenya county |
| town | CharField | Town / estate |
| address_details | TextField | Optional extra address |
| approximate_clients | CharField | e.g. "5–10 per month" |
| message | TextField | About their business |
| status | CharField | pending / approved / rejected / on_hold |
| partner_code | CharField | Auto-generated on approval e.g. MNV-ABC-12345 |
| discount_percent | PositiveSmallIntegerField | e.g. 10 |
| admin_notes | TextField | Internal notes |
| submitted_at | DateTimeField | Auto |
| reviewed_at | DateTimeField | Set on action |

### `DesignSubmission`

| Field | Type | Notes |
|-------|------|-------|
| partner | ForeignKey | Links to PartnerApplication |
| project_title | CharField | e.g. "Karen Villa Master Bedroom" |
| project_type | CharField | cabinet / furniture / construction / office / kitchen / bedroom / other |
| description | TextField | Full scope of work |
| site_location | CharField | e.g. "Karen, Nairobi" |
| expected_start_date | DateField | |
| expected_completion_date | DateField | |
| priority | CharField | standard / urgent / flexible |
| budget_range | CharField | e.g. "150,000 – 300,000" |
| design_file_1/2/3 | FileField | Uploaded to `media/partner_designs/<partner_id>/` |
| workshop_status | CharField | submitted → reviewing → quoted → in_progress → completed / cancelled |
| admin_notes | TextField | Workshop notes |
| quoted_amount | DecimalField | KSh |
| assigned_to | CharField | Workshop staff name |
| submitted_at / updated_at | DateTimeField | Auto |

---

## 📁 Uploaded Files Location

Design files are stored at:
```
media/
└── partner_designs/
    └── <partner_id>/
        ├── floor-plan.pdf
        ├── elevation.jpg
        └── cabinet-detail.dwg
```

Set a 20 MB upload limit in `settings.py` (optional but recommended):
```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024   # 20 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024   # 20 MB
```

---

## 🔒 Security Notes

- Staff dashboard (`/partners/staff/…`) is protected by `@staff_member_required` — only users with `is_staff=True` in Django admin can access it.
- Design submissions are gated: a partner must have `status="approved"` to submit.
- CSRF protection is active on all forms.
- No public registration of login credentials — verification is email-based and human-reviewed.

---

## ✅ Checklist After Installation

- [ ] `python manage.py migrate` completed without errors
- [ ] `'partners'` added to `INSTALLED_APPS`
- [ ] `path('partners/', include('partners.urls'))` added to `mnventures/urls.py`
- [ ] "Become a Partner" link added to navbar or homepage
- [ ] Superuser can access `/partners/staff/partners/`
- [ ] Test application submitted at `/partners/become-a-partner/`
- [ ] Test application approved via staff dashboard
- [ ] Test design upload at `/partners/submit-design/?email=<approved_email>`
