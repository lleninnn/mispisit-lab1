import sys
import os
import time
from django.conf import settings
from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.management import execute_from_command_line
from django.db import models, connection
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. КОНФИГУРАЦИЯ И ПОДКЛЮЧЕНИЕ К БД
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='lab3-postgres-secret-key',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        INSTALLED_APPS=[
            __name__,
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME', 'fraud_db'),
                'USER': os.environ.get('DB_USER', 'postgres'),
                'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
                'HOST': os.environ.get('DB_HOST', 'localhost'),
                'PORT': os.environ.get('DB_PORT', '5432'),
            }
        },
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
        }],
    )

django.setup()


# 2. ОПРЕДЕЛЕНИЕ МОДЕЛИ ДАННЫХ
class Transaction(models.Model):
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    sender = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='На проверке')

    class Meta:
        managed = False  # Отключаем миграции Django для этой модели
        db_table = 'transactions'


# 3. ИНИЦИАЛИЗАЦИЯ ТАБЛИЦЫ (Защищенный метод)
def init_db():
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    amount NUMERIC(15, 2) NOT NULL,
                    sender VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL
                )
            ''')
            # Добавим тестовую запись, если таблица пуста
            cursor.execute('SELECT COUNT(*) FROM transactions')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO transactions (amount, sender, status) 
                    VALUES (950000, 'ООО "Вектор"', 'Фрод')
                ''')
    except Exception as e:
        print(f"Ожидание базы данных... ({e})")


# Запускаем инициализацию при старте
init_db()


# 4. ПРЕДСТАВЛЕНИЯ (VIEWS)
def index(request):
    return render(request, 'index.html')


def transaction_list(request):
    # Получаем все записи из БД
    transactions = Transaction.objects.all().order_by('-id')
    return render(request, 'transaction_list.html', {'transactions': transactions})


def transaction_new(request):
    if request.method == 'POST':
        # Сохраняем новую запись в PostgreSQL
        Transaction.objects.create(
            amount=request.POST.get('amount'),
            sender=request.POST.get('sender'),
            status='На проверке'
        )
        return HttpResponseRedirect('/transactions/')
    return render(request, 'transaction_form.html')


def transaction_detail(request, tx_id):
    try:
        tx = Transaction.objects.get(id=tx_id)
    except Transaction.DoesNotExist:
        return HttpResponseRedirect('/transactions/')

    if tx.status in ['Фрод', 'Ок']:
        return render(request, 'access_denied.html')

    return render(request, 'transaction_detail.html', {'tx': tx})


# 5. МАРШРУТЫ (URLS)
urlpatterns = [
    path('', index),
    path('transactions/', transaction_list),
    path('transactions/new/', transaction_new),
    path('transactions/<int:tx_id>/', transaction_detail),
]

if __name__ == '__main__':
    execute_from_command_line(sys.argv)