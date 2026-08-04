# Task 00: Discovery i bootstrap repozytorium

## Cel

Zweryfikować środowisko Synology i przygotować minimalny szkielet projektu bez implementacji funkcji użytkowych.

## Zakres

- sprawdzenie wersji Python;
- sprawdzenie działającej wersji `pychromecast`;
- sprawdzenie dostępności `venv`;
- zapis `pip freeze` do pliku diagnostycznego;
- utworzenie struktury projektu;
- podstawowa konfiguracja Flask;
- endpoint `/health`;
- konfiguracja testów;
- konfiguracja logowania;
- `.env.example`;
- `requirements.txt` z wersjami zgodnymi z Pythonem 3.8;
- `requirements-dev.txt`;
- `THIRD_PARTY_NOTICES.md`.

## Kryteria akceptacji

- aplikacja startuje na Pythonie 3.8;
- `GET /health` zwraca JSON 200;
- testy przechodzą;
- brak zależności wymagających Pythona 3.9+;
- README zawiera faktyczne polecenia instalacji dla Synology.
