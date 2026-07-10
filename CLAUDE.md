# MyHitster Karten Generator

## Projekt
Generiert druckfertige Hitster-Spielkarten (6x6 cm, Vorder- + Rückseite) als PDF aus Spotify-Playlists.

## Nutzung
```bash
# Komplett: Import → Bereinigen → PDF
PYTHONUTF8=1 python hitster_generator.py --full

# Nur Playlist-Import
PYTHONUTF8=1 python hitster_generator.py --playlist

# Nur PDF aus bestehender Songliste
PYTHONUTF8=1 python hitster_generator.py Interpret-Titel.txt
```

## Wichtige Dateien
- `hitster_generator.py` – Hauptskript (Playlist-ID `2SCZlvxCLcGyzBSxLMXepb` ist direkt im Script hinterlegt)
- `Interpret-Titel.txt` – Songliste (Format: `Artist Titel`, eine Zeile pro Song)
- `.env` – Spotify API Credentials (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
- `.processed` – Bereits zu Karten verarbeitete Songs (für Fortsetzung nach Abbruch)
- `.spotify_cache` – Gecachter OAuth-Token
- `Hitster-Print.pdf` – Generierte Karten (früher: `hitster_druckblatt.pdf`)

## Spotify API Einschränkungen
- **Development Mode:** Fremde/Spotify-kuratierte Playlists (z.B. "All Out 80s") geben 404. Nur eigene Playlists sind abrufbar. Workaround: Playlists in eigenes Konto kopieren.
- **Neue API-Struktur:** Spotify gibt `items`/`item` zurück statt `tracks`/`track`. Spotipy funktioniert damit nicht korrekt → Playlist-Import nutzt direkte `requests`-Aufrufe.
- **Redirect URI:** Muss `http://127.0.0.1:8888/callback` sein (nicht https, nicht localhost). Im Spotify Developer Dashboard entsprechend konfigurieren.
- **Rate Limits:** ~2-3 Sekunden pro Song (3 API-Calls). Bei ~2300 Songs ca. 1.5-3 Stunden.
- **`PYTHONUTF8=1`** wird auf Windows benötigt, da die Konsole (cp1252) Unicode-Zeichen (✓, ✗) nicht darstellen kann.
- **`search(limit=…)` im Development Mode:** Gibt 400 bei `limit > 10` zurück. Alle Spotify-Suchen müssen `limit=10` (oder weniger) verwenden.
- **Original-Jahreszahl:** Spotify gibt für Klassiker oft die Remaster-/Kompilationsversion zurück (z.B. Queen 1975 → 2018 Movie Soundtrack). `_find_original_year()` macht daher 3 Suchen: Feld-Syntax, freier Text, und bei verdächtig aktuellem Ergebnis (≥ 2000) nochmals mit `year:1950-{Jahr-1}`.

## Bereinigung (automatisch bei --full)
- Alles nach ` - ` / ` – ` / ` — ` wird entfernt (Remaster, Edit, Version, Soundtrack-Hinweise)
- Remaster-Zusätze in Klammern `(Remastered 2021)` werden entfernt — Pattern: `_REMASTER_PAREN`
- Einträge mit asiatischer Schrift werden komplett entfernt
- Duplikate (case-insensitive) werden entfernt
- Zusätzlich sucht die Kartengenerierung das Original-Erscheinungsjahr über die Spotify API

## Karten-Layout (Druckblatt)
- **Format:** 55×55 mm = 650×650 px bei 300 DPI
- **PDF-Dateiname:** `Hitster-Print.pdf`
- **A4-Raster:** 3 Spalten × 4 Zeilen = 12 Karten pro Seite, zentriert, GAP=0
- **Duplex-Druck:** Langer Rand (wie Buch aufblättern). Vorderseite (Seite 1) normal; Rückseite (Seite 2) horizontal gespiegelt (`mirror=True`) damit die Karten nach dem Schneiden übereinstimmen.
- **Schnittlinien:** Nur auf der Vorderseite (QR). Weiss durch den Kartenbereich, schwarz bis Blattrand. `create_sheet_page(..., cutlines=True)` für Vorderseite, `cutlines=False` für Rückseite.
- **Lichttest:** Beim Halten gegen das Licht erscheint der Rückseitentext spiegelverkehrt — das ist normal und korrekt. Verifikation durch Ausschneiden einer Karte.

## Spotify App Konfiguration
1. https://developer.spotify.com/dashboard → "Create App"
2. Redirect URI: `http://127.0.0.1:8888/callback`
3. Client ID + Secret in `.env` eintragen
