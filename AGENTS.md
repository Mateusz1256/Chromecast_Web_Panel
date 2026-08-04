# AGENTS.md

## Zasady pracy agenta

Ten projekt jest lekkim panelem sterowania Google Cast uruchamianym na Synology NAS. Priorytetami są: niezawodność, prostota, kompatybilność z Pythonem 3.8 i możliwość łatwego serwisowania przez jedną osobę.

## Najważniejsze ograniczenia

- Python 3.8.
- Brak Dockera.
- Brak obowiązkowego Apache/Nginx.
- Ograniczone zasoby sprzętowe NAS-a.
- Pliki aplikacji i środowisko mogą znajdować się na `/volume1`.
- Katalog tymczasowy pip może wymagać `TMPDIR` ustawionego na `/volume1`.
- Google Cast może być osiągalny wyłącznie po lokalnym IP.
- Nie polegaj wyłącznie na mDNS.
- Nie aktualizuj zależności bez sprawdzenia zgodności.

## Metodyka

Pracuj małymi krokami:

1. Zrozum task.
2. Sprawdź istniejący kod.
3. Zaproponuj plan.
4. Zaimplementuj minimalny zakres.
5. Dodaj lub popraw testy.
6. Uruchom testy i lint.
7. Uzupełnij dokumentację.
8. Zaktualizuj changelog.
9. Wykonaj pojedynczy logiczny commit.

Nie mieszaj kilku niezależnych zmian w jednym commicie.

## Format commitów

Używaj Conventional Commits:

```text
feat: add cast device status endpoint
fix: handle missing media namespace
refactor: extract media URL builder
test: cover volume limit validation
docs: document Synology startup task
chore: pin Python 3.8 compatible dependencies
```

Dozwolone typy:

- `feat`
- `fix`
- `refactor`
- `test`
- `docs`
- `chore`
- `perf`
- `security`

Zmiana breaking:

```text
feat!: change settings schema
```

Opis commita ma mówić, co faktycznie zmieniono. Unikaj komunikatów typu `update`, `changes`, `fix stuff`.

## Wersjonowanie

SemVer:

- PATCH: poprawki błędów, dokumentacja, drobne bezpieczne zmiany;
- MINOR: nowe funkcje kompatybilne wstecz;
- MAJOR: zmiany niekompatybilne.

Przed `1.0.0` projekt może używać `0.x.y`, ale każda zmiana schematu konfiguracji musi być opisana.

## Changelog

Prowadź `CHANGELOG.md` zgodnie z Keep a Changelog.

Sekcje:

- Added
- Changed
- Deprecated
- Removed
- Fixed
- Security

Każdy task, który zmienia zachowanie użytkowe, ma aktualizować changelog.

## Kod

- Czytelne nazwy.
- Małe funkcje.
- Type hints zgodne z Pythonem 3.8.
- Brak globalnego mutowalnego stanu poza kontrolowanymi singletonami usług.
- Brak gołych `except:`.
- Wyjątki domenowe dla warstwy Cast.
- Logowanie przez `logging`, nigdy przez przypadkowe `print` w kodzie produkcyjnym.
- Nie loguj haseł, tokenów, ciasteczek, pełnych nagłówków ani danych prywatnych.
- Wszystkie operacje sieciowe muszą mieć timeout.

## Frontend

- Bez frameworka SPA.
- Progressive enhancement.
- Formularze działają także bez JavaScriptu, o ile ma to sens.
- JavaScript tylko dla statusu, sliderów, uploadu i wygodnych interakcji.
- Responsywność.
- Dostępność: etykiety, focus, kontrast, obsługa klawiatury.

## Testy

Minimalny zakres:

- testy konfiguracji;
- testy walidacji uploadu;
- testy budowania URL-i;
- testy limitów głośności;
- testy zachowania przy braku Cast;
- testy serwisu Cast z mockiem;
- testy autoryzacji;
- testy endpointów krytycznych.

Nie wymagaj prawdziwego urządzenia Cast w testach automatycznych.

Test integracyjny z prawdziwym urządzeniem ma być osobny i domyślnie pomijany.

## Bezpieczeństwo

- Brak komend systemowych składanych z danych użytkownika.
- Brak arbitralnego wskazywania URL-i przez niezaufanego użytkownika.
- Wyłącznie dozwolone typy mediów.
- Nazwy plików sanityzowane.
- Ścieżki sprawdzane względem katalogu bazowego.
- CSRF.
- Sesje z bezpiecznymi flagami.
- Hasła hashowane.
- Rate limiting poleceń.
- Panel nie może sugerować publicznego wystawienia w internecie.
- Dokumentacja ma preferować Tailscale.

## Licencje i credits

- Utwórz `THIRD_PARTY_NOTICES.md`.
- Wymień używane biblioteki oraz ich licencje.
- Nie kopiuj kodu z przypadkowych źródeł bez sprawdzenia licencji.
- Nie dołączaj binariów ani fontów bez licencji.
- W README dodaj sekcję Credits.

## Czego nie robić

- Nie dodawaj Dockera.
- Nie dodawaj Reacta/Vite.
- Nie dodawaj Celery, Redisa ani zewnętrznej bazy bez realnej potrzeby.
- Nie buduj systemu nadzoru użytkowników.
- Nie zapisuj historii oglądania z aplikacji.
- Nie wykonuj samoczynnych komend na telewizorze bez wyraźnej akcji użytkownika.
- Nie ustawiaj głośności na 100% jako wartości domyślnej.
