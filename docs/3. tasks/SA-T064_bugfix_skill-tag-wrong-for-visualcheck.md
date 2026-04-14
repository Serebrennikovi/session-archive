**Дата:** 2026-04-09
**Статус:** draft

# SA-T064 — Skill tags: `/visualcheck` → `codereview`/`codereview-local` вместо `visualcheck`

## Проблема

Сессия, в которой пользователь вызвал `/visualcheck`, получила теги `skill: codereview` и `skill: codereview-local` вместо `skill: visualcheck`. `domain` = `docs` вместо `ui`.

Прецедент: сессия `c52bd9af` (sproektirui, 2026-04-09). Пользователь вызвал `t147 /visualcheck`, агент выполнил Playwright visual check с 14 скриншотами. В архиве — только кодревью теги.

## Root cause (предположение)

Детектор skill-тегов, скорее всего, читает контент шаблона `visualcheck`. Этот шаблон содержит упоминание `/codereview` (например, «аналогично `/codereview`» или ссылки на формат находок), и детектор подхватывает `codereview` и `codereview-local` как якобы использованные скиллы.

Смежный баг: SA-T061 (skill-tag-from-interrupted-invocation), SA-T024 (skill-detection-command-message).

## Как воспроизвести

1. Вызвать `/visualcheck` в сессии
2. Убедиться, что `/codereview` и `/codereview-local` в сессии не вызывались
3. Запустить `archive-current` — в `session_tags` появятся `skill: codereview` и `skill: codereview-local`

## Acceptance Criteria

- [ ] Skill-тег = только вызванный через Skill tool скилл (`visualcheck`)
- [ ] Упоминания других скиллов в тексте шаблона не порождают skill-теги
- [ ] `domain: ui` для сессий с Playwright / visual check (не `docs`)
- [ ] Регрессионный тест: сессия с `/visualcheck` → tags содержит только `visualcheck` + `playwright`
