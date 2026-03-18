# Production Control API

Веб-приложение для управления сменными заданиями на производстве с асинхронной обработкой задач, импортом/экспортом, файловым хранилищем и внешними интеграциями.

## Возможности

- управление рабочими центрами
- создание и обновление партий
- привязка изделий к партиям
- синхронная и асинхронная агрегация изделий
- импорт партий из CSV / Excel
- экспорт партий в Excel
- генерация отчетов
- webhook-интеграции
- аналитика по партиям
- мониторинг Celery через Flower

## Стек

### Backend
- Python 3.11
- FastAPI
- SQLAlchemy 2.0 Async
- Pydantic v2

### База данных
- PostgreSQL 16
- Alembic

### Асинхронные задачи
- Celery
- RabbitMQ
- Redis
- Celery Beat
- Flower

### Хранилище
- MinIO

### Инфраструктура
- Docker
- Docker Compose

## Структура проекта

```text
app/
  api/v1/             # роутеры API
  repositories/       # работа с БД
  services/           # бизнес-логика
  schemas/            # Pydantic-схемы
  tasks/              # Celery tasks
  storage/            # MinIO
  migrations/         # Alembic migrations
  main.py             # FastAPI app
  database.py         # engine/session
  routes.py           # общий роутер

tests/
  test_health.py
  test_analytics.py