**Дата:** 2026-04-07
**Статус:** open
**Severity:** MEDIUM

# SA-T048 — Модель не обновляется при /model switch mid-session

## Проблема

Парсер извлекает `ai_model` из первого assistant-сообщения. Если пользователь переключает модель через `/model` mid-session, парсер записывает старую модель.

**Пример:** Сессия 269d0bd4 стартовала на `claude-sonnet-4-6`, переключена на `claude-opus-4-6` через `/model`. В архиве записано `sonnet`.

## Воспроизведение

1. Начать сессию на sonnet
2. Выполнить `/model opus`
3. Продолжить работу
4. Архивировать
5. В экспорте: model = sonnet (неверно)

## Ожидаемое поведение

`ai_model` отражает модель на которой выполнена основная работа — или последнюю модель, или "multi-model" пометку.

## Рекомендация по фиксу

В JSONL при `/model` switch появляется сообщение с `local-command-stdout` содержащим `Set model to <model>`. Парсить эти сообщения и обновлять `ai_model` на последнее значение.

## Прецедент #2 — session d3dae777 (sproektirui, 2026-04-09)

Сессия стартовала на sonnet, user interrupted, переключился на opus через `/model opus` (в JSONL: `<local-command-stdout>Set model to opus (claude-opus-4-6)</local-command-stdout>`). Вся реальная работа (visual check, smoke test, deployment) выполнена на opus. В архиве записано `<synthetic>` вместо `claude-opus-4-6`. Дополнительно: тег `skill: model` добавлен ошибочно — `/model` это CLI-команда, не skill.
