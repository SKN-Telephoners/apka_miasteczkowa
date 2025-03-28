import logging
from logging.handlers import RotatingFileHandler
from flask import Flask

app = Flask(__name__)

if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(username)s - %(message)s - %(ip)s')
    file_handler.setFormatter(formatter)

    app.logger.addHandler(file_handler)

@app.route('/')
def index():
    app.logger.info('Żądanie głównej strony')
    return "Witaj w aplikacji mobilnej!"

if __name__ == '__main__':
    app.run()

#Logowanie błędów i wyjątków
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error('Wystąpił błąd: %s', e, exc_info=True)
    return "Wystąpił błąd", 500

#Logowanie zapytań i odpowiedzi
@app.before_request
def log_request_info():
    app.logger.info('Przychodzące żądanie: %s %s', Flask.request.method, Flask.request.url)

@app.after_request
def log_response_info(response):
    app.logger.info('Odpowiedź: status %s', response.status)
    return response


#Moduł logging – pozwala na rejestrowanie zdarzeń na różnych poziomach.
#RotatingFileHandler – automatycznie zarządza rozmiarem pliku logów i tworzy kopie zapasowe.
#Middleware/dekoratory – umożliwiają logowanie szczegółowych informacji o żądaniach i odpowiedziach.
#Zewnętrzne systemy (np. Sentry) – wspomagają monitorowanie błędów w czasie rzeczywistym i analizę problemów.