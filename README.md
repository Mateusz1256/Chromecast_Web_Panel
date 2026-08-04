# Cast Control Panel

Lekki panel webowy Flask do sterowania urządzeniem Google Cast / Android TV z Synology NAS.

## Założenia

- Python 3.8;
- Synology DSM;
- brak Dockera;
- dostęp zdalny przez Tailscale;
- lokalne połączenie NAS → Android TV / Chromecast;
- media przechowywane lokalnie na NAS-ie.

## Planowane funkcje

- status urządzenia i aktywnej aplikacji;
- wyświetlanie obrazów;
- odtwarzanie audio i wideo;
- sterowanie play/pause/stop/seek;
- głośność i mute;
- biblioteka multimediów;
- pokazy slajdów;
- presety;
- kolejka;
- konfiguracja i eksport ustawień;
- lokalne konto administratora;
- techniczne logi operacji.

## Wymagania

- Python 3.8;
- działający `pip`;
- działające połączenie z urządzeniem Cast po TCP 8009;
- pakiet `pychromecast` zgodny z Pythonem 3.8;
- dostęp urządzenia Cast do lokalnego URL-a NAS-a.

## Docelowa lokalizacja

Przykład:

```text
/volume1/skrypty/cast-panel
```

Zalecane katalogi:

```text
/volume1/skrypty/cast-panel/media
/volume1/skrypty/cast-panel/logs
/volume1/skrypty/cast-panel/instance
/volume1/skrypty/tmp-pip
```

## Instalacja deweloperska

