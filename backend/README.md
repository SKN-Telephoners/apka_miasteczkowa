4.12.2025
Wcześniejsza gałąź feed_view mi się zepsułą i nie chciałem jej już naprawiać XD

jest dodana funkcja 
feed()
w routes.py która zwraca 21 eventów

jest zrobiny zalązeg testów w pliku test_feed.py

w conftest.py
dodałęm fixture który tworzy 21 eventów do testów

09.12.2025

funkcja działa feed/
działa 
ma przy parametry
    page - która strona ma być
    limit - ile ma być zwróconych ewentów
    sort - sortuje po dacie rosnąca dla "1" i malejąco dla "2"

testy działają
sprawdzają 22 wcześniej utworzone ewenty
czy parametr page i sort działa
oraz brak ewentów


