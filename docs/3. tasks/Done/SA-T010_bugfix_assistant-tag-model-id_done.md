**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T010 — Исправить assistant/model теги: захардкожен "claude"

## Customer-facing инкремент

После исправления поле `assistant` в тегах и `ai_model` в sessions будет содержать реальный model ID (`claude-sonnet-4-6`, `claude-opus-4-6` и т.д.) вместо заглушки `claude`. Не нужно вручную исправлять model после каждой архивации.

---

## Баги

### BUG-ASSISTANT-TAG-VALUE — `assistant` тег захардкожен как "claude"

**Симптом:** В `session_tags` запись `(category='assistant', value='claude')` вместо `(category='assistant', value='claude-sonnet-4-6')`. Поле `ai_model` в таблице `sessions` также пишется как `claude`. При этом поле `model` в JSONL содержит полный model ID.

**Root cause:** `_build_metadata()` содержит захардкоженное значение:
```python
tags.append({'category': 'assistant', 'value': 'claude'})
```
Вместо извлечения model ID из JSONL-сообщений. JSONL assistant-сообщения содержат поле `model` с полным ID.

**Повторялось:** 5+ раз в последних сессиях (каждый раз исправляется вручную).

**Fix:**

```python
def extract_model_id(messages: list[dict]) -> str:
    """Извлечь model ID из первого assistant-сообщения с полем model."""
    for msg in messages:
        if msg.get('role') == 'assistant':
            model = msg.get('model', '')
            if model and model != 'claude':  # не заглушка
                return model
    return 'claude'  # fallback если не найдено

# В _build_metadata():
model_id = extract_model_id(messages)
tags.append({'category': 'assistant', 'value': model_id})
tags.append({'category': 'model', 'value': model_id})
session_data['ai_model'] = model_id
```

Для Codex JSONL — аналогично: искать поле `model` в metadata-блоке.

---

## Scope

- В `session_archive.py`: добавить `extract_model_id(messages)` для парсинга model из JSONL
- Заменить захардкоженный `'claude'` на результат вызова функции в `_build_metadata()`
- Обновить `ai_model` в таблице `sessions` из того же источника
- Синхронизировать `session_tags.model` и `sessions.ai_model` (один источник)

## Out of scope

- Ретроактивное исправление старых записей в БД
- Поддержка мультимодельных сессий (когда в одной сессии используется >1 модели)

---

## Как протестировать

1. Запустить `/archive-session` для любой Claude-сессии
2. Проверить `sessions.ai_model` — должно быть `claude-sonnet-4-6` (или актуальный model ID)
3. Проверить `session_tags` — запись `(assistant, claude-sonnet-4-6)` и `(model, claude-sonnet-4-6)`
4. Проверить export MD — `| Model | claude-sonnet-4-6 |`

## Критерии приёмки

1. `sessions.ai_model` = `claude-sonnet-4-6` без ручного исправления
2. `session_tags`: `assistant` и `model` совпадают и не равны `claude` (для claude-sonnet сессий)
3. Export MD показывает корректный model ID в таблице метаданных
4. Codex-сессии показывают корректный Codex model ID