```bash
cd /volume1/skrypty/cast-panel

python3 -m venv .venv
source .venv/bin/activate

export TMPDIR=/volume1/skrypty/tmp-pip
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jeżeli `venv` nie jest dostępne w pakiecie Pythona Synology, użyj instalacji użytkownika i odnotuj to w dokumentacji środowiska. Nie instaluj zależności systemowo bez potrzeby.

Minimalna konfiguracja startowa znajduje się w `.env.example`. Skopiuj ją do
`.env` i ustaw co najmniej `SECRET_KEY`, `MEDIA_DIRECTORY` oraz
`LOG_DIRECTORY` zgodnie ze ścieżkami na NAS-ie.

Weryfikacja bootstrapu:

```bash
python -m pytest
python -m ruff check .
python run.py
```

Pierwsze konto administratora utwórz ręcznie przez CLI. Aplikacja nie ma
domyślnego loginu ani hasła:

```bash
flask --app wsgi:app init-admin
```

Endpoint diagnostyczny:

```text
GET /health
```

Poprawna odpowiedź:

```json
{"status": "ok"}
```

Uwaga: pierwszy bootstrap został lokalnie sprawdzony na Pythonie 3.12.4,
ponieważ taki interpreter jest dostępny w środowisku roboczym. Zależności
w `requirements.txt` są przypięte do wersji deklarujących zgodność z
Pythonem 3.8 albo wcześniejszym. Na Synology należy uruchomić te same testy
pod docelowym Pythonem 3.8.

## Uruchomienie

MVP:

```bash
python run.py
```

Produkcja lokalna:

```bash
waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
```

Panel powinien być udostępniany wyłącznie przez LAN lub Tailscale.

## Konfiguracja

Konfiguracja ma być przechowywana w:

```text
instance/config.json
```

Sekrety i hash hasła nie mogą trafiać do Git.

Lokalne konto administratora jest przechowywane w SQLite:

```text
instance/app.sqlite3
```

Hasła są hashowane przez Werkzeug. Formularze logowania i ustawień są
chronione przez CSRF. Import i eksport ustawień obejmuje tylko publiczne pola
konfiguracji, bez sekretów aplikacji i bez hashy haseł.

Przykładowe ustawienia:

```json
{
  "cast_ip": "192.168.0.39",
  "nas_lan_ip": "192.168.0.10",
  "app_port": 5000,
  "media_directory": "/volume1/skrypty/cast-panel/media",
  "max_upload_mb": 100,
  "max_volume": 0.5,
  "default_audio_volume": 0.2,
  "cast_timeout_seconds": 10,
  "monitor_app_changes": false
}
```

Na etapie rdzenia Cast dostępna jest warstwa `CastService`, która przyjmuje
`CAST_IP` i `CAST_TIMEOUT_SECONDS` z konfiguracji aplikacji. Serwis łączy się
przez `known_hosts=[CAST_IP]`, nie polega wyłącznie na mDNS i zwraca własne
słowniki statusu zamiast obiektów `pychromecast`.

Obsługiwane błędy domenowe:

- `CastDeviceUnavailable`;
- `CastConnectionTimeout`;
- `CastUnsupportedCommand`;
- `CastMediaLaunchFailed`.

Testy tej warstwy używają mockowanego adaptera i nie wymagają fizycznego
urządzenia Cast.

Panel ustawień zapisuje konfigurację trwale w `instance/config.json`.
Walidowane są adresy IP, port, katalog mediów, limity uploadu, poziomy
głośności i timeout Cast. Katalog mediów musi znajdować się pod katalogiem
projektu, co ogranicza ryzyko przypadkowego udostępnienia obcych ścieżek.

## Dashboard statusu

Po zalogowaniu pierwszym ekranem jest dashboard pod `/`. Widok pokazuje stan
online/offline, nazwę urządzenia, model, aktywną aplikację, `app_id`, standby,
aktywne wejście, głośność, mute i standardowy status mediów, jeśli urządzenie
go udostępnia.

Status jest dostępny również jako JSON:

```text
GET /status
```

Endpoint jest chroniony logowaniem i mapuje błędy Cast na odpowiedź offline
bez tracebacka. Frontend odświeża status prostym pollingiem AJAX zgodnie z
`status_refresh_seconds` z ustawień i utrzymuje tylko jedno aktywne zapytanie.

Dashboard zawiera też podstawowy pilot:

- ustawianie głośności suwakiem;
- mute/unmute;
- play/pause/stop;
- seek, gdy dostępny jest standardowy status mediów.

Komendy pilota są wysyłane do endpointów `/remote/*` metodą POST i wymagają
zalogowania oraz CSRF. Backend zawsze wymusza `max_volume` z ustawień, więc
frontend nie może przypadkiem ustawić 100%. Każda poprawnie wykonana komenda
zwraca świeży status urządzenia. Prosty rate limit `COMMAND_RATE_LIMIT_SECONDS`
ogranicza zbyt szybkie powtarzanie tej samej komendy.

## Biblioteka obrazów

Widok `/media` pozwala zalogowanemu administratorowi przesłać, podejrzeć,
usunąć i odtworzyć media na urządzeniu Cast. Obsługiwane typy obrazów:

- JPG/JPEG;
- PNG;
- WebP.

Obsługiwane typy audio:

- MP3;
- AAC/M4A;
- OGG;
- WAV.

Obsługiwane typy wideo:

- MP4;
- WebM.

Upload sprawdza rozszerzenie, MIME, podstawową sygnaturę dla obrazów, limit
`max_upload_mb` i sanityzuje nazwę pliku. Pliki są zapisywane wyłącznie w
skonfigurowanym katalogu mediów.

Aplikacja nie transkoduje plików i nie obiecuje obsługi dowolnego kodeka.
Dla wideo zalecany jest MP4 H.264 + AAC, bo jest najlepiej wspierany przez
Google Cast / Android TV. WebM i inne kontenery mogą zależeć od konkretnego
odbiornika.

Publiczny endpoint plików:

```text
GET /media/files/<filename>
```

Ten endpoint nie wymaga sesji Flask, ponieważ urządzenie Cast musi móc pobrać
plik bez ciasteczek logowania. Odczyt nadal jest ograniczony do katalogu
`media`, blokuje path traversal i obsługuje tylko dozwolone typy obrazów.

URL wysyłany do Cast jest budowany z lokalnego adresu NAS-a i portu aplikacji:

```text
http://<nas_lan_ip>:<app_port>/media/files/<filename>
```

Przycisk „Wyświetl” albo „Odtwórz” uruchamia Default Media Receiver przez
`CastService`. Przy audio aplikacja przed startem ustawia bezpieczną domyślną
głośność `default_audio_volume`, nie przekraczając `max_volume`, i zapamiętuje
poprzedni poziom do przywrócenia po `Stop`. Widok pokazuje potwierdzenie przed
przerwaniem aktywnej aplikacji oraz udostępnia przycisk `Stop`.

Biblioteka obsługuje też proste scenariusze:

- pokaz slajdów z wyborem obrazów i czasem slajdu;
- kolejkę wybranych mediów;
- presety zapisywane w `instance/presets.json`.

Aktywne zadanie jest trzymane wyłącznie w pamięci procesu. Aplikacja dopuszcza
tylko jedno aktywne zadanie naraz, pozwala je zatrzymać i nie wznawia komend
samoczynnie po restarcie. Presety przetrwają restart, ale uruchomienie presetu
zawsze wymaga jawnej akcji użytkownika.

## Logi i audyt

Aplikacja zapisuje dwa typy logów w katalogu `logs`:

- `app.log` - techniczne logi aplikacji Flask;
- `audit.log` - rotowany JSONL z operacjami panelu.

Rozmiar i liczba kopii logów są kontrolowane przez `LOG_MAX_BYTES` oraz
`LOG_BACKUP_COUNT`, więc pliki nie rosną bez końca. Panel `/audit` pokazuje
ostatnie operacje i ostatnie błędy.

Audyt zapisuje użytkownika, nazwę komendy, wynik, błąd i ograniczone szczegóły
techniczne. Sekrety, hasła, tokeny, ciasteczka, nagłówki, pełne URL-e mediów,
tytuły i `content_id` są redagowane albo nie są przekazywane do audytu. Audyt
nie jest historią oglądania.

Monitoring zmian aktywnej aplikacji Cast jest opcjonalny i domyślnie wyłączony:

```json
{
  "monitor_app_changes": false
}
```

Po jawnym włączeniu zapisywane są tylko techniczne informacje o zmianie
aplikacji, takie jak `app_id` i nazwa aplikacji, bez tytułów odtwarzanych treści.

## Start po uruchomieniu DSM

Docelowo aplikacja powinna mieć skrypt:

```text
scripts/start.sh
```

i być uruchamiana przez Harmonogram zadań DSM jako zadanie przy starcie systemu.

Skrypt ma:

- ustawić katalog roboczy;
- aktywować środowisko;
- ustawić `TMPDIR`, jeśli potrzebne;
- uruchomić Waitress;
- przekierować logi do pliku;
- zapobiegać uruchomieniu drugiej instancji.

## Bezpieczeństwo

- Nie wystawiaj portu aplikacji na publiczny internet.
- Używaj Tailscale.
- Ustaw silne hasło administratora.
- Nie używaj domyślnych danych logowania.
- Ogranicz głośność.
- Nie pozwalaj użytkownikowi sterować dowolnym adresem IP.
- Włącz CSRF i limit uploadu.

## Taski

Kolejność realizacji znajduje się w katalogu `tasks/`.

## Licencja

Do ustalenia przed publikacją. Dla projektu open source rozsądnym wyborem jest MIT lub Apache-2.0.

## Credits

Projekt korzysta z bibliotek wymienionych w `THIRD_PARTY_NOTICES.md`.
Przed publikacją należy ponownie zweryfikować metadane licencji i wybrać
licencję dla samej aplikacji.
