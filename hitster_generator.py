"""
Hitster Karten Generator (CSV-Variante)
========================================
Liest Songs aus Exportify-CSV-Dateien und erstellt druckfertige Hitster-Karten als PDF.
Keine Spotify API erforderlich.

Installation:
    pip install qrcode[pil] Pillow

Export:
    1. exportify.net aufrufen → mit Spotify anmelden
    2. Playlist auswählen → CSV herunterladen → in Playlists/ ablegen

Nutzung:
    python hitster_generator.py "Playlists/My Hitster Playlist.csv"

Ausgabe:
    Fertige PDF landet in PDF-Print/Hitster-Print.pdf
"""

import sys, math, os, re, csv, json, time, unicodedata, tempfile, shutil
import requests
import qrcode
from PIL import Image, ImageDraw, ImageFont

# ─── Karten-Dimensionen ───────────────────────────────────────────────────────
CARD_W, CARD_H = 650, 650
MARGIN = 28

# Duplex-Druckversatz: Rückseite erscheint beim Gegenhalten gegen das Licht
# um diesen Wert nach links verschoben → positiver Wert korrigiert nach rechts.
# Einheit: mm. Anpassen falls Drucker anders abweicht. 0 = keine Korrektur.
BACK_OFFSET_MM = 0
BACK_OFFSET_PX = round(BACK_OFFSET_MM * 300 / 25.4)

FONT_BOLD    = "C:/Windows/Fonts/arialbd.ttf"
FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"

BG_BACK   = "#1DB954"
WHITE     = "#ffffff"
DARK_TEXT = "#121212"

MB_CACHE_FILE   = ".mb_cache"
_mb_cache: dict = {}

# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

_font_cache: dict = {}

def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# Matches suffixes after " - " / " – " / " — " that should be stripped
_SUFFIX_RE = re.compile(
    r"^("
    r"(\d{4}\s+)?(digital(ly)?\s+)?remaster(ed)?(\s+\d{4})?(\s+(version|mix))?"
    r"|deluxe(\s+edition)?"
    r"|anniversary(\s+edition)?(\s+(edition|remaster(ed)?)(\s+\d{4})?)?"
    r"|bonus\s+tracks?(\s+version)?"
    r"|expanded(\s+edition)?"
    r"|super\s+deluxe(\s+edition)?"
    r"|special\s+edition"
    r"|(\d+th|\d+st|\d+nd|\d+rd)\s+anniversary(\s+(edition|remaster(ed)?)(\s+\d{4})?)?"
    r"|live(\s+(at|in|from|version|recording).*)?"
    r"|radio\s+(version|mix|edit|cut)"
    r"|single(\s+(version|edit|mix|cut))?"
    r"|instrumental(\s+(version|mix))?"
    r"|video\s+edit"
    r"|tv\s+(mix|version)"
    r"|edit|remix|mix"
    r"|(club|dance|extended|original|acoustic|unplugged|disco)\s+(mix|version|edit|recording)"
    r"|original\s+(mix|version|recording)"
    r"|mono|stereo"
    r"|re-?recorded"
    r"|from\s+.+"
    r"|.*\bsoundtrack\b.*"
    r"|\d{4}(\s*[-–—]\s*.+)?"
    r"|.+\s+(mix|edit|version|remix)(\s+\d{4})?"
    r"|.+\s+remaster(ed)?(\s+\d{4})?"
    r"|\d+\s+years?\s+remaster(ed)?(\s+\d{4})?"
    r")$",
    re.IGNORECASE | re.DOTALL,
)

# Matches parenthetical version/edition/mix/live tags to strip
_CLEANUP_PAREN = re.compile(
    r"\s*\(\s*("
    r"(\d{4}\s+)?remaster(ed)?[^)]*"
    r"|live[^)]*"
    r"|instrumental(\s+(version|mix))?"
    r"|[^)]*\b(mix|edit|version|remix)\b[^)]*"
    r")\s*\)",
    re.IGNORECASE,
)

