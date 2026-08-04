# Task 02: Logowanie i ustawienia

## Cel

Dodać lokalne konto administratora i trwałą konfigurację.

## Zakres

- Flask-Login;
- inicjalizacja pierwszego administratora przez CLI;
- hashowanie hasła;
- SQLite;
- formularz ustawień;
- walidacja IP, portów, ścieżek i limitów;
- test połączenia z Cast;
- import / eksport bez sekretów;
- CSRF.

## Kryteria akceptacji

- niezalogowany użytkownik nie steruje urządzeniem;
- brak domyślnego hasła;
- ustawienia przetrwają restart;
- błędne IP i ścieżki są odrzucane.
