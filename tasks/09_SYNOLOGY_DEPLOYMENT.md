# Task 09: Wdrożenie na Synology

## Cel

Przygotować stabilne uruchamianie aplikacji bez Dockera.

## Zakres

- Waitress;
- `scripts/start.sh`;
- `scripts/stop.sh`;
- PID file lub bezpieczne wykrywanie procesu;
- logi startowe;
- uruchamianie z Harmonogramu zadań DSM;
- ustawienie katalogu roboczego;
- aktywacja venv;
- konfiguracja `TMPDIR`;
- backup konfiguracji i bazy;
- instrukcja aktualizacji.

## Kryteria akceptacji

- aplikacja startuje po restarcie DSM;
- druga instancja nie uruchamia się;
- błędy startu trafiają do logu;
- instrukcja nie wymaga Dockera ani Apache.
