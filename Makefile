# =============================================================================
# АС ОУДО — Makefile
# Управление БД (Docker), приложением, документами и графикой.
# =============================================================================

PYTHON      ?= python3
VENV        ?= .venv

# На Apple Silicon принудительно используем arm64 во всех Python-вызовах,
# иначе universal-бинарь Python может выбрать x86_64-режим (через Rosetta) и
# тогда arm64-wheel'ы PyQt5/Qt5 не загрузятся (или наоборот). Префикс делает
# архитектуру детерминированной независимо от настроек терминала.
# Используем sysctl hw.optional.arm64, потому что uname -m показывает
# архитектуру _текущего процесса_, а нам нужна архитектура _машины_.
UNAME_S         := $(shell uname -s)
IS_APPLE_SILICON := $(shell sysctl -n hw.optional.arm64 2>/dev/null)
ifeq ($(UNAME_S),Darwin)
  ifeq ($(IS_APPLE_SILICON),1)
    ARCH_PREFIX := arch -arm64
  endif
endif

PIP          = $(ARCH_PREFIX) $(VENV)/bin/pip
PY           = $(ARCH_PREFIX) $(VENV)/bin/python
COMPOSE     ?= docker compose
PG_CONTAINER = ac_oudo_postgres
PG_DB       ?= ac_oudo
PG_USER     ?= postgres

SQL_FILES = \
	sql/01_schema.sql \
	sql/02_indexes.sql \
	sql/03_views.sql \
	sql/04_seed.sql

SQL_BULK = sql/06_seed_bulk.sql

.DEFAULT_GOAL := help

# -------------------------------------------------------------------- help ---
.PHONY: help
help: ## Показать список целей
	@printf "АС ОУДО — доступные цели:\n\n"
	@awk 'BEGIN { FS = ":.*##" } /^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "\nЧастые сценарии:\n"
	@printf "  make bootstrap       — поднять БД + установить зависимости + миграции\n"
	@printf "  make run             — запустить десктопное приложение\n"
	@printf "  make rpz             — собрать РПЗ.docx со всеми рисунками\n"
	@printf "  make demo            — bootstrap + run\n"

# ------------------------------------------------------------- инициализация --
.PHONY: bootstrap
bootstrap: db-up venv install db-init ## Полная подготовка стенда

.PHONY: demo
demo: bootstrap run ## bootstrap + запуск UI

# ----------------------------------------------------------------- Docker ---
.PHONY: db-up
db-up: ## Поднять PostgreSQL в Docker и дождаться готовности
	$(COMPOSE) up -d
	@echo "Жду готовности PostgreSQL…"
	@for i in $$(seq 1 30); do \
	    if $(COMPOSE) exec -T postgres pg_isready -U $(PG_USER) -d $(PG_DB) >/dev/null 2>&1; then \
	        echo "PostgreSQL готов."; exit 0; \
	    fi; sleep 1; \
	done; \
	echo "PostgreSQL не отвечает за 30 секунд"; exit 1

.PHONY: db-down
db-down: ## Остановить контейнер (данные сохраняются)
	$(COMPOSE) down

.PHONY: db-purge
db-purge: ## Полностью удалить контейнер и том с данными
	$(COMPOSE) down -v

.PHONY: db-logs
db-logs: ## Показать логи контейнера PostgreSQL
	$(COMPOSE) logs -f postgres

.PHONY: db-shell
db-shell: ## Открыть psql внутри контейнера
	$(COMPOSE) exec postgres psql -U $(PG_USER) -d $(PG_DB)

# -------------------------------------------------------------- миграции ---
.PHONY: db-init
db-init: ## Применить схему, индексы, представления и тестовые данные
	@for f in $(SQL_FILES); do \
	    echo ">>> Применяю $$f"; \
	    $(COMPOSE) exec -T postgres psql -v ON_ERROR_STOP=1 -U $(PG_USER) -d $(PG_DB) -f /$$f; \
	done

.PHONY: db-reset
db-reset: db-purge db-up db-init ## Снести том и пересоздать БД с нуля

.PHONY: db-seed-bulk
db-seed-bulk: ## Дозалить «продакшен-объём» данных (≈2 000 студентов, 100k оценок)
	$(COMPOSE) exec -T postgres psql -v ON_ERROR_STOP=1 -U $(PG_USER) -d $(PG_DB) -f /$(SQL_BULK)

.PHONY: db-explain
db-explain: ## Прогнать сценарий оптимизации запроса (EXPLAIN ANALYZE)
	$(COMPOSE) exec -T postgres psql -U $(PG_USER) -d $(PG_DB) -f /sql/05_optimize.sql | tee build/explain_output.txt

.PHONY: db-explain-bulk
db-explain-bulk: ## EXPLAIN ANALYZE на больших объёмах (после `make db-seed-bulk`)
	$(COMPOSE) exec -T postgres psql -U $(PG_USER) -d $(PG_DB) -f /sql/05_optimize.sql | tee build/explain_bulk_output.txt

# ----------------------------------------------------- Python и приложение ---
.PHONY: venv
venv: $(VENV)/bin/python ## Создать виртуальное окружение

