**Дата:** 2026-04-09
**Статус:** draft

# SA-T067 — Skill tag: последний вызванный скилл перебивает основной

## Проблема

Сессия sproektirui `b721c44b` (2026-04-09): основная работа — `/smoketest` (большая часть сессии, Playwright, деплой). В конце вызван `/archive-session`. Результат: `skill: archive-session` вместо `skill: smoketest`.

## Root cause

Детектор, по всей видимости, берёт последний обнаруженный скилл или перезаписывает предыдущий. `/archive-session` вызывается в конце любой сессии, поэтому систематически перекрывает реальный skill.

Смежный баг: SA-T064 (skill-tag-wrong-for-visualcheck — там тоже `/archive-session` и `/verify-archive` вызывались после основного скилла).

## Как воспроизвести

1. Вести сессию с основным скиллом X (`/smoketest`, `/codereview`, `/visualcheck`)
2. В конце вызвать `/archive-session` и/или `/verify-archive`
3. Проверить skill-тег → будет `archive-session` вместо X

## Acceptance Criteria

- [ ] skill-тег = скилл с наибольшим весом/объёмом работы в сессии, не последний вызванный
- [ ] `/archive-session` и `/verify-archive` помечаются как `utility` и не конкурируют с основным skill
- [ ] Если в сессии X = smoketest (основной) + archive-session (утилита) → skill: smoketest
- [ ] Регрессионный тест: smoketest-сессия с архивацией в конце → skill: smoketest

## Рекомендация по fix

Исключить `archive-session` и `verify-archive` из конкурирующего набора skill-тегов. Они — вспомогательные утилиты, не основная работа сессии. Можно хранить как отдельный тег `utility: archive-session`.
