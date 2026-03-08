# Production Control API

Backend-сервис для управления производственными партиями и агрегацией продуктов.

Проект реализован на **FastAPI + Async SQLAlchemy + PostgreSQL**  
с архитектурой **Service / Repository / Unit of Work** и запускается через **Docker**.

---

# Технологический стек

- Python 3.11
- FastAPI
- Async SQLAlchemy
- PostgreSQL
- Docker / Docker Compose
- Redis
- RabbitMQ

---

# Возможности API

Сервис позволяет:

- создавать производственные партии
- получать список партий
- получать партию по ID
- обновлять данные партии
- агрегировать продукты внутри партии

---

# Архитектура проекта

Проект построен по многоуровневой архитектуре:

**API layer**  
обрабатывает HTTP запросы (FastAPI routers)

**Service layer**  
содержит бизнес-логику приложения

**Repository layer**  
отвечает за взаимодействие с базой данных

**Unit of Work**  
управляет транзакциями и жизненным циклом репозиториев

---

# Структура проекта


```production-control/
├── app/
│   ├── api/            # FastAPI роуты
│   ├── models/         # SQLAlchemy модели
│   ├── repositories/   # работа с базой данных
│   ├── services/       # бизнес-логика
│   ├── schemas/        # Pydantic схемы
│   ├── uow.py          # Unit of Work
│   └── main.py         # запуск FastAPI
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md```