$(VENV)/bin/python:
	$(ARCH_PREFIX) $(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip wheel

.PHONY: install
install: venv ## Установить Python-зависимости
	$(PIP) install -r requirements.txt

.PHONY: run
run: venv ## Запустить приложение АС ОУДО
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@PY_VER=$$($(PY) -c 'import sys; print(f"python{sys.version_info[0]}.{sys.version_info[1]}")') && \
	export QT_QPA_PLATFORM_PLUGIN_PATH="$(VENV)/lib/$$PY_VER/site-packages/PyQt5/Qt5/plugins/platforms" && \
	PYTHONPATH=. $(PY) -m app.main

.PHONY: smoke
smoke: venv ## Распечатать чек-лист методики испытаний
	PYTHONPATH=. $(PY) tests/test_smoke.py

# --------------------------------------------------------- документация ----
NPX            = npx --yes
MERMAID_FLAGS  = --width 2400 --backgroundColor white --theme neutral
GRAPHIC_DIR    = docs/graphics
MMD_SOURCES    = $(wildcard $(GRAPHIC_DIR)/*.mmd)
MMD_PNGS       = $(MMD_SOURCES:.mmd=.png)

.PHONY: mermaid
mermaid: $(MMD_PNGS) ## Сконвертировать все Mermaid-диаграммы в PNG

$(GRAPHIC_DIR)/%.png: $(GRAPHIC_DIR)/%.mmd
	$(NPX) -p @mermaid-js/mermaid-cli mmdc -i $< -o $@ $(MERMAID_FLAGS)

DOCS_OUT  = build
DOCX      = $(DOCS_OUT)/Воробьёв_РПЗ.docx
PDF       = $(DOCS_OUT)/Воробьёв_РПЗ.pdf
REF_DOCX  = tools/reference.docx
RPZ_SRC   = docs/00_Преамбула.md \
            docs/РПЗ.md \
            docs/Приложение_А_ТЗ.md \
            docs/Приложение_Б_Руководство_пользователя.md \
            docs/Приложение_В_Методика_испытаний.md \
            docs/Приложение_Г_Графическая_часть.md

.PHONY: placeholders
placeholders: ## Сгенерировать заглушки скриншотов через Pillow
	python3 tools/make_placeholders.py

.PHONY: screenshots
screenshots: venv install ## Снять реальные скриншоты UI через QWidget.grab()
	@PY_VER=$$($(PY) -c 'import sys; print(f"python{sys.version_info[0]}.{sys.version_info[1]}")') && \
	export QT_QPA_PLATFORM=offscreen && \
	export QT_QPA_PLATFORM_PLUGIN_PATH="$(VENV)/lib/$$PY_VER/site-packages/PyQt5/Qt5/plugins/platforms" && \
	PYTHONPATH=. $(PY) tools/make_screenshots.py

.PHONY: reference
reference: venv install ## Сгенерировать tools/reference.docx со стилями ГОСТ
	$(PY) tools/build_reference_docx.py

.PHONY: rpz
rpz: mermaid screenshots $(REF_DOCX) $(DOCX) ## Собрать РПЗ.docx со всеми рисунками

$(REF_DOCX): tools/build_reference_docx.py
	$(PY) tools/build_reference_docx.py

$(DOCX): $(RPZ_SRC) $(MMD_PNGS) $(REF_DOCX) tools/fixup_docx_tables.py
	@mkdir -p $(DOCS_OUT)
	pandoc $(RPZ_SRC) \
	    --resource-path=docs:. \
	    --reference-doc=$(REF_DOCX) \
	    --from=markdown+pipe_tables+grid_tables+yaml_metadata_block+raw_html+fenced_divs+raw_attribute \
	    --to=docx \
	    --syntax-highlighting=monochrome \
	    --columns=200 \
	    --metadata lang="ru-RU" \
	    --output $(DOCX)
	$(PY) tools/fixup_docx_tables.py $(DOCX)
	@echo "Готово: $(DOCX)"

.PHONY: rpz-pdf
rpz-pdf: mermaid $(PDF) ## Собрать РПЗ.pdf (требует LaTeX)

$(PDF): $(RPZ_SRC) $(MMD_PNGS)
	@mkdir -p $(DOCS_OUT)
	pandoc $(RPZ_SRC) \
	    --resource-path=docs:. \
	    --pdf-engine=xelatex \
	    -V mainfont="Times New Roman" \
	    -V geometry:margin=20mm \
	    -V lang=ru \
	    --toc --toc-depth=3 \
	    --output $(PDF)

# ----------------------------------------------------------- утилитарное ---
.PHONY: clean
clean: ## Удалить кэш Python
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf $(DOCS_OUT)

.PHONY: clean-all
clean-all: clean db-purge ## clean + удалить .venv и Docker-том
	rm -rf $(VENV)

.PHONY: status
status: ## Показать статус БД и приложения
	@echo "=== Docker ==="
	@$(COMPOSE) ps
	@echo
	@echo "=== Размер БД ==="
	@$(COMPOSE) exec -T postgres psql -U $(PG_USER) -d $(PG_DB) -c \
	    "SELECT relname AS table, n_live_tup AS rows FROM pg_stat_user_tables ORDER BY relname;"
