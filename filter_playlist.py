"""
Playlist-Filter für MyHitster
=============================
Filtert FullExportPlayList.csv nach den definierten Kriterien und erzeugt
My Hitster Playlist_Gefiltert.csv.

Nutzung:
    PYTHONUTF8=1 python filter_playlist.py
"""

import csv, re, os, sys
from collections import defaultdict, Counter

# ─── Pfade ──────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE, "Playlists", "FullExportPlayList.csv")
HITSTER_CSV = os.path.join(BASE, "Playlists", "Hitster_Original_Songs.csv")
OUTPUT_CSV = os.path.join(BASE, "Playlists", "My Hitster Playlist_Gefiltert.csv")

# ─── Interpreten komplett entfernen ─────────────────────────────────────────
REMOVE_ARTISTS = {a.lower() for a in [
    "Sebastian Lightfoot", "Nova", "Retrofile", "Future World Orchestra",
    "Peru", "SRNDE", "Lone Tusker", "Hurricane on Saturn", "Star Inc.",
    "New Paradise", "Gliese", "Vivian Reed",
    # Moderne Remixes/Covers
    "Acko", "BNHM", "rivve",
    # Neuerer Technosound
    "AVAO", "Zynic",
]}

# ─── Depeche Mode: alle behalten, sogar ergänzen ────────────────────────────
UNLIMITED_ARTISTS = {a.lower() for a in [
    "Depeche Mode",
]}

# ─── Dark Wave / EBM / Synthpop / Industrial: alle behalten ─────────────────
DARKWAVE_EBM_ARTISTS = {a.lower() for a in [
    "Faderhead", "Sisters of Mercy", "The Sisters of Mercy",
    "Front 242", "VNV Nation", "CHROM", "The Neon Judgement",
    "Nitzer Ebb", "Covenant", "Apoptygma Berzerk", "Blutengel",
    "Massive Ego", "Diary of Dreams", "Diary Of Dreams",
    "De/Vision", "Mesh", "Clan of Xymox",
    "And One", "Camouflage", "Propaganda", "Wolfsheim",
    "Project Pitchfork", "Assemblage 23", "Combichrist",
    "Hocico", "Suicide Commando", "Wumpscut", ":Wumpscut:",
    "Das Ich", "Kirlian Camera", "She Past Away",
    "Lebanon Hanover", "Boy Harsher", "Drab Majesty",
    "Cold Cave", "Soft Cell", "Ultravox", "Visage",
    "Gary Numan", "Bauhaus", "DAF", "Ministry",
    "Killing Joke", "Fad Gadget", "The Mission", "Anne Clark",
    "Deine Lakaien", "Peter Murphy", "Love and Rockets",
    "Public Image Ltd.", "Gang Of Four", "Cabaret Voltaire",
    "Xmal Deutschland", "The Jesus and Mary Chain",
    "Martha and the Muffins", "The Cult",
    "The KVB", "Molchat Doma", "Twin Tribes",
    "Mr.Kitty", "Light Asylum", "Snowy Red", "Red Zebra",
    "Virgin Prunes", "Vicious Pink", "A Split-Second",
    "Shriekback", "TC Matic", "De Brassers",
    "Executive Slacks", "Arbeid Adelt!", "2 Belgen",
    "Rheingold", "Grauzone", "Alan Vega",
    "Parade Ground", "ES23", "Eisfabrik",
    "Panther Modern", "Cold Room Society",
    "John Maus", "Buzz Kull", "My Manifesto",
    "Nacht Und Nebel", "Vive La Fête",
    "Gene Loves Jezebel", "The House of Love",
    "Siouxsie and the Banshees",
    # Rauswurf-Rücknahme: Dark/EBM/Industrial
    "Ruined Conflict", "BodyHarvest", "In Strict Confidence",
    "Mono Inc.", "Rotersand", "Diorama", "Eisbrecher", "X-Perience",
]}