# Matches bracketed version/edition/mix/live tags to strip, e.g. "[Radio Edit]"
_CLEANUP_BRACKET = re.compile(
    r"\s*\[\s*("
    r"[^\]]*\bremaster(ed)?\b[^\]]*"
    r"|live[^\]]*"
    r"|bonus\s+track[^\]]*"
    r"|[^\]]*\b(mix|edit|version|remix)\b[^\]]*"
    r")\s*\]",
    re.IGNORECASE,
)


def _clean_title(title: str) -> str:
    # Strip semicolon-separated suffix variants ("- Single Version; 2019 Remaster")
    if ";" in title:
        title = title[: title.index(";")].strip()
    # Strip parenthetical/bracketed version/edition/mix tags first, so a trailing
    # dash-suffix isn't hidden behind them (e.g. "Song - Radio Edit [Remastered]")
    title = _CLEANUP_PAREN.sub("", title)
    title = _CLEANUP_BRACKET.sub("", title)
    # Strip dash-separated version/remix/edit suffixes from right to left,
    # incl. "/"-chained tags ("Fast Version / 2003 Digital Remaster")
    while True:
        matches = list(re.finditer(r"\s+[-–—]\s+", title))
        if not matches:
            break
        m = matches[-1]  # rightmost dash separator
        suffix = title[m.end() :].strip()
        segments = [s.strip() for s in re.split(r"\s+/\s+", suffix) if s.strip()]
        if segments and all(_SUFFIX_RE.match(seg) for seg in segments):
            title = title[: m.start()]
        else:
            break
    # Drop a leftover separator dangling at the end after tag removal ("Song -")
    title = re.sub(r"[\s,/\-–—]+$", "", title)
    return title.strip()


# Artists/Titles that must keep their ALL-CAPS spelling
_ALLCAPS_KEEP = {
    "INXS", "AC/DC", "ABBA", "DEVO", "TOTO", "KISS", "U2", "UB40",
    "R.E.M.", "TLC", "ATB", "RMB", "U96", "EMF", "OMD", "XTC", "UFO",
    "SNAP!", "CHIC", "SOS", "DNA", "ABC", "M/A/R/R/S", "DAF",
    "DJ BoBo", "DJ", "ZZ Top", "MC", "DMC", "D.J.", "DJ",
    "GIGI D'AGOSTINO", "CHROM", "VNV Nation", "EBM",
    "N-Trance", "E-Type", "E-Rotic", "N'SYNC", "*NSYNC",
    "OK", "TV", "USA", "UK", "NYC", "LA", "SOS", "TNT", "DNA",
    "CEO", "DJ", "MC", "MR", "MRS", "DR", "VS",
}

# Words that should only match as whole words (e.g. roman numerals)
_ALLCAPS_WHOLEWORD = {
    "II", "III", "IV", "VI", "VII", "VIII", "IX", "XI", "XII",
    "DJ", "MC", "DR", "MR", "VS",
}

def _fix_caps(text: str) -> str:
    """Korrigiert ALL-CAPS Text zu Title Case, behält bekannte Akronyme bei."""
    if not text or not text.isupper() or len(text) <= 3:
        return text
    # Check if the whole string is a known exception
    if text in _ALLCAPS_KEEP:
        return text
    # Title-case it, then restore any known acronyms within
    result = text.title()
    # Fix common patterns: Mc/Mac names, apostrophes
    result = re.sub(r"\bMc(\w)", lambda m: "Mc" + m.group(1).upper(), result)
    # Restore known all-caps words (whole-word match only)
    for word in _ALLCAPS_WHOLEWORD:
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        result = pattern.sub(word, result)
    # Restore known all-caps words (substring match)
    for word in _ALLCAPS_KEEP - _ALLCAPS_WHOLEWORD:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        if pattern.search(result):
            result = pattern.sub(word, result)
    return result


def _dedup_key(artist: str, title: str) -> str:
    """Normalisierter Schlüssel für Duplikat-Erkennung über CSV-Grenzen hinweg."""
    def norm(s):
        s = unicodedata.normalize("NFKD", s.lower())
        s = re.sub(r"[^\w\s]", "", s)
        return re.sub(r"\s+", " ", s).strip()
    return norm(artist) + "|" + norm(title)


