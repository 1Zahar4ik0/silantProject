Создайте базу `silant`. Подключение: `127.0.0.1:5432`, пользователь `postgres`.

Первый запуск:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:POSTGRES_PASSWORD = 'ваш пароль PostgreSQL'
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py import_source
.\.venv\Scripts\python manage.py create_demo_users
.\.venv\Scripts\python manage.py runserver
```

Сайт: http://127.0.0.1:8000/ . Логины и пароли создаются командой `create_demo_users` и сохраняются в `.local-credentials.txt`.

Повторный запуск:

```powershell
$env:POSTGRES_PASSWORD = 'ваш пароль PostgreSQL'
.\.venv\Scripts\python manage.py runserver
```

