import sys
from django.conf import settings
from django.urls import path
from django.http import HttpResponse
from django.core.management import execute_from_command_line

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='lab1-secret-key',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
    )

def home(request):
    return HttpResponse("""
        <html>
        <head><meta charset="utf-8"><title>Фрод-мониторинг</title></head>
        <body style="font-family: Arial; padding: 50px;">
            <h1>Система фрод-мониторинга финансовых транзакций</h1>
            <h3>Обнаружение мошеннических операций (Градиентный бустинг + Isolation Forest)</h3>
            <p>Версия 0.0.1</p>
            <p><i>Разработка продолжается</i></p>
        </body>
        </html>
    """)

urlpatterns = [path('', home)]

if __name__ == '__main__':
    execute_from_command_line(sys.argv)