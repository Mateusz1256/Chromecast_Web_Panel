# Task 04: Biblioteka obrazów i wyświetlanie

## Cel

Dostarczyć główną funkcję MVP: upload obrazu i wyświetlenie go na Play Boxie.

## Zakres

- upload JPG/JPEG/PNG/WebP;
- limit rozmiaru;
- sanityzacja nazw;
- podgląd;
- lista plików;
- usuwanie;
- endpoint udostępniający media;
- URL na lokalnym IP NAS-a;
- uruchamianie Default Media Receiver;
- potwierdzenie przerwania aktywnej aplikacji;
- stop.

## Kryteria akceptacji

- plik poza katalogiem `media` nie może być odczytany;
- path traversal jest zablokowany;
- obraz jest osiągalny przez Play Box;
- po kliknięciu „Wyświetl” aktywna aplikacja przełącza się na odbiornik Cast;
- użytkownik dostaje wynik operacji.
