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

Przykładowe ustawienia:

```json
{
  "cast_ip": "192.168.0.39",
  "nas_lan_ip": "192.168.0.10",
  "media_port": 5000,
  "media_directory": "/volume1/skrypty/cast-panel/media",
  "max_upload_mb": 100,
  "max_volume": 0.5,
  "default_audio_volume": 0.2,
  "cast_timeout_seconds": 10
}
```

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
