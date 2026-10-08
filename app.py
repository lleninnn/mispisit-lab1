import sys
import os
from django.conf import settings
from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.management import execute_from_command_line

# Настройки Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='lab2-secret-key',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
        }],
    )

# Эмуляция базы данных в памяти
db_transactions = [
    {'id': 1, 'amount': 15000, 'sender': 'Иванов И.И.', 'status': 'На проверке'},
    {'id': 2, 'amount': 950000, 'sender': 'ООО "Вектор"', 'status': 'Фрод'},
]


# --- ПРЕДСТАВЛЕНИЯ (VIEWS) ---

def index(request):
    return render(request, 'index.html')


# Функция 1: Просмотр списка
def transaction_list(request):
    return render(request, 'transaction_list.html', {'transactions': db_transactions})


# Функция 2: Создание новой транзакции
def transaction_new(request):
    if request.method == 'POST':
        new_id = max([t['id'] for t in db_transactions]) + 1 if db_transactions else 1
        db_transactions.append({
            'id': new_id,
            'amount': request.POST.get('amount'),
            'sender': request.POST.get('sender'),
            'status': 'На проверке'
        })
        return HttpResponseRedirect('/transactions/')
    return render(request, 'transaction_form.html')


# Карточка транзакции и Функция 3: Отказ
def transaction_detail(request, tx_id):
    tx = next((t for t in db_transactions if t['id'] == tx_id), None)
    if not tx:
        return HttpResponseRedirect('/transactions/')

    # Симуляция отказа: если статус уже не "На проверке", имитируем ошибку доступа
    # при попытке открыть карточку с целью "редактирования"
    if tx['status'] in ['Фрод', 'Ок']:
        return render(request, 'access_denied.html')

    return render(request, 'transaction_detail.html', {'tx': tx})


# --- МАРШРУТЫ (URLS) ---
urlpatterns = [
    path('', index),
    path('transactions/', transaction_list),
    path('transactions/new/', transaction_new),
    path('transactions/<int:tx_id>/', transaction_detail),
]

if __name__ == '__main__':
    execute_from_command_line(sys.argv)