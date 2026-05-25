.PHONY: install dev build migrate superuser run watch collect clean help celery beat

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Setup ─────────────────────────────────────────────────
install: ## Install Python + Node deps
	pip install -r requirements.txt
	npm install

setup: install migrate superuser build collect ## Full first-time setup
	@echo "✅  Setup complete! Run: make dev"

# ── Development ───────────────────────────────────────────
dev: ## Django + Tailwind watcher (parallel)
	@trap 'kill 0' SIGINT; npm run dev & python manage.py runserver & wait

run: ## Django dev server only
	python manage.py runserver

watch: ## Tailwind CSS watcher only
	npm run dev

celery: ## Start Celery worker (requires Redis)
	celery -A mnventures worker -l info

beat: ## Start Celery beat scheduler (closes auctions on time)
	celery -A mnventures beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# ── Build ─────────────────────────────────────────────────
build: ## Minified production CSS
	npm run build

build-dev: ## Unminified CSS (for debugging)
	npm run build:dev

collect: ## Collect Django static files
	python manage.py collectstatic --noinput

# ── Database ──────────────────────────────────────────────
migrate: ## Run all migrations
	python manage.py migrate

migrations: ## Create new migrations
	python manage.py makemigrations

superuser: ## Create Django admin superuser
	python manage.py createsuperuser

# ── Maintenance ───────────────────────────────────────────
clean: ## Remove compiled CSS and staticfiles
	rm -f static/store/css/tailwind.css
	rm -rf staticfiles/

shell: ## Django shell
	python manage.py shell

close-auctions: ## Manually close expired auctions (use if Celery not running)
	python manage.py close_auctions