# ─── Bekannte Artists die IMMER bleiben ─────────────────────────────────────
ALWAYS_KEEP_ARTISTS = {a.lower() for a in [
    # 80er Synthpop/New Wave
    "New Order", "The Cure", "Orchestral Manoeuvres In The Dark",
    "Tears For Fears", "Erasure", "A Flock Of Seagulls", "Joy Division",
    "The Human League", "Duran Duran", "Spandau Ballet", "Pet Shop Boys",
    "Culture Club", "Talk Talk", "Frankie Goes To Hollywood",
    "Simple Minds", "The Police", "Blondie",
    "Alphaville", "a-ha", "Kim Wilde", "Heaven 17",
    "Yazoo", "The B-52's", "Modern Talking",
    "Madness", "DEVO", "Talking Heads", "The Cars",
    "ABC", "Thompson Twins", "Howard Jones", "Echo & the Bunnymen",
    "The Smiths", "Information Society", "Dead Or Alive",
    "Bronski Beat", "The Communards", "Berlin", "Japan",
    "Nik Kershaw", "Go West", "Mr. Mister", "Thomas Dolby",
    "Modern English", "Missing Persons", "Naked Eyes",
    "Fine Young Cannibals", "Everything But The Girl", "Blancmange",
    "The Psychedelic Furs", "Roxy Music", "The Stranglers",
    "Peter Schilling", "Men At Work", "Bananarama",
    "Level 42", "Wang Chung", "The Fixx", "Real Life",
    "Re-Flex", "Trans-X", "Limahl", "Nena", "Red Flag",
    "The Outfield", "Cutting Crew", "ICEHOUSE",
    "Men Without Hats", "Animotion", "Toni Basil",
    "Altered Images", "Swing Out Sister", "Johnny Hates Jazz",
    "China Crisis", "The Go-Go's", "Bryan Ferry",
    "The The", "When In Rome", "Starship",
    "Prefab Sprout", "The Style Council", "Kate Bush",
    "Book Of Love", "Anything Box", "The Motels", "The Romantics",
    "'Til Tuesday", "Pretenders",

    # Pop/Rock Legenden
    "Queen", "Michael Jackson", "Madonna", "The Beatles", "The Rolling Stones",
    "David Bowie", "Prince", "Elton John", "Phil Collins", "Genesis",
    "Rod Stewart", "Billy Joel", "Bruce Springsteen", "Daryl Hall & John Oates",
    "Fleetwood Mac", "Whitney Houston", "TOTO", "Dire Straits",
    "Billy Idol", "Steve Winwood", "George Michael", "U2",
    "Roxette", "Sandra", "ABBA", "Bryan Adams", "Chris de Burgh",
    "Kylie Minogue", "Simply Red", "Bee Gees", "Stevie Wonder",
    "Tina Turner", "Lionel Richie", "Cyndi Lauper", "Paul Young",
    "Wham!", "Billy Ocean", "Pat Benatar", "Alison Moyet",
    "Robert Palmer", "Rick Astley", "Robbie Williams", "Seal",
    "Jennifer Rush", "Laura Branigan", "Stevie Nicks",
    "Mariah Carey", "Belinda Carlisle", "Paula Abdul",
    "Falco", "Peter Gabriel", "Paul McCartney", "Roy Orbison",
    "Sting", "Chris Rea", "Mark Knopfler",
    "Kenny Loggins", "Crowded House", "Suzanne Vega",
    "Neneh Cherry", "UB40", "Taylor Dayne", "Robin Beck",
    "Peter Cetera", "Rick Springfield", "John Waite",
    "John Parr", "F.R. David", "Bonnie Tyler",

    # Hard Rock / Metal - die Grossen
    "AC/DC", "Metallica", "Aerosmith", "Foreigner", "Def Leppard",
    "ZZ Top", "Van Halen", "Bon Jovi", "Guns N' Roses", "KISS",
    "Scorpions", "Whitesnake", "Europe", "Heart", "Journey", "Survivor",
    "Iron Maiden", "Judas Priest", "Ozzy Osbourne", "Led Zeppelin",
    "Alice Cooper", "Cheap Trick", "REO Speedwagon",
    "Don Henley", "Tom Petty", "Tom Petty and the Heartbreakers",
    "Huey Lewis & The News", "Styx", "Supertramp", "Status Quo",
    "Eddie Money", "Loverboy", "Nazareth",
    "Deep Purple", "Black Sabbath", "Rainbow",
    "Thin Lizzy", "Lynyrd Skynyrd",

    # Classic Rock
    "Pink Floyd", "The Who", "The Doors", "Jimi Hendrix", "Eagles",
    "Eric Clapton", "Santana", "Electric Light Orchestra",
    "Simon & Garfunkel", "The Doobie Brothers",
    "The Clash", "Rush", "The Alan Parsons Project",
    "Boston", "Kansas", "Asia", "Foreigner",
    "Gerry Rafferty", "Mike + The Mechanics",

    # Electronic/Synth
    "Kraftwerk", "Mike Oldfield", "Yello", "Enigma",
    "Jean-Michel Jarre", "Vangelis", "Jan Hammer",
    "Tangerine Dream", "Giorgio Moroder", "The Art Of Noise",
    "Harold Faltermeyer", "Kitaro", "Jon & Vangelis",
    "Enya", "Klaus Schulze", "Boytronic", "Laserdance", "Koto",
    "Patrick Cowley", "Schiller",

    # Disco/Funk - die Hits
    "Donna Summer", "Boney M.", "CHIC", "Earth, Wind & Fire",
    "Sister Sledge", "Kool & The Gang", "KC & The Sunshine Band",
    "Gloria Gaynor", "Dan Hartman", "Patrick Hernandez",
    "Lipps Inc.", "Imagination", "Cameo", "Odyssey",

    # 90er/2000er Rock - die Bekannten
    "Nirvana", "Pearl Jam", "Green Day", "Red Hot Chili Peppers",
    "R.E.M.", "Oasis", "Linkin Park", "Foo Fighters",
    "The Cranberries", "The Offspring", "Radiohead",
    "The Killers",

    # Eurodance / Dance - die Hits
    "2 Unlimited", "Scooter", "Real McCoy", "La Bouche",
    "DJ BoBo", "Aqua", "Vengaboys", "Haddaway",
    "Dr. Alban", "Robert Miles", "ATB", "Darude",
    "Sash!", "Daft Punk", "Faithless", "Moby",
    "The Prodigy", "Jamiroquai", "Fatboy Slim",
    "GIGI D'AGOSTINO", "SNAP!", "Technotronic",
    "Ace of Base", "Culture Beat", "Magic Affair",
    "Corona", "Whigfield", "Eiffel 65", "N-Trance", "Coolio",
    "U96", "Marusha",

    # Rammstein
    "Rammstein",

    # Deutsche Hits
    "Nena", "Hubert Kah", "C.C. Catch", "Bad Boys Blue",
    "Blue System", "Peter Schilling",

    # Italo Disco
    "Ken Laszlo", "Fancy", "Silent Circle",
    "Valerie Dore", "Miko Mission",

    # One-Hit-Wonders die jeder kennt
    "Eurythmics", "INXS", "Joan Jett & the Blackhearts",
    "Irene Cara", "Grace Jones", "Hot Chocolate",
    "Herbie Hancock", "Bobby Brown",
    "Richard Marx", "Billy Squier",

    # Weitere bekannte
    "Daryl Braithwaite", "Cock Robin", "Blümchen",
    "Mötley Crüe", "George Harrison",
    "Creedence Clearwater Revival", "Steve Miller Band",
    "Steve Perry", "The Bangles", "Twisted Sister",
    "Lenny Kravitz", "T. Rex", "Christopher Cross",
    "John Mellencamp", "Bruce Hornsby and the Range",
    "Poison", "Yes", "Midnight Oil", "Glass Tiger",
    "Eric Carmen", "Armin van Buuren",
    "Joe Jackson", "Bob Seger", "The Knack",
    "Kim Carnes", "Blue Öyster Cult", "4 Non Blondes",
    "Ramones", "Ennio Morricone", "Loverboy",
    "Bob Dylan", "Elvis Presley", "Cher",
    "Annie Lennox", "Iggy Pop", "Patti Smith",
    "Diana Ross", "Barry White",
    "Gloria Estefan", "Janet Jackson",
    "Run-D.M.C.", "Grandmaster Flash",
    "Sex Pistols", "Dead Kennedys",
    "Pixies", "Cocteau Twins",
    "Jeff Buckley", "Savage Garden",
    "Crash Test Dummies", "Chumbawamba",
    "The Beach Boys", "Kajagoogoo", "The Animals",
    "Steppenwolf", "The Kinks", "The Hollies",
    "Big Country", "Michael Sembello", "The Rembrandts",
    "38 Special", "The Monkees", "Quiet Riot",
    "Bachman-Turner Overdrive", "George Thorogood & The Destroyers",
    "Tommy Tutone", "Nickelback", "Shania Twain",
    "John Williams", "Hans Zimmer",
    "Kajagoogoo", "Ratt",
    "Earth, Wind & Fire", "The J. Geils Band",
    "Rita Lee",
    "Adam & The Ants", "Backstreet Boys", "Baltimora",
    "Bill Medley", "Climie Fisher", "David Lee Roth",
    "Eminem", "Joe Cocker", "Kenny Rogers",
    "Olivia Newton-John", "Soul II Soul", "Sweet",
    "The Buggles", "Manfred Mann", "Aretha Franklin",
    "Alanis Morissette", "Beastie Boys",
    "Barclay James Harvest", "Dexys Midnight Runners",
    "Divinyls", "Elvis Costello", "Elvis Costello & The Attractions",
    "Dio", "Winger", "Mr. Big", "Chicago",
    "Village People", "Opus", "Alannah Myles",
    "Mick Jagger", "Marillion", "Robin Gibb",
    "Jefferson Airplane", "Cream", "Traveling Wilburys",
    "The Goo Goo Dolls", "Weezer", "Matchbox Twenty",
    "John Denver", "John Farnham",

    # Rauswurf-Rücknahme: Legenden & Klassiker
    "Bob Marley & The Wailers", "Janis Joplin", "Chuck Berry",
    "Fats Domino", "Neil Diamond", "Neil Young", "John Lennon",
    "Freddie Mercury", "Tom Jones", "Tracy Chapman", "Meat Loaf",
    "Art Garfunkel", "Sade", "Chaka Khan", "Dionne Warwick",

    # Rauswurf-Rücknahme: Rock/Metal
    "Gary Moore", "Uriah Heep", "Jethro Tull", "Slade",
    "Cinderella", "Krokus", "Ugly Kid Joe", "Dirkschneider & The Old Gang",
    "Dr. Feelgood", "Stray Cats", "Sparks",

    # Rauswurf-Rücknahme: 80er Pop/New Wave
    "Boy George", "Marc Almond", "Debbie Gibson", "Fiction Factory",
    "Freeez", "Frida", "Jermaine Stewart", "Julian Lennon",
    "Katrina & The Waves", "Londonbeat", "Murray Head",
    "Nick Kamen", "Philip Bailey", "Scritti Politti",
    "Sheena Easton", "T'Pau", "Captain Sensible", "Adam Ant",
    "Living In A Box", "Shakin' Stevens", "Showaddywaddy",
    "The Hooters", "The Housemartins", "Paul Hardcastle",
    "Rockwell", "Lisa Stansfield", "Joan Osborne",
    "Jon Bon Jovi", "Lou Gramm", "Chris Isaak", "Chris Norman",
    "John Miles", "Amii Stewart", "Malcolm McLaren",

    # Rauswurf-Rücknahme: 90er/2000er Pop
    "Counting Crows", "The Connells", "Third Eye Blind",
    "No Doubt", "Spin Doctors", "Sheryl Crow", "Avril Lavigne",
    "Britney Spears", "Christina Aguilera", "P!nk", "Céline Dion",
    "Ricky Martin", "Shaggy", "Nelly", "USHER", "Will Smith",
    "Kid Rock", "Uncle Kracker", "Spice Girls", "Wet Wet Wet",

    # Rauswurf-Rücknahme: Disco/Funk/Soul
    "Inner Circle", "Luther Vandross", "DeBarge",
    "The Jacksons", "The Pointer Sisters", "The Temptations",
    "Vanessa Williams", "Bobby Brown", "Salt-N-Pepa",

    # Rauswurf-Rücknahme: Dance/Eurodance
    "Brooklyn Bounce", "MC Hammer", "Kris Kross",
    "East 17", "Mr. President", "Vanilla Ice", "Milli Vanilli",
    "R3SPAWN", "Oh Well", "RMB", "Lost Frequencies", "David Guetta",

    # Rauswurf-Rücknahme: Italo Disco
    "Gazebo", "Scotch", "Fun Fun", "Rockets",

    # Rauswurf-Rücknahme: Deutsche Hits
    "Münchener Freiheit", "Die Prinzen", "Klaus Lage",
    "Wolfgang Petry", "BAP", "Joachim Witt", "David Hasselhoff",

    # Rauswurf-Rücknahme: Film/Soundtrack-Komponisten
    "Alan Silvestri", "John Carpenter",
    # Nachnamen-Varianten (gleiche Künstler, anderer Credit in CSV)
    "Zimmer", "Moroder", "Jarre", "Gore", "Martin L. Gore", "Hammer",

    # Rauswurf-Rücknahme: Sonstige Bekannte
    "Jive Bunny and the Mastermixers", "Les Humphries Singers",
    "Alisha", "Bob Marley & The Wailers", "M/A/R/R/S",
    "Manfred Mann's Earth Band", "Miami Sound Machine",
    "Ram Jam", "Space", "Sydney Youngblood", "Sailor",
    "Al Bano And Romina Power", "Alcazar", "Baccara", "Band Aid",
    "Chubby Checker", "Eddy Grant", "ELO", "Gary Glitter",
    "Gregorian", "Jimmy Cliff", "Jimmy Somerville",
    "J.Hammer", "Los Lobos", "Los Del Rio",
    "Ray Parker Jr.", "Salvador Dream", "Till Lindemann",
    "Todd Hoffman", "Umberto Tozzi", "The Toy Dolls",
    "Yaz", "IQ", "Frida",
]}

