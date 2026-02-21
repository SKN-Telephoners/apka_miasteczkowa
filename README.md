w models.py 
dodałem do tabeli
     is_confirmed = db.Column(db.Boolean, default=False)


a w bazie danych przy tworzeniu tabeli
    is_confirmed BOOLEAN DEFAULT FALSE NOT NULL,


mail weryfikujący wysyła się od razu w funkcji register_user():

dodałem dwa endponty
mail_auth_request() --- gdyby trzeba było ponownie wysyłać weryfikację


mail_auth() --- potwierdzajcy weryfikację



11.11.2025

dodałem do test_user.py
test_auth_user() i test_auth_user_invalid_email()
do testowania potwierdzenia urzytkownika przez mail

w routes.py w mail_auth_request()
poprawiłem drobne błedy związane z wysyłaniem wysyłaniem maila 