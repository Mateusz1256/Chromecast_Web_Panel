# Task 01: Core Cast Service

## Cel

Zbudować niezależną warstwę obsługi urządzenia Google Cast.

## Zakres

- `CastService`;
- konfiguracja `cast_ip`;
- połączenie przez `known_hosts`;
- timeout;
- reconnect;
- blokada komend;
- ustandaryzowany status;
- własne wyjątki:
  - device unavailable;
  - connection timeout;
  - unsupported command;
  - media launch failed;
- mockowalne adaptery do testów.

## Kryteria akceptacji

- status urządzenia jest zwracany jako własny DTO/dict;
- brak surowych obiektów `pychromecast` w warstwie widoków;
- błędy są czytelnie mapowane;
- testy nie wymagają fizycznego Play Boxa.
