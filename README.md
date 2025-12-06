# Payouts Management Service

REST API сервис для управления заявками на выплату средств с асинхронной обработкой через Celery.

## Технологический стек

- Python 3.10+
- Django 4.2+
- Django REST Framework
- Celery + Redis
- PostgreSQL
- Poetry (управление зависимостями)
- Docker & docker-compose

## Быстрый старт

### Предварительные требования

- Python 3.10+
- Poetry
- PostgreSQL
- Redis
- Docker и docker-compose (опционально)

### Установка зависимостей

```bash
make install
# или
poetry install
```

### Настройка окружения

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=payouts_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Запуск миграций

```bash
make migrate
# или
poetry run python manage.py migrate
```

### Запуск сервиса

В одном терминале запустите Django сервер:

```bash
make run
# или
poetry run python manage.py runserver
```

В другом терминале запустите Celery worker:

```bash
make worker
# или
poetry run celery -A config worker --loglevel=info
```

### Запуск тестов

```bash
make test
# или
poetry run pytest
```

## Использование Docker

### Запуск всех сервисов

```bash
make docker-up
```

Это запустит:
- PostgreSQL (порт 5432)
- Redis (порт 6379)
- Django web сервер (порт 8000)
- Celery worker

### Остановка сервисов

```bash
make docker-down
```

### Выполнение миграций в Docker

```bash
docker-compose exec web python manage.py migrate
```

## API Endpoints

### Базовый URL
```
http://localhost:8000/api/
```

### Доступные endpoints:

- `GET /api/payouts/` - Список всех заявок
- `GET /api/payouts/{id}/` - Получение заявки по ID
- `POST /api/payouts/` - Создание новой заявки
- `PATCH /api/payouts/{id}/` - Частичное обновление заявки (в основном статус)
- `DELETE /api/payouts/{id}/` - Удаление заявки

### API Документация

После запуска сервера доступна интерактивная документация:
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

### Пример создания заявки

```bash
curl -X POST http://localhost:8000/api/payouts/ \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "100.50",
    "currency": "USD",
    "recipient_details": "John Doe, Account: 1234567890",
    "description": "Monthly payment"
  }'
```

## Модель данных

Заявка на выплату (Payout) содержит следующие поля:

- `id` (UUID) - Уникальный идентификатор
- `amount` (Decimal) - Сумма выплаты
- `currency` (String, 3 символа) - Валюта (USD, EUR, etc.)
- `recipient_details` (Text) - Реквизиты получателя
- `status` (String) - Статус заявки (pending, processing, completed, failed, cancelled)
- `description` (Text, опционально) - Описание или комментарий
- `created_at` (DateTime) - Дата создания
- `updated_at` (DateTime) - Дата обновления

## Валидация

При создании заявки проверяется:

- Обязательность полей (amount, currency, recipient_details)
- Положительность суммы
- Формат валюты (3 буквы)
- Длина строковых полей (recipient_details до 1000 символов, description до 2000)

## Асинхронная обработка

При создании заявки автоматически запускается Celery задача `process_payout_task`, которая:

1. Обновляет статус заявки на "processing"
2. Имитирует обработку (задержка, проверки)
3. Обновляет статус на "completed" или "failed" в зависимости от результата

## Тестирование

Минимальный набор тестов включает:

- Тест успешного создания заявки
- Тест проверки вызова Celery-задачи при создании (через mock)
- Тесты валидации
- Тесты CRUD операций

Запуск тестов:

```bash
make test
```

## Развёртывание в production

### Архитектура

Для production окружения рекомендуется следующая архитектура:

1. **Web сервер**: Django приложение запускается через Gunicorn или uWSGI за reverse proxy (Nginx)
2. **База данных**: PostgreSQL на отдельном сервере или managed service
3. **Брокер сообщений**: Redis или RabbitMQ для Celery
4. **Celery workers**: Отдельные процессы/контейнеры для обработки задач
5. **Мониторинг**: Логирование, метрики, health checks

### Необходимые сервисы

- PostgreSQL (база данных)
- Redis (брокер для Celery)
- Nginx (reverse proxy, опционально)
- Gunicorn/uWSGI (WSGI сервер)
- Supervisor/systemd (управление процессами)

### Пример запуска в production

```bash
# Запуск Django через Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Запуск Celery worker
celery -A config worker --loglevel=info --concurrency=4

# Запуск Celery beat (если нужны периодические задачи)
celery -A config beat --loglevel=info
```

### Минимальные шаги подготовки окружения

1. Установить зависимости: `poetry install --no-dev`
2. Настроить переменные окружения (SECRET_KEY, DB credentials, etc.)
3. Выполнить миграции: `python manage.py migrate`
4. Собрать статические файлы: `python manage.py collectstatic`
5. Запустить сервисы (web, worker, redis, postgres)

### Рекомендации

- Использовать environment variables для конфигурации
- Настроить логирование
- Использовать SSL/TLS для API
- Настроить rate limiting
- Регулярные бэкапы базы данных
- Мониторинг и алертинг

## Дополнительные команды

```bash
make lint      # Проверка кода линтерами
make format    # Форматирование кода
make shell     # Django shell
make superuser # Создание суперпользователя
```

## Структура проекта

```
test_smart_collect/
├── config/          # Настройки Django проекта
├── payouts/         # Приложение для работы с заявками
│   ├── models.py    # Модель Payout
│   ├── serializers.py
│   ├── views.py     # ViewSet для API
│   ├── urls.py      # URL маршруты
│   ├── tasks.py     # Celery задачи
│   └── tests.py     # Тесты
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
```

## Лицензия

Это тестовое задание.

