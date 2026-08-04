# Changelog

Wszystkie istotne zmiany będą dokumentowane w tym pliku.

Format bazuje na Keep a Changelog, a projekt stosuje Semantic Versioning.

## [Unreleased]

### Added

- Dokumentacja projektu.
- Plan implementacji etapowej.
- Wymagania bezpieczeństwa i zgodności z Pythonem 3.8.
- Minimalny szkielet aplikacji Flask z endpointem `/health`.
- Konfiguracja pytest, Ruff, logowania rotowanego oraz plików zależności.
- Diagnostyka środowiska i `THIRD_PARTY_NOTICES.md`.
- `CastService` z mockowalnym adapterem, timeoutem, reconnectem, blokadą
  komend, ustandaryzowanym statusem i wyjątkami domenowymi.
- Lokalne logowanie administratora przez Flask-Login, CLI `init-admin`,
  hashowanie haseł, CSRF oraz trwałe ustawienia w `instance/config.json`.
- Walidacja ustawień IP, portów, ścieżek, limitów uploadu, głośności i
  timeoutów oraz import/eksport konfiguracji bez sekretów.