def load_reference_keys(csv_path: str) -> set:
    """Lädt Artist/Titel-Dedup-Keys aus der Abgleichsliste offizieller Hitster-Editionen
    (Format: Artist,Title,Year,Editions — kein Exportify-Export)."""
    keys: set = set()
    if not os.path.isfile(csv_path):
        return keys
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist = row.get("Artist", "").strip()
            title = row.get("Title", "").strip()
            if artist and title:
                keys.add(_dedup_key(artist, _clean_title(title)))
    return keys


def _load_mb_cache():
    global _mb_cache
    if os.path.exists(MB_CACHE_FILE):
        try:
            with open(MB_CACHE_FILE, encoding="utf-8") as f:
                _mb_cache = json.load(f)
        except Exception:
            _mb_cache = {}


def _save_mb_cache():
    with open(MB_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(_mb_cache, f, ensure_ascii=False)


def _mb_earliest(items: list, date_field: str) -> int | None:
    """Gibt das früheste Jahr aus einer Liste von MusicBrainz-Objekten zurück."""
    earliest = None
    for item in items:
        date = item.get(date_field, "")
        if len(date) >= 4:
            try:
                y = int(date[:4])
                if 1900 <= y <= 2030 and (earliest is None or y < earliest):
                    earliest = y
            except ValueError:
                pass
    return earliest


def _find_original_year(artist: str, title: str, csv_year: str) -> str:
    """Sucht Original-Erscheinungsjahr via MusicBrainz (gecacht, ~1 req/s).

    Strategie: release-group-Suche (korrekt für Singles) → Fallback auf
    recording-Suche → Fallback auf csv_year.
    """
    cache_key = f"{artist.lower()}|{title.lower()}"
    if cache_key in _mb_cache:
        return _mb_cache[cache_key]

    headers = {"User-Agent": "MyHitster/1.0 (martin.gyr@swisstph.ch)"}
    primary = re.split(r"[,;]", artist)[0].strip().replace('"', "")
    q_title = title.replace('"', "")
    earliest = None

    # ── 1. Release-Group-Suche (liefert korrekte Single-/Album-Jahreszahlen) ──
    try:
        resp = requests.get(
            "https://musicbrainz.org/ws/2/release-group",
            params={"query": f'artist:"{primary}" AND release:"{q_title}"',
                    "fmt": "json", "limit": 15},
            headers=headers, timeout=15,
        )
        time.sleep(1.1)
        if resp.status_code == 200:
            earliest = _mb_earliest(resp.json().get("release-groups", []),
                                    "first-release-date")
    except Exception:
        pass

    if earliest:
        _mb_cache[cache_key] = str(earliest)
        return str(earliest)

    # ── 2. Fallback: Recording-Suche (für reine Album-Tracks ohne Single) ──
    try:
        resp = requests.get(
            "https://musicbrainz.org/ws/2/recording",
            params={"query": f'artist:"{primary}" AND recording:"{q_title}"',
                    "fmt": "json", "limit": 10},
            headers=headers, timeout=15,
        )
        time.sleep(1.1)
        if resp.status_code == 200:
            earliest = _mb_earliest(resp.json().get("recordings", []),
                                    "first-release-date")
    except Exception:
        pass

    result = str(earliest) if earliest else csv_year
    _mb_cache[cache_key] = result
    return result


def get_decade_tag(year: str) -> str:
    try:
        decade = int(year[:3]) * 10
        return f"{decade % 100:02d}s" if decade < 2000 else f"{decade}s"
    except (ValueError, IndexError):
        return ""


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _text_color_for_bg(hex_color: str) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return DARK_TEXT if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.5 else WHITE


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines


# ─── Genre-Mapping aus CSV-Genres ────────────────────────────────────────────

def map_genre(genres_str: str) -> str:
    g = genres_str.lower()
    if "soundtrack" in g or "film score" in g: return "Soundtrack"
    if "metal" in g:                            return "Metal"
    if "hard rock" in g:                        return "Rock"
    if "new wave" in g or "synth" in g or "darkwave" in g: return "New Wave"
    if "punk" in g or "grunge" in g:            return "Rock"
    if "rock" in g:                             return "Rock"
    if "electro" in g or "techno" in g or "house" in g or "trance" in g: return "Electronic"
    if "hip hop" in g or "rap" in g:            return "Hip-Hop"
    if "r&b" in g or "soul" in g:              return "Soul"
    if "funk" in g:                             return "Funk"
    if "jazz" in g:                             return "Jazz"
    if "classical" in g or "orchest" in g:      return "Klassik"
    if "country" in g:                          return "Country"
    if "disco" in g or "dance" in g:            return "Disco"
    if "reggae" in g or "ska" in g:             return "Reggae"
    if "pop" in g:                              return "Pop"
    return ""


# ─── CSV einlesen ────────────────────────────────────────────────────────────

def read_csv_songs(csv_path: str) -> list:
    """Liest Exportify-CSV und gibt eine Liste von Song-Dicts zurück."""
    songs = []
    try:
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uri = row.get("Track URI", "").strip()
                if not uri.startswith("spotify:track:"):
                    continue
                track_id = uri.split(":")[-1]
                link = f"https://open.spotify.com/track/{track_id}"

                # Artist: nur Hauptinterpret (vor dem ersten Semikolon)
                artists = _fix_caps(row.get("Artist Name(s)", "").split(";")[0].strip())

                title = _fix_caps(_clean_title(row.get("Track Name", "").strip()))
                release_date = row.get("Release Date", "")
                year = release_date[:4] if len(release_date) >= 4 else "????"
                genre = map_genre(row.get("Genres", ""))

                songs.append({
                    "uri":    uri,
                    "link":   link,
                    "artist": artists,
                    "title":  title,
                    "year":   year,
                    "genre":  genre,
                })
    except FileNotFoundError:
        print(f"  ✗ Datei nicht gefunden: {csv_path}")
    return songs


# ─── Karten-Grafik ───────────────────────────────────────────────────────────

RAINBOW_COLORS = [
    (41, 128, 185),   # Blau
    (29, 185, 84),    # Grün
    (241, 196, 15),   # Gelb
    (230, 126, 34),   # Orange
    (233, 30, 140),   # Pink
    (142, 68, 173),   # Lila
    (26, 188, 156),   # Türkis
    (192, 57, 43),    # Rot
]

DECADE_COLORS = {
    "196": ("#E67E22", "#c96a1b"),
    "197": ("#8E44AD", "#7a3a95"),
    "198": ("#2980B9", "#2471a3"),
    "199": ("#C0392B", "#a93226"),
    "200": ("#F1C40F", "#d4ac0d"),
    "201": ("#E91E8C", "#c4197a"),
    "202": ("#1ABC9C", "#17a589"),
}

def get_decade_colors(year: str) -> tuple:
    prefix = year[:3] if len(year) >= 3 else ""
    return DECADE_COLORS.get(prefix, (BG_BACK, "#17a349"))


def make_qr(link: str, size: int = 420) -> Image.Image:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(link)
    qr.make(fit=True)
    return qr.make_image(fill_color="#4A4A4A", back_color="white").convert("RGB").resize(
        (size, size), Image.LANCZOS
    )


def create_front(info: dict, card_number: int = 1) -> Image.Image:
    img = Image.new("RGB", (CARD_W, CARD_H), "#1a1a2a")
    draw = ImageDraw.Draw(img)

    for y in range(CARD_H):
        r = int(68 + 15 * math.sin(y * 0.01))
        g = int(68 + 10 * math.sin(y * 0.012 + 1))
        b = int(88 + 15 * math.sin(y * 0.008 + 2))
        draw.line([(0, y), (CARD_W, y)], fill=(r, g, b))

    cx, cy = CARD_W // 2, CARD_H // 2 + 14
    outer_r = 289
    inner_r = 168

    vinyl_layer = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    vinyl_draw  = ImageDraw.Draw(vinyl_layer)
    for r in range(outer_r, inner_r, -1):
        base = 25 + int(12 * math.sin(r * 0.3))
        if r % 16 < 5:
            color_idx = (r // 16) % len(RAINBOW_COLORS)
            rc = RAINBOW_COLORS[color_idx]
            vinyl_draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(rc[0], rc[1], rc[2], 255))
        else:
            vinyl_draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(base, base, base, 255))
    _, _, _, alpha_ch = vinyl_layer.split()
    alpha_ch = alpha_ch.point(lambda x: int(x * 0.67))
    vinyl_layer.putalpha(alpha_ch)
    img = Image.alpha_composite(img.convert("RGBA"), vinyl_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    qr_size = 318
    qr = make_qr(info["link"], size=qr_size)
    qr_x = cx - qr_size // 2
    qr_y = cy - qr_size // 2
    draw.rounded_rectangle(
        [qr_x - 11, qr_y - 11, qr_x + qr_size + 11, qr_y + qr_size + 11],
        radius=12, fill="white"
    )
    img.paste(qr, (qr_x, qr_y))

    draw.rectangle([0, 0, CARD_W, 40], fill=(0, 0, 0))
    font_header = _font(FONT_BOLD, 20)
    draw.text((MARGIN, 9), "MyHitster", font=font_header, fill=WHITE)
    num = f"#{card_number:04d}"
    draw.text((CARD_W - MARGIN - draw.textlength(num, font=font_header), 9), num, font=font_header, fill=WHITE)

    font_hint = _font(FONT_REGULAR, 15)
    hint = "Scan & Play"
    draw.text(((CARD_W - draw.textlength(hint, font=font_hint)) // 2, CARD_H - 22),
              hint, font=font_hint, fill="#888899")

    return img


def create_back(info: dict, card_number: int = 1) -> Image.Image:
    bg_color, _ = get_decade_colors(info["year"])
    bg_rgb = hex_to_rgb(bg_color)

    img = Image.new("RGB", (CARD_W, CARD_H), bg_color)
    draw = ImageDraw.Draw(img)

    for y in range(CARD_H):
        f = y / (CARD_H - 1)
        light = f * 0.55
        r = int(bg_rgb[0] + (255 - bg_rgb[0]) * light)
        g = int(bg_rgb[1] + (255 - bg_rgb[1]) * light)
        b = int(bg_rgb[2] + (255 - bg_rgb[2]) * light)
        draw.line([(0, y), (CARD_W, y)], fill=(r, g, b))

    def text_color_at(y: int) -> str:
        f = min(1.0, max(0.0, y / (CARD_H - 1)))
        light = f * 0.55
        rgb = tuple(int(bg_rgb[i] + (255 - bg_rgb[i]) * light) for i in range(3))
        return _text_color_for_bg(f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}")

    cx   = CARD_W // 2
    cy_v = 220
    outer_r = 180
    label_r = 92

    for r in range(outer_r, label_r, -1):
        base = 25 + int(12 * math.sin(r * 0.3))
        if r % 16 < 5:
            color_idx = (r // 16) % len(RAINBOW_COLORS)
            rc = RAINBOW_COLORS[color_idx]
            draw.ellipse([cx-r, cy_v-r, cx+r, cy_v+r], fill=(rc[0], rc[1], rc[2]))
        else:
            draw.ellipse([cx-r, cy_v-r, cx+r, cy_v+r], fill=(base, base, base))

    draw.ellipse([cx-label_r, cy_v-label_r, cx+label_r, cy_v+label_r], fill=bg_color)

    font_year = _font(FONT_BOLD, 68)
    yw = draw.textlength(info["year"], font=font_year)
    draw.text(((CARD_W - yw) // 2, cy_v - 34), info["year"], font=font_year,
              fill=_text_color_for_bg(bg_color))

    font_artist = _font(FONT_BOLD, 42)
    font_title  = _font(FONT_REGULAR, 37)

    ay = cy_v + outer_r + 65
    artist_lines = wrap_text(info["artist"], font_artist, CARD_W - 44, draw)[:2]
    for line in artist_lines:
        aw = draw.textlength(line, font=font_artist)
        draw.text(((CARD_W - aw) // 2, ay), line, font=font_artist,
                  fill=text_color_at(ay + 21))
        ay += 50

    title_lines = wrap_text(info["title"], font_title, CARD_W - 44, draw)[:2]
    for line in title_lines:
        tw = draw.textlength(line, font=font_title)
        draw.text(((CARD_W - tw) // 2, ay), line, font=font_title,
                  fill=text_color_at(ay + 18))
        ay += 45

    font_tag = _font(FONT_BOLD, 24)
    decade = get_decade_tag(info["year"])
    top_text = _text_color_for_bg(bg_color)
    draw.text((18, 9), decade, font=font_tag, fill=top_text)
    dw = draw.textlength(decade, font=font_tag)
    draw.text((CARD_W - 18 - dw, 9), decade, font=font_tag, fill=top_text)

    genre = info.get("genre", "")
    if genre:
        draw.text((18, CARD_H - 32), genre, font=font_tag, fill=WHITE)

    num = f"#{card_number:04d}"
    draw.text((CARD_W - 18 - draw.textlength(num, font=font_tag), CARD_H - 32),
              num, font=font_tag, fill=WHITE)

    return img


def create_sheet_page(cards: list, cols: int = 3, mirror: bool = False,
                      cutlines: bool = False) -> Image.Image:
    """A4-Seite mit Karten-Raster. mirror=True für Duplex-Rückseite."""
    A4_W, A4_H = 2480, 3508
    GAP = 0
    rows = math.ceil(len(cards) / cols)
    grid_w = cols * CARD_W + (cols - 1) * GAP
    grid_h = rows * CARD_H + (rows - 1) * GAP
    offset_x = (A4_W - grid_w) // 2
    if mirror:
        offset_x -= BACK_OFFSET_PX
    offset_y = (A4_H - grid_h) // 2

    sheet = Image.new("RGB", (A4_W, A4_H), "white")
    draw  = ImageDraw.Draw(sheet)

    for i, card in enumerate(cards):
        col = i % cols
        row = i // cols
        if mirror:
            col = cols - 1 - col
        x = offset_x + col * (CARD_W + GAP)
        y = offset_y + row * (CARD_H + GAP)
        sheet.paste(card, (x, y))

    if cutlines:
        CUT = "#1a1a1a"
        for c in range(cols + 1):
            lx = offset_x + c * CARD_W
            draw.line([(lx, offset_y), (lx, offset_y + grid_h)], fill="white", width=1)
            draw.line([(lx, 0), (lx, offset_y - 1)], fill=CUT, width=1)
            draw.line([(lx, offset_y + grid_h + 1), (lx, A4_H)], fill=CUT, width=1)
        for r in range(rows + 1):
            ly = offset_y + r * CARD_H
            draw.line([(offset_x, ly), (offset_x + grid_w, ly)], fill="white", width=1)
            draw.line([(0, ly), (offset_x - 1, ly)], fill=CUT, width=1)
            draw.line([(offset_x + grid_w + 1, ly), (A4_W, ly)], fill=CUT, width=1)

    return sheet


# ─── Hauptprogramm ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    PDF_DIR              = "PDF-Print"
    os.makedirs(PDF_DIR, exist_ok=True)
    PDF_FILE            = os.path.join(PDF_DIR, "Hitster-Print.pdf")
    PROCESSED_FILE      = ".processed_csv"
    PROCESSED_KEYS_FILE = ".processed_keys"
    CARDS_PER_PAGE      = 12

    if len(sys.argv) < 2:
        print('Nutzung: python hitster_generator.py "Playlists/My Hitster Playlist.csv" [--pages N]')
        sys.exit(1)

    args = sys.argv[1:]
    max_pages = None
    if "--pages" in args:
        idx = args.index("--pages")
        try:
            max_pages = int(args[idx + 1])
            args = args[:idx] + args[idx + 2:]
        except (IndexError, ValueError):
            print("Fehler: --pages erwartet eine Zahl, z.B. --pages 2")
            sys.exit(1)

    if "--offset" in args:
        idx = args.index("--offset")
        try:
            BACK_OFFSET_MM = float(args[idx + 1])
            BACK_OFFSET_PX = round(BACK_OFFSET_MM * 300 / 25.4)
            args = args[:idx] + args[idx + 2:]
        except (IndexError, ValueError):
            print("Fehler: --offset erwartet eine Zahl in mm, z.B. --offset 1.5")
            sys.exit(1)

    REFERENCE_FILE = os.path.join("Playlists", "Hitster_Original_Songs.csv")

    csv_files = args
    _load_mb_cache()

    # ── Bereits verarbeitete URIs + Dedup-Keys laden ──────────────────────
    processed_uris: set = set()
    if os.path.isfile(PROCESSED_FILE):
        with open(PROCESSED_FILE, encoding="utf-8") as f:
            processed_uris = {l.strip() for l in f if l.strip()}

    seen_keys: set = set()
    if os.path.isfile(PROCESSED_KEYS_FILE):
        with open(PROCESSED_KEYS_FILE, encoding="utf-8") as f:
            seen_keys = {l.strip() for l in f if l.strip()}

    reference_keys = load_reference_keys(REFERENCE_FILE)
    if reference_keys:
        print(f"✓ Abgleichsliste geladen: {len(reference_keys)} Songs aus offiziellen Hitster-Editionen\n")

    # ── Alle Songs aus CSVs laden, URI- und Titel-Duplikate entfernen ────
    seen_uris: set = set(processed_uris)
    all_songs: list = []
    total_dupes = 0
    total_reference_dupes = 0
    for csv_path in csv_files:
        songs = read_csv_songs(csv_path)
        new_songs = []
        for s in songs:
            if s["uri"] in seen_uris:
                continue
            key = _dedup_key(s["artist"], s["title"])
            if key in seen_keys:
                total_dupes += 1
                continue
            if key in reference_keys:
                total_reference_dupes += 1
                continue
            seen_uris.add(s["uri"])
            seen_keys.add(key)
            new_songs.append(s)
        all_songs.extend(new_songs)
        print(f"✓ {csv_path}: {len(songs)} Songs, {len(new_songs)} neu")

    if total_dupes:
        print(f"  ({total_dupes} Duplikate entfernt)")
    if total_reference_dupes:
        print(f"  ({total_reference_dupes} bereits in offiziellen Hitster-Editionen enthalten, übersprungen)")

    if max_pages is not None:
        limit = max_pages * CARDS_PER_PAGE
        if len(all_songs) > limit:
            all_songs = all_songs[:limit]
            print(f"  (auf {limit} Songs begrenzt für {max_pages} Seite(n))")

    if not all_songs:
        print("\nAlle Songs bereits verarbeitet.")
        sys.exit(0)

    print(f"\n{len(all_songs)} Songs zu verarbeiten, {len(processed_uris)} bereits gesichert.\n")

    # ── Bestehende PDF laden (inkrementelles Anfügen) ─────────────────────
    already_done   = len(processed_uris)
    already_on_page = already_done % CARDS_PER_PAGE
    start_number   = already_done + 1

    tmp_dir = tempfile.mkdtemp(prefix="hitster_")
    page_count = 0

    if os.path.isfile(PDF_FILE) and already_done > 0:
        try:
            existing_pdf = Image.open(PDF_FILE)
            n_frames = getattr(existing_pdf, "n_frames", 1)
            keep = n_frames - (2 if already_on_page > 0 else 0)
            for frame_idx in range(keep):
                if frame_idx > 0:
                    existing_pdf.seek(frame_idx)
                pg = existing_pdf.copy().convert("RGB")
                pg.save(os.path.join(tmp_dir, f"page_{page_count:04d}.png"))
                pg.close()
                page_count += 1
            existing_pdf.close()
            print(f"✓ Bestehende PDF geladen ({page_count} Seiten)\n")
        except Exception:
            page_count = 0

    def _save_page_to_tmp(img):
        """Speichert eine Seite als PNG im tmp-Verzeichnis, gibt RAM frei."""
        idx = len(os.listdir(tmp_dir))
        img.save(os.path.join(tmp_dir, f"page_{idx:04d}.png"))
        img.close()

    def _save_pdf():
        """Baut PDF aus den tmp-PNGs — lädt nur je 1 Seite in den RAM."""
        pages = sorted(os.listdir(tmp_dir))
        if not pages:
            return
        first = Image.open(os.path.join(tmp_dir, pages[0])).convert("RGB")
        rest = []
        for p in pages[1:]:
            rest.append(Image.open(os.path.join(tmp_dir, p)).convert("RGB"))
        first.save(PDF_FILE, "PDF", resolution=300, save_all=True, append_images=rest)
        first.close()
        for p in rest:
            p.close()

    # ── Karten generieren ─────────────────────────────────────────────────
    fronts, backs    = [], []
    new_uris: list   = []
    new_keys: list   = []
    total_new        = 0
    _t0 = time.time()

    for i, song in enumerate(all_songs, 1):
        card_num = start_number + len(new_uris)
        pct = i * 100 // len(all_songs)

        # Original-Jahr via MusicBrainz (gecacht)
        orig_year = _find_original_year(song["artist"], song["title"], song["year"])
        if orig_year != song["year"]:
            print(f"[{i}/{len(all_songs)} · {pct}%] {song['artist']} – {song['title']} "
                  f"({song['year']} → {orig_year})")
            song["year"] = orig_year
        else:
            print(f"[{i}/{len(all_songs)} · {pct}%] {song['artist']} – {song['title']} ({song['year']})")

        fronts.append(create_front(song, card_num))
        backs.append(create_back(song, card_num))
        new_uris.append(song["uri"])
        new_keys.append(_dedup_key(song["artist"], song["title"]))

        # ── Alle 12 Karten (1 Seite) speichern ──
        cards_for_page = already_on_page + len(fronts)
        if cards_for_page >= CARDS_PER_PAGE:
            if already_on_page > 0:
                ph = [Image.new("RGB", (CARD_W, CARD_H), "white")] * already_on_page
                pf = ph + fronts[:CARDS_PER_PAGE - already_on_page]
                pb = ph + backs[:CARDS_PER_PAGE - already_on_page]
                fronts = fronts[CARDS_PER_PAGE - already_on_page:]
                backs  = backs[CARDS_PER_PAGE - already_on_page:]
                already_on_page = 0
            else:
                pf = fronts[:CARDS_PER_PAGE]
                pb = backs[:CARDS_PER_PAGE]
                fronts = fronts[CARDS_PER_PAGE:]
                backs  = backs[CARDS_PER_PAGE:]

            _save_page_to_tmp(create_sheet_page(pf, cols=3, mirror=False, cutlines=True))
            _save_page_to_tmp(create_sheet_page(pb, cols=3, mirror=True))
            _save_pdf()

            with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
                for uri in new_uris:
                    f.write(uri + "\n")
            with open(PROCESSED_KEYS_FILE, "a", encoding="utf-8") as f:
                for key in new_keys:
                    f.write(key + "\n")
            _save_mb_cache()
            total_new += len(new_uris)
            new_uris = []
            new_keys = []
            total = already_done + total_new
            elapsed = time.time() - _t0
            done_so_far = total_new + len(new_uris)
            per_song = elapsed / max(done_so_far, 1)
            remaining = per_song * (len(all_songs) - i)
            eta = f"{int(remaining // 60)}m{int(remaining % 60):02d}s"
            print(f"  💾 Seite gespeichert · {total} Karten · {int(elapsed // 60)}m verstr. · ~{eta} verbleibend")

    # ── Letzte unvollständige Seite ───────────────────────────────────────
    if fronts:
        if already_on_page > 0:
            ph = [Image.new("RGB", (CARD_W, CARD_H), "white")] * already_on_page
            pf, pb = ph + fronts, ph + backs
        else:
            pf, pb = fronts, backs
        _save_page_to_tmp(create_sheet_page(pf, cols=3, mirror=False, cutlines=True))
        _save_page_to_tmp(create_sheet_page(pb, cols=3, mirror=True))

    if new_uris:
        with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
            for uri in new_uris:
                f.write(uri + "\n")
        with open(PROCESSED_KEYS_FILE, "a", encoding="utf-8") as f:
            for key in new_keys:
                f.write(key + "\n")
        _save_mb_cache()
        total_new += len(new_uris)

    if total_new > 0:
        _save_pdf()

    shutil.rmtree(tmp_dir, ignore_errors=True)

    total = already_done + total_new
    if total_new > 0:
        print(f"\n✓ {total_new} neue Karte(n) generiert")
        print(f"✓ {PDF_FILE}  ← druckfertig (A4, 300 DPI, beidseitig)")
        print(f"✓ Gesamt: {total} Karten")
        print("\nTipp: Beidseitig drucken (Bindung an langer Kante), ausschneiden, fertig!")