# ─── Mainstream-Acts: max Top 10 ────────────────────────────────────────────
MAINSTREAM_MAX10 = {a.lower() for a in [
    "Queen", "Michael Jackson", "The Beatles", "Madonna",
    "The Rolling Stones", "Prince", "Bruce Springsteen",
    "Elton John", "Phil Collins", "Genesis", "Fleetwood Mac",
    "Rod Stewart", "Bryan Adams", "Bon Jovi", "Aerosmith",
    "AC/DC", "INXS", "U2", "Billy Joel", "Dire Straits",
    "TOTO", "Guns N' Roses", "Van Halen", "ZZ Top",
    "The Who", "KISS", "Pink Floyd", "David Bowie",
    "Roxette", "Pet Shop Boys", "Duran Duran",
    "The Police", "Tears For Fears", "Billy Idol",
    "The Human League", "Foreigner", "Electric Light Orchestra",
    "The Clash", "Survivor", "Huey Lewis & The News",
    "The Cure", "Journey", "Tom Petty",
    "The Alan Parsons Project", "Simple Minds",
    "Rammstein", "Mike Oldfield", "The Outfield",
    "Daryl Hall & John Oates", "Pat Benatar", "The Cars",
    "Pretenders", "Whitesnake", "Europe",
    "Stevie Nicks", "George Michael", "Don Henley",
    "Culture Club", "Dead Or Alive",
    "Mr. Mister", "REO Speedwagon", "Richard Marx",
    "Supertramp", "The Doobie Brothers", "Thompson Twins",
    "a-ha", "Robert Palmer",
    "Tina Turner", "Whitney Houston", "Wham!",
    "Stevie Wonder", "Red Hot Chili Peppers",
    "Status Quo", "Bee Gees", "Simon & Garfunkel",
    "Paul McCartney", "Boston", "Asia",
    "Rick Springfield", "Roxy Music", "Rush",
    "The B-52's", "The Bangles", "Thin Lizzy",
    "Oasis", "Cutting Crew", "Men Without Hats",
    "Enigma", "John Parr", "Billy Squier",
    "Eddie Money", "Falco", "Joan Jett & the Blackhearts",
    "Jimi Hendrix", "Ozzy Osbourne", "R.E.M.",
    "The Fixx", "Mike + The Mechanics",
    "Frankie Goes To Hollywood", "Wang Chung",
    "Jan Hammer", "Metallica", "Led Zeppelin",
    "Deep Purple", "Black Sabbath",
]}

# Spezifische Limits pro Interpret
ARTIST_LIMITS = {
    "vangelis": 5,
    "jean-michel jarre": 10,
    "sisters of mercy": 10,
    "the sisters of mercy": 10,
    "kraftwerk": 10,
    "orchestral manoeuvres in the dark": 10,
}

# ─── Bekannte Akronyme (Caps-Korrektur) ─────────────────────────────────────
ALLCAPS_KEEP = {
    "INXS", "AC/DC", "ABBA", "DEVO", "TOTO", "KISS", "U2", "UB40",
    "R.E.M.", "TLC", "ATB", "RMB", "U96", "EMF", "OMD", "XTC", "UFO",
    "SNAP!", "CHIC", "SOS", "DNA", "ABC", "M/A/R/R/S", "DAF",
    "DJ BoBo", "ZZ Top", "CHROM", "VNV Nation",
    "N-Trance", "E-Type", "E-Rotic", "*NSYNC",
    "ICEHOUSE", "OK", "TV", "USA", "UK", "NYC", "TNT",
    "II", "III", "IV", "DJ", "MC",
}
_ALLCAPS_LOOKUP = {k.upper(): k for k in ALLCAPS_KEEP}

# ─── Titel-Bereinigung (Remaster, Version, Extended, Bonus) ─────────────────
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

_CLEANUP_PAREN = re.compile(
    r"\s*\(\s*("
    r"(\d{4}\s+)?remaster(ed)?[^)]*"
    r"|live[^)]*"
    r"|instrumental(\s+(version|mix))?"
    r"|bonus\s+track[^)]*"
    r"|mono(\s+version)?"
    r"|stereo(\s+version)?"
    r"|single(\s+(version|edit|mix))?"
    r"|extended(\s+(version|edit|mix))?"
    r"|[^)]*\b(mix|edit|version|remix)\b[^)]*"
    r")\s*\)",
    re.IGNORECASE,
)

_CLEANUP_BRACKET = re.compile(
    r"\s*\[\s*("
    r"[^\]]*\bremaster(ed)?\b[^\]]*"
    r"|live[^\]]*"
    r"|bonus\s+track[^\]]*"
    r"|[^\]]*\b(mix|edit|version|remix)\b[^\]]*"
    r")\s*\]",
    re.IGNORECASE,
)


def clean_title(title: str) -> str:
    """Bereinigt Titel von Remaster/Version/Extended/Bonus-Zusätzen."""
    if ";" in title:
        title = title[: title.index(";")].strip()
    title = _CLEANUP_PAREN.sub("", title)
    title = _CLEANUP_BRACKET.sub("", title)
    while True:
        matches = list(re.finditer(r"\s+[-–—]\s+", title))
        if not matches:
            break
        m = matches[-1]
        suffix = title[m.end():].strip()
        segments = [s.strip() for s in re.split(r"\s+/\s+", suffix) if s.strip()]
        if segments and all(_SUFFIX_RE.match(seg) for seg in segments):
            title = title[: m.start()]
        else:
            break
    title = re.sub(r"[\s,/\-–—]+$", "", title)
    return title.strip()


def get_main_artist(artist_names: str) -> str:
    """Nur Hauptinterpret (alles nach Komma weg, feat. bleibt)."""
    # Exportify trennt mehrere Artists mit ", " — nur ersten behalten
    parts = artist_names.split(",")
    return parts[0].strip()


def fix_caps(text: str) -> str:
    """GROSSBUCHSTABEN → Title Case, ausser bekannte Akronyme."""
    if not text or not text.isupper() or len(text) <= 3:
        return text
    if text.upper() in _ALLCAPS_LOOKUP:
        return _ALLCAPS_LOOKUP[text.upper()]
    words = text.split()
    result = []
    for w in words:
        if w.upper() in _ALLCAPS_LOOKUP:
            result.append(_ALLCAPS_LOOKUP[w.upper()])
        else:
            result.append(w.capitalize())
    return " ".join(result)


def has_asian_chars(text: str) -> bool:
    """Prüft auf asiatische Schriftzeichen."""
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff" or "\u3040" <= ch <= "\u30ff" or "\uac00" <= ch <= "\ud7af":
            return True
    return False


def load_hitster_originals(path: str) -> set:
    """Lädt Hitster Original Songs als Set von (artist_lower, title_lower)."""
    originals = set()
    if not os.path.exists(path):
        return originals
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist = row.get("Artist", "").strip().lower()
            title = row.get("Title", "").strip().lower()
            if artist and title:
                originals.add((artist, title))
    return originals


