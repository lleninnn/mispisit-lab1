import sys
import os
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.management import execute_from_command_line
from django.db import models, connection
from django.db.models import Sum
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. КОНФИГУРАЦИЯ И ПОДКЛЮЧЕНИЕ К БД
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY=os.environ.get('SECRET_KEY', 'default-insecure-dev-key'),
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        INSTALLED_APPS=[
            __name__,
            'django.contrib.staticfiles',
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
        STATIC_URL='/static/',
        STATICFILES_DIRS=[
            os.path.join(BASE_DIR, 'static'),
        ],
    )

django.setup()

# 2. МОДЕЛЬ ДАННЫХ
class Transaction(models.Model):
    """Модель финансовой транзакции для фрод-мониторинга."""
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    sender = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='На проверке')

    class Meta:
        managed = False
        db_table = 'transactions'

# 3. ИНИЦИАЛИЗАЦИЯ ТАБЛИЦЫ
def init_db():
    """Создаёт таблицу транзакций при старте, если она ещё не существует."""
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
    except Exception as e:
        print(f"[ Warning ] Не удалось инициализировать таблицу transactions: {e}")

init_db()

# 4. ПРЕДСТАВЛЕНИЯ (VIEWS)
def index(request):
    """Главная страница: аналитический дашборд приложения."""
    try:
        total_count = Transaction.objects.count()
        fraud_count = Transaction.objects.filter(status='Фрод').count()
        ok_count = Transaction.objects.filter(status='Ок').count()
        pending_count = Transaction.objects.filter(status='На проверке').count()
        total_amount = Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        recent_txs = Transaction.objects.all().order_by('-id')[:5]
    except Exception:
        total_count = fraud_count = ok_count = pending_count = 0
        total_amount = Decimal('0.00')
        recent_txs = []

    context = {
        'total_count': total_count,
        'fraud_count': fraud_count,
        'ok_count': ok_count,
        'pending_count': pending_count,
        'total_amount': total_amount,
        'recent_txs': recent_txs,
        'version': '0.0.4'
    }
    return render(request, 'index.html', context)

def transaction_list(request):
    """Реестр всех транзакций."""
    transactions = Transaction.objects.all().order_by('-id')
    return render(request, 'transaction_list.html', {'transactions': transactions})

def transaction_new(request):
    """Форма регистрации новой транзакции с валидацией данных."""
    error = None
    if request.method == 'POST':
        raw_amount = request.POST.get('amount', '').strip()
        sender = request.POST.get('sender', '').strip()

        try:
            amount = Decimal(raw_amount)
            if amount <= 0:
                raise InvalidOperation
            if not sender:
                error = "Укажите наименование отправителя."
            else:
                Transaction.objects.create(
                    amount=amount,
                    sender=sender,
                    status='На проверке'
                )
                return HttpResponseRedirect('/transactions/')
        except InvalidOperation:
            error = "Введите корректную положительную сумму (например: 15000.50)."

    return render(request, 'transaction_form.html', {'error': error})

def transaction_detail(request, tx_id):
    """Карточка проверки транзакции и вынесения вердикта аналитиком."""
    try:
        tx = Transaction.objects.get(id=tx_id)
    except Transaction.DoesNotExist:
        return HttpResponseRedirect('/transactions/')

    if tx.status in ['Фрод', 'Ок']:
        return render(request, 'access_denied.html', {'tx': tx})

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Фрод', 'Ок']:
            tx.status = new_status
            tx.save()
            return HttpResponseRedirect('/transactions/')

    return render(request, 'transaction_detail.html', {'tx': tx})

def access_denied(request):
    """Отдельная страница ошибочного сценария."""
    return render(request, 'access_denied.html', {})

# 5. МАРШРУТЫ (URLS)
urlpatterns = [
    path('', index),
    path('transactions/', transaction_list),
    path('transactions/new/', transaction_new),
    path('transactions/<int:tx_id>/', transaction_detail),
    path('access-denied/', access_denied),
]

if __name__ == '__main__':
    execute_from_command_line(sys.argv)