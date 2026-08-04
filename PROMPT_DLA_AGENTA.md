# Prompt dla agenta AI: Cast Control Panel na Synology

## Cel

Zbuduj lekką aplikację webową we Flasku, uruchamianą bez Dockera na Synology NAS z Pythonem 3.8. Aplikacja ma sterować lokalnym urządzeniem Google Cast / Android TV przez `pychromecast`, a panel ma być dostępny zdalnie przez Tailscale.

Środowisko docelowe jest ograniczone:

- Synology DSM;
- Python 3.8;
- brak Dockera / Container Managera;
- brak potrzeby używania Apache;
- aplikacja ma działać samodzielnie przez serwer WSGI albo wbudowany serwer Flask na etapie MVP;
- urządzenie Cast może być wskazywane bezpośrednio po lokalnym IP, bez polegania na mDNS;
- przykładowy Cast: `192.168.0.39`;
- pliki multimedialne mają być przechowywane na NAS-ie, np. w `/volume1/skrypty/cast-panel/media`, ale mogą być uploadowane przez przeglądarkę usera;
- panel ma być dostępny wyłącznie w zaufanej sieci lub przez Tailscale.

Nie implementuj wszystkiego naraz. Pracuj etapami zgodnie z plikami w katalogu `tasks/`.

## Główne funkcje

### 1. Połączenie i status urządzenia

- konfiguracja IP urządzenia Cast;
- test połączenia;
- prezentacja:
  - nazwy urządzenia;
  - modelu;
  - aktywnej aplikacji;
  - `app_id`;
  - stanu standby;
  - aktywnego wejścia;
  - poziomu głośności;
  - wyciszenia;
  - podstawowego statusu mediów, jeśli aplikacja go udostępnia;
- czytelne komunikaty, gdy aplikacja natywna, np. Netflix lub Disney+, nie udostępnia statusu odtwarzania.

### 2. Sterowanie multimediami

- play;
- pause;
- stop;
- seek;
- mute / unmute;
- ustawienie głośności suwakiem;
- bezpieczny limit maksymalnej głośności konfigurowany przez administratora;
- przed wysłaniem mediów pokaż ostrzeżenie, jeśli urządzenie ma aktywną inną aplikację.

### 3. Obrazy

- upload JPG, JPEG, PNG i WebP;
- lista obrazów dostępnych na NAS-ie;
- podgląd;
- wyświetlenie wybranego obrazu przez Default Media Receiver;
- opcjonalny pokaz slajdów;
- czas wyświetlania slajdu;
- zatrzymanie pokazu.

### 4. Audio

- upload MP3, AAC/M4A, OGG i WAV, jeśli odbiornik obsługuje dany format;
- odtworzenie wybranego pliku;
- zatrzymanie;
- opcjonalne automatyczne ustawienie bezpiecznej głośności przed odtworzeniem;
- po zakończeniu możliwość przywrócenia poprzedniej głośności.

### 5. Wideo

- upload i lista plików MP4/WebM;
- odtworzenie;
- play / pause / stop / seek;
- walidacja typu MIME;
- komunikat, że najlepiej wspieranym formatem jest MP4 H.264 + AAC.

### 6. Lokalny serwer plików

- aplikacja ma udostępniać media po HTTP z adresu osiągalnego przez urządzenie Cast;
- nie używaj adresu Tailscale jako URL-a dla Cast;
- URL ma bazować na lokalnym IP NAS-a skonfigurowanym w ustawieniach;
- nie wystawiaj całego systemu plików;
- udostępniaj wyłącznie katalog `media`;
- zabezpiecz ścieżki przed path traversal.

### 7. Presety i kolejki

- zapisywanie presetów:
  - wybrany plik;
  - typ medium;
  - głośność;
  - opcjonalny czas zatrzymania;
- kolejka odtwarzania;
- proste uruchamianie presetów jednym przyciskiem.

### 8. Historia i logi

- dziennik techniczny:
  - data i czas;
  - użytkownik;
  - wykonana komenda;
  - wynik;
  - błąd;
- nie zapisuj treści prywatnych aplikacji ani historii oglądania;
- monitorowanie zmiany aplikacji ma być opcjonalne i domyślnie wyłączone;
- logi rotowane, bez nieograniczonego wzrostu.

### 9. Panel ustawień

- IP urządzenia Cast;
- lokalne IP NAS-a;
- port aplikacji;
- katalog mediów;
- limit rozmiaru uploadu;
- limit głośności;
- domyślna głośność dla audio;
- timeout połączenia;
- interwał odświeżania statusu;
- opcja włączenia / wyłączenia historii zmian aktywnej aplikacji;
- import i eksport konfiguracji JSON;
- walidacja konfiguracji przed zapisem.

### 10. Bezpieczeństwo

- aplikacja nie może być projektowana do publicznego wystawienia w internecie;
- dostęp tylko przez LAN lub Tailscale;
- lokalne logowanie do panelu;
- hasła hashowane przez Werkzeug;
- sesje Flask zabezpieczone losowym `SECRET_KEY`;
- CSRF dla formularzy;
- ograniczenie uploadów;
- whitelist rozszerzeń i MIME;
- bez wykonywania komend shell na podstawie danych użytkownika;
- brak domyślnego konta z prostym hasłem;
- możliwość wyłączenia logowania tylko jawnie w konfiguracji deweloperskiej;
- podstawowy rate limit dla poleceń sterujących;
- nie przechowuj haseł w repozytorium;
- plik `.env` wyłączony z Git;
- połączenia sterujące wykonywane tylko do skonfigurowanego urządzenia lub listy dozwolonych urządzeń.

### 11. Responsywność

- aplikacja musi być dostępna przez urządzenia mobilne
- aplikacja musi wyglądać na nich schludnie i być dostosowana

## Architektura

Zastosuj prostą, modułową architekturę Flask:

```text
cast-panel/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   ├── services/
│   │   ├── cast_service.py
│   │   ├── media_service.py
│   │   ├── settings_service.py
│   │   └── audit_service.py
│   ├── blueprints/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── cast/
│   │   ├── media/
│   │   └── settings/
│   ├── templates/
│   └── static/
├── instance/
├── media/
├── logs/
├── scripts/
├── tests/
├── tasks/
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── run.py
└── wsgi.py
```

Nie twórz nadmiernie skomplikowanej architektury. To ma działać na słabym NAS-ie, a nie udawać platformę Netflixa.

## Technologie

Preferowane:

- Flask;
- Flask-Login;
- Flask-WTF;
- SQLAlchemy + SQLite;
- `pychromecast`;
- `python-dotenv`;
- Waitress jako prosty serwer WSGI zgodny z Windows i Linux;
- Bootstrap 5 lokalnie lub prosty własny CSS;
- pytest;
- Ruff lub Flake8;
- Black, tylko jeśli wersja kompatybilna z Pythonem 3.8;
- type hints zgodne z Pythonem 3.8.

Nie dodawaj Reacta, Node.js ani procesu budowania frontendu bez wyraźnej potrzeby. Panel ma być lekki i łatwy do uruchomienia na Synology.

## Zgodność z Pythonem 3.8

To wymaganie krytyczne.

- Nie używaj składni `str | None`.
- Używaj `Optional[str]`.
- Nie używaj `match`.
- Nie zakładaj dostępności najnowszych wersji bibliotek.
- Przed przypięciem wersji sprawdź, jaka wersja `pychromecast` działa już w środowisku użytkownika.
- Wygeneruj `requirements.txt` na podstawie sprawdzonych, kompatybilnych wersji.
- Nie aktualizuj automatycznie działającego środowiska do wersji mogących porzucić Python 3.8.

## Obsługa Google Cast

Utwórz `CastService`, który:

- utrzymuje pojedynczą współdzieloną sesję;
- ma blokadę na równoległe komendy;
- ponawia połączenie po błędzie;
- rozpoznaje brak urządzenia;
- rozpoznaje aplikacje natywne bez standardowego namespace;
- nie blokuje requestu HTTP bez limitu czasu;
- udostępnia:
  - `connect()`;
  - `disconnect()`;
  - `get_status()`;
  - `play_media()`;
  - `show_image()`;
  - `pause()`;
  - `resume()`;
  - `stop()`;
  - `seek()`;
  - `set_volume()`;
  - `mute()`;
  - `unmute()`;
- korzysta z `known_hosts=[CAST_IP]`;
- przy odtwarzaniu obrazu / audio / wideo uruchamia Default Media Receiver;
- zwraca ustandaryzowane wyniki, zamiast przepuszczać surowe wyjątki do widoku.

## UX

Panel powinien mieć:

- dashboard z dużą kartą statusu;
- wskaźnik online/offline;
- nazwę aktywnej aplikacji;
- suwaki i przyciski pilota;
- bibliotekę multimediów z filtrami;
- podgląd obrazów;
- dialog potwierdzenia przed przerwaniem aktywnej aplikacji;
- czytelne komunikaty sukcesu i błędu;
- responsywny układ mobilny;
- ciemny motyw domyślny;
- brak irytujących animacji;
- stan ładowania podczas wysyłania polecenia.

Odświeżanie statusu może być przez prosty polling AJAX co kilka sekund. WebSockety są opcjonalne i nie są potrzebne w MVP.

## Praca etapami

1. Przeczytaj `AGENTS.md`.
2. Wykonuj taski po kolei.
3. Przed każdym taskiem:
   - przeczytaj jego plik;
   - wypisz krótki plan;
   - sprawdź stan repozytorium.
4. Po każdym tasku:
   - uruchom testy;
   - uruchom lint;
   - zaktualizuj `CHANGELOG.md`;
   - zaktualizuj dokumentację;
   - wykonaj mały, logiczny commit.
5. Nie przechodź do kolejnego taska, jeśli bieżący nie działa.
6. Nie zmieniaj architektury bez uzasadnienia w dokumentacji decyzji.
7. Nie implementuj dodatkowych funkcji „przy okazji”.

## Kryterium ukończenia MVP

MVP jest gotowe, gdy użytkownik może:

1. uruchomić aplikację na Synology;
2. zalogować się;
3. skonfigurować IP Cast i lokalne IP NAS-a;
4. zobaczyć status Play Boxa;
5. przesłać obraz;
6. wyświetlić go na Play Boxie;
7. zatrzymać odtwarzanie;
8. sterować głośnością;
9. zobaczyć błąd w czytelnej formie;
10. ponownie uruchomić aplikację bez utraty ustawień.

Najpierw dostarcz MVP. Audio, wideo, presety, kolejki i rozbudowane logi są etapami późniejszymi.