def main():
    print("=" * 60)
    print("MyHitster Playlist-Filter")
    print("=" * 60)

    # Hitster Original Songs laden (zum Abgleich)
    hitster_originals = load_hitster_originals(HITSTER_CSV)
    print(f"\nHitster Original Songs geladen: {len(hitster_originals)}")

    # CSV einlesen
    rows = []
    with open(INPUT_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    total = len(rows)
    print(f"Songs in FullExportPlayList.csv: {total}")

    # ─── Schritt 1: Hauptinterpret extrahieren ───────────────────────────────
    for row in rows:
        row["_main_artist"] = get_main_artist(row["Artist Name(s)"])
        row["_main_artist_lower"] = row["_main_artist"].lower()

    # ─── Schritt 2: Interpreten komplett entfernen ───────────────────────────
    before = len(rows)
    rows = [r for r in rows if r["_main_artist_lower"] not in REMOVE_ARTISTS]
    print(f"\n1. Entfernte Interpreten (Blocklist): -{before - len(rows)} Songs")

    # ─── Schritt 3: Asiatische Schrift entfernen ────────────────────────────
    before = len(rows)
    rows = [r for r in rows
            if not has_asian_chars(r["Track Name"])
            and not has_asian_chars(r["_main_artist"])]
    print(f"2. Entfernte Songs (asiatische Schrift): -{before - len(rows)}")

    # ─── Schritt 4: Nur bekannte Interpreten behalten ───────────────────────
    all_known = ALWAYS_KEEP_ARTISTS | DARKWAVE_EBM_ARTISTS | UNLIMITED_ARTISTS
    before = len(rows)
    removed_unknown = []
    kept = []
    for row in rows:
        if row["_main_artist_lower"] in all_known:
            kept.append(row)
        else:
            removed_unknown.append(row)
    rows = kept
    print(f"3. Entfernte unbekannte Interpreten: -{len(removed_unknown)} Songs")
    # Zeige die entfernten Interpreten
    unknown_artists = Counter(r["_main_artist"] for r in removed_unknown)
    if unknown_artists:
        print(f"   Entfernte Interpreten ({len(unknown_artists)} verschiedene):")
        for artist, count in unknown_artists.most_common(30):
            print(f"     {count:3d}x  {artist}")
        if len(unknown_artists) > 30:
            print(f"     ... und {len(unknown_artists) - 30} weitere")

    # ─── Schritt 5: Titel bereinigen ────────────────────────────────────────
    cleaned = 0
    for row in rows:
        orig = row["Track Name"]
        row["Track Name"] = clean_title(row["Track Name"])
        if row["Track Name"] != orig:
            cleaned += 1
    print(f"\n4. Titel bereinigt (Remaster etc.): {cleaned}")

    # ─── Schritt 6: Caps korrigieren ────────────────────────────────────────
    caps_fixed = 0
    for row in rows:
        new_artist = fix_caps(row["_main_artist"])
        new_title = fix_caps(row["Track Name"])
        if new_artist != row["_main_artist"] or new_title != row["Track Name"]:
            caps_fixed += 1
        row["_main_artist"] = new_artist
        row["_main_artist_lower"] = new_artist.lower()
        row["Artist Name(s)"] = new_artist
        row["Track Name"] = new_title
    print(f"5. Caps-Korrekturen: {caps_fixed}")

    # ─── Schritt 7: Duplikate entfernen (case-insensitive) ──────────────────
    before = len(rows)
    seen = set()
    unique_rows = []
    for row in rows:
        key = (row["_main_artist_lower"], row["Track Name"].lower())
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)
    rows = unique_rows
    print(f"6. Entfernte Duplikate: -{before - len(rows)}")

    # ─── Schritt 8: Song-Anzahl pro Interpret begrenzen ─────────────────────
    artist_songs = defaultdict(list)
    for row in rows:
        artist_songs[row["_main_artist_lower"]].append(row)

    limited_rows = []
    limited_count = 0
    limit_details = []
    for artist_lower, songs in artist_songs.items():
        # Sortiere nach Popularity (höchste zuerst)
        songs.sort(key=lambda r: int(r.get("Popularity", 0) or 0), reverse=True)

        if artist_lower in UNLIMITED_ARTISTS:
            limited_rows.extend(songs)
        elif artist_lower in DARKWAVE_EBM_ARTISTS:
            limited_rows.extend(songs)
        elif artist_lower in ARTIST_LIMITS:
            limit = ARTIST_LIMITS[artist_lower]
            if len(songs) > limit:
                limited_rows.extend(songs[:limit])
                cut = len(songs) - limit
                limited_count += cut
                limit_details.append(f"     {songs[0]['_main_artist']}: {len(songs)} → {limit} (-{cut})")
            else:
                limited_rows.extend(songs)
        elif artist_lower in MAINSTREAM_MAX10:
            if len(songs) > 10:
                limited_rows.extend(songs[:10])
                cut = len(songs) - 10
                limited_count += cut
                limit_details.append(f"     {songs[0]['_main_artist']}: {len(songs)} → 10 (-{cut})")
            else:
                limited_rows.extend(songs)
        elif len(songs) > 5:
            # Weniger bekannte: max Top 5
            limited_rows.extend(songs[:5])
            cut = len(songs) - 5
            limited_count += cut
            limit_details.append(f"     {songs[0]['_main_artist']}: {len(songs)} → 5 (-{cut})")
        else:
            limited_rows.extend(songs)

    rows = limited_rows
    print(f"\n7. Reduzierte Songs (Interpreten-Limit): -{limited_count}")
    if limit_details:
        for d in sorted(limit_details):
            print(d)

    # ─── Schritt 9: Abgleich mit Hitster Original Songs ─────────────────────
    hitster_matches = 0
    for row in rows:
        key = (row["_main_artist_lower"], row["Track Name"].lower())
        if key in hitster_originals:
            row["_in_hitster"] = "JA"
            hitster_matches += 1
        else:
            row["_in_hitster"] = ""
    print(f"\n8. Songs auch in Hitster Original: {hitster_matches}")

    # ─── Schritt 10: CSV schreiben ──────────────────────────────────────────
    out_fields = [
        "Artist Name(s)", "Track Name", "Album Name",
        "Album Release Date", "Popularity", "Track URI",
        "In Hitster Original",
    ]

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(out_fields)
        for row in rows:
            writer.writerow([
                row["_main_artist"],
                row["Track Name"],
                row.get("Album Name", ""),
                row.get("Album Release Date", ""),
                row.get("Popularity", ""),
                row.get("Track URI", ""),
                row.get("_in_hitster", ""),
            ])

    print(f"\n{'=' * 60}")
    print(f"ERGEBNIS: {len(rows)} Songs (von {total} original)")
    print(f"Gespeichert: {OUTPUT_CSV}")
    print(f"{'=' * 60}")

    # Top Interpreten
    final_artists = Counter()
    for row in rows:
        final_artists[row["_main_artist"]] += 1
    print(f"\nTop 40 Interpreten:")
    for artist, count in final_artists.most_common(40):
        marker = " [DM!]" if artist.lower() in UNLIMITED_ARTISTS else \
                 " [DW]" if artist.lower() in DARKWAVE_EBM_ARTISTS else ""
        print(f"  {count:3d}  {artist}{marker}")
    print(f"\n  Total: {len(final_artists)} verschiedene Interpreten")


if __name__ == "__main__":
    main()
