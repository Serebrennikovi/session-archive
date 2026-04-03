**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T008 — Исправить domain-теги: дрейф из текста диалога

## Customer-facing инкремент

После исправления domain-теги (`frontend`, `backend`, `database`, `autodev` и т.д.) будут отражать реально изменённые файлы сессии, а не случайные слова из текста разговора. Не нужно вручную чистить теги после каждой сессии.

---

## Баги

### BUG-TAGS-CONTEXT-DRIFT — domain-теги из текста диалога

**Симптом:** После архивирования сессия получает фантомные domain-теги — например `frontend`, `database`, `tests`, `autodev`, `architecture`, `ci_cd` — хотя реально в сессии менялись только `.py` и `.md` файлы. Теги приходится удалять вручную из SQLite.

**Root cause:** `detect_domains()` сканирует `text = " ".join(m["text"] for m in messages)` — весь текст диалога. Ключевые слова (`autodev`, `frontend`, `database`) случайно встречаются в:
- тексте skill-экспансий (`/next`, `/archive-session`, `/codereview`)
- именах файлов упомянутых в разговоре
- содержимом прочитанных файлов (HANDOFF, спеки)

**Повторялось:** 13+ раз, каждый раз исправляется вручную в SQLite.

**Fix:**

Ограничить источник данных для domain-детекции — только реально изменённые файлы:

```python
def detect_domains(artifacts: list[dict]) -> list[str]:
    """Определить domains только по file_path изменённых/созданных артефактов."""
    domains = set()

    DOMAIN_RULES = {
        'frontend': [r'\.(tsx?|jsx?|css|scss|html|vue|svelte)$', r'/(components|pages|ui|views|styles)/'],
        'backend':  [r'\.(py|go|rs|rb|java|php)$', r'/(api|handlers|routes|services)/'],
        'database': [r'\.(sql|migration)$', r'/(migrations|models|schemas)/'],
        'docs':     [r'\.(md|rst|txt)$', r'/(docs|documentation)/'],
        'tests':    [r'(test_|_test\.|spec\.|\.test\.)', r'/(tests?|spec)/'],
        'ci_cd':    [r'\.(yml|yaml)$', r'/(\.github|\.gitlab|ci|deploy)/'],
    }

    for artifact in artifacts:
        if artifact.get('action') not in ('modified', 'created', 'deleted'):
            continue
        path = artifact.get('file_path', '')
        for domain, patterns in DOMAIN_RULES.items():
            if any(re.search(p, path) for p in patterns):
                domains.add(domain)

    return sorted(domains)
```

Важно: `autodev` и `architecture` не должны быть автоматическими domain-тегами — они слишком широкие и всегда появляются ложно.

---

## Scope

- Переписать `detect_domains()` в `session_archive.py`: источник — только `file_path` из `session_artifacts` с action modified/created/deleted
- Убрать text-regex поиск по тексту диалога для domain-определения
- Исключить `autodev` и `architecture` из автоматических domain-тегов (или перенести в skill-теги)

## Out of scope

- Изменение правил для skill-тегов (отдельная проблема BUG-SKILL-PHANTOM)
- Ручная разметка domain-тегов пользователем

---

## Как протестировать

1. Провести сессию с `/codereview` задачи — в тексте будут слова "autodev", "database", "frontend"
2. Запустить `/archive-session`
3. Проверить `session_tags` — domain должен соответствовать типу реально изменённых файлов
4. Провести сессию, изменяющую только `.md` файлы
5. Проверить — domain = только `docs`, нет `database`/`autodev`/`frontend`

## Критерии приёмки

1. Сессия с изменением только `.py` и `.md` → domains: `backend`, `docs` (не `autodev`, не `frontend`)
2. Сессия с изменением `.tsx` файлов → domains: `frontend`
3. Слова "autodev", "frontend", "database" в тексте диалога НЕ генерируют domain-теги
4. Теги соответствуют реальности без ручного исправления
