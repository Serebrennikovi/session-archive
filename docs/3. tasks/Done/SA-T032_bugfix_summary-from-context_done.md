**Дата:** 2026-04-03
**Статус:** done
**Завершено:** 2026-04-03
**Спецификация:** —

# SA-T032 — Исправить Summary: извлечение из контекста вместо фактического outcome

## Customer-facing инкремент

После архивирования сессии `## Summary` будет отражать реальный результат работы — что было сделано, какие задачи закрыты — а не пересказ первого сообщения пользователя или ссылки на HANDOFF.

---

## Баги

### BUG-SUMMARY-FROM-CONTEXT — Summary генерируется из начала диалога

**Симптом:** `summary` в БД и `## Summary` в markdown-экспорте содержат:
- Пересказ первого запроса пользователя (`$intro`, `$codereview T145`)
- Ссылки на задачи из HANDOFF, которые только читались, а не выполнялись (`T022`, `T139`, `T140`, `T141`)
- Meta-фразы про verify-archive / session-archive из конца диалога
- Куски итогового ответа ассистента, не являющиеся summary

Примеры из сессий:
- `019d4f8b`: `summary` склеился из goal + refs + длинного outcome, притянул `T022`/`ADV-S03`
- `019d4fa5`: `Summary` = первый запрос `$intro` + ссылки на задачи из HANDOFF + meta-фраза про verify-archive
- `019d51be`: `Summary` = исходный запрос + ссылки на T139–T146 + meta-фраза про verify/archive

**Повторялось:** 3+ раза, в каждой сессии где был `$intro` или чтение HANDOFF.

**Fix (реализовано):**

В `build_summary` добавлена очистка goal-строки от meta-management слов через `_SUMMARY_META_WORDS` regex:

```python
_SUMMARY_META_WORDS = re.compile(
    r'\b(verify-archive|archive-session|archive-current|session-archive)\b',
    re.IGNORECASE,
)

# В build_summary:
if goal:
    goal = _SUMMARY_META_WORDS.sub("", goal).strip(" .,;")
```

Это удаляет ссылки на архивирование из goal-части summary. Outcome-часть summary уже защищена через `_is_meta_outcome()` (добавлено ранее).

---

## Scope

- ✅ Добавить фильтр meta-фраз в `build_summary` (goal)
- Outcome-часть (`_is_meta_outcome`) уже работает корректно

## Out of scope

- Переписывать уже сохранённые summary в БД (только новые архивации)
- ML-классификация outcome vs context
- Полная замена `_select_goal` на outcome-приоритет (архитектурное изменение → SA-T029)

---

## Критерии приёмки

1. ✅ Summary не содержит слова `verify-archive`, `archive-session`, `archive-current`
2. ✅ `--summary` аргумент → используется verbatim, не перезаписывается (уже работало)
