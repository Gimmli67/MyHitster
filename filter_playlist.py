"""Filter My Hitster Playlist: nur bekannte Songs behalten.
Profil: Kinder der 80er, Metal-Fans, 90er Eurodance, Dark Wave/EBM/Synthpop/Industrial.
"""
import csv
import re
from collections import Counter

INFILE = 'Playlists/My Hitster Playlist.csv'
OUTFILE = 'Playlists/My Hitster Playlist_Gefiltert.csv'

# ─── Genres die KOMPLETT rausfliegen ─────────────────────────────────────────
REMOVE_GENRES = {
    'chanson', 'französischer jazz', 'variété française',
    'french chanson', 'chanson française',
    'country', 'bluegrass', 'americana',
    'reggae', 'dancehall', 'ska',
    'latin', 'latin pop', 'reggaeton', 'salsa', 'bachata', 'cumbia',
    'k-pop', 'j-pop', 'mandopop', 'c-pop',
    'bollywood',
    'gregorianischer gesang',
    'christmas', 'weihnachten',
    'jazz', 'jazz fusion', 'smooth jazz', 'vocal jazz',
    'classical', 'klassik', 'elektronische klassik',
    'new age', 'space music', 'ambient',
    'celtic rock', 'celtic',
    'lounge',
    'singer-songwriter',
    'surf rock',
    'rockabilly', 'psychobilly',
    'blues', 'bluesrock',
    'southern rock',
    'yacht rock',
    'art rock',
    'jangle pop',
    'quiet storm',
    'motown', 'klassischer soul', 'soul',
    'r&b', 'neo soul',
    'soundtrack',
    'trip-hop',
    'tropical house',
    'witch house',
    'electro house',
    'french house',
    'französischer house',
    'hypertechno',
    'acid house',
    'gabba', 'hardcore techno',
    'dance pop',
    'old school hip-hop', 'east coast hip-hop', 'hip-hop',
    'west coast hip-hop', 'gangster rap', 'g-funk', 'rap',
    'glam rock', 'glam metal', 'proto-punk',
    'power pop',
}

def genre_should_remove(genre_str):
    """Prüft ob ALLE Genres eines Songs in der Remove-Liste sind."""
    if not genre_str.strip():
        return False  # kein Genre = nicht filtern
    genres = [g.strip().lower() for g in genre_str.split(',')]
    # Entfernen wenn ALLE Genres in der Remove-Liste sind
    return all(g in REMOVE_GENRES for g in genres)


# ─── Bekannte Artists die IMMER bleiben (egal welches Genre) ─────────────────
# Nur die wirklich grossen/bekannten
ALWAYS_KEEP_ARTISTS = {
    # 80er Synthpop/New Wave - die Grossen
    'Depeche Mode', 'New Order', 'The Cure', 'Orchestral Manoeuvres In The Dark',
    'Tears For Fears', 'Erasure', 'Ultravox', 'A Flock Of Seagulls', 'Joy Division',
    'The Human League', 'Duran Duran', 'Spandau Ballet', 'Pet Shop Boys',
    'Culture Club', 'Soft Cell', 'Talk Talk', 'Frankie Goes To Hollywood',
    'Gary Numan', 'Simple Minds', 'The Police', 'Blondie',
    'Alphaville', 'a-ha', 'Kim Wilde', 'Heaven 17',
    'Yazoo', "The B-52's", 'Modern Talking', 'Camouflage',
    'Madness', 'DEVO', 'Talking Heads', 'The Cars',
    'ABC', 'Thompson Twins', 'Howard Jones', 'Echo & the Bunnymen',
    'Siouxsie and the Banshees', 'The Smiths',
    'Information Society', 'Dead Or Alive', 'Bronski Beat',
    'The Communards', 'Visage', 'Berlin', 'Japan',
    'Nik Kershaw', 'Go West', 'Mr. Mister', 'Thomas Dolby',
    'Modern English', 'Missing Persons', 'Naked Eyes',
    'Fine Young Cannibals', 'Everything But The Girl', 'Blancmange',
    'The Psychedelic Furs', 'Roxy Music', 'The Stranglers',
    'Peter Schilling', 'Men At Work', 'Bananarama',
    'Level 42', 'Wang Chung', 'The Fixx', 'Real Life',
    'Re-Flex', 'Trans-X', 'Limahl', 'Nena', 'Red Flag',
    'The Outfield', 'Cutting Crew', 'ICEHOUSE',
    'Men Without Hats', 'Animotion', 'Toni Basil',
    'Altered Images', 'Swing Out Sister', 'Johnny Hates Jazz',
    'China Crisis', "The Go-Go's", 'Bryan Ferry',
    'The The', 'When In Rome', 'Starship',
    'Prefab Sprout', 'The Style Council', 'Kate Bush',
    'Book Of Love', 'Anything Box', 'The Motels', 'The Romantics',
    "'Til Tuesday", 'Pretenders',

    # Pop/Rock Legenden
    'Queen', 'Michael Jackson', 'Madonna', 'The Beatles', 'The Rolling Stones',
    'David Bowie', 'Prince', 'Elton John', 'Phil Collins', 'Genesis',
    'Rod Stewart', 'Billy Joel', 'Bruce Springsteen', 'Daryl Hall & John Oates',
    'Fleetwood Mac', 'Whitney Houston', 'TOTO', 'Dire Straits',
    'Billy Idol', 'Steve Winwood', 'George Michael', 'U2',
    'Roxette', 'Sandra', 'ABBA', 'Bryan Adams', 'Chris de Burgh',
    'Kylie Minogue', 'Simply Red', 'Bee Gees', 'Stevie Wonder',
    'Tina Turner', 'Lionel Richie', 'Cyndi Lauper', 'Paul Young',
    'Wham!', 'Billy Ocean', 'Pat Benatar', 'Alison Moyet',
    'Robert Palmer', 'Rick Astley', 'Robbie Williams', 'Seal',
    'Jennifer Rush', 'Laura Branigan', 'Stevie Nicks',
    'Mariah Carey', 'Belinda Carlisle', 'Paula Abdul',
    'Samantha Fox', 'Sabrina', 'Sonia', 'Tiffany', 'Debbie Gibson',
    'Falco', 'Peter Gabriel', 'Paul McCartney', 'Roy Orbison',
    'Sting', 'Chris Rea', 'Mark Knopfler', 'Cliff Richard',
    'Joe Jackson', 'Adam Ant', 'Feargal Sharkey',
    'Kenny Loggins', 'Crowded House', 'Suzanne Vega',
    'New Kids On The Block', 'Neneh Cherry', 'Wet Wet Wet',
    'UB40', 'Bros', 'Taylor Dayne', 'Robin Beck',
    'Transvision Vamp', 'Peter Cetera', 'Rick Springfield',
    'John Waite', 'Mick Jagger', 'Deacon Blue',
    'Sananda Maitreya', 'John Parr', 'F.R. David',
    'Climie Fisher', 'The Waterboys',
    'Bobby Brown', 'Chaka Khan', 'Shalamar',
    'Salt-N-Pepa', 'Janet Jackson',
    'Bonnie Tyler', 'Don Johnson',

    # Disco/Funk/Soul - die Hits
    'Donna Summer', 'Boney M.', 'Gibson Brothers', 'CHIC',
    'The Pointer Sisters', 'Earth, Wind & Fire', 'Sister Sledge',
    'Kool & The Gang', 'KC & The Sunshine Band', 'Gloria Gaynor',
    'Dan Hartman', 'Patrick Hernandez', 'Lipps Inc.',
    'Ottawan', 'Imagination', 'James Brown', 'The Jacksons',
    'Marvin Gaye', 'Cameo', 'Inner City', 'Odyssey',
    'Evelyn "Champagne" King',

    # Hard Rock / Metal - die Grossen
    'AC/DC', 'Metallica', 'Aerosmith', 'Foreigner', 'Def Leppard',
    'ZZ Top', 'Van Halen', 'Bon Jovi', "Guns N' Roses", 'KISS',
    'Scorpions', 'Whitesnake', 'Europe', 'Heart', 'Journey', 'Survivor',
    'Iron Maiden', 'Judas Priest', 'Ozzy Osbourne', 'Led Zeppelin',
    'Poison', 'Cinderella', 'Skid Row', 'Alice Cooper',
    'Cheap Trick', 'REO Speedwagon', 'Steve Miller Band',
    'Bob Seger', 'Don Henley', 'Tom Petty', 'Tom Petty and the Heartbreakers',
    'Bruce Hornsby and the Range', 'Huey Lewis & The News',
    'Styx', 'Chicago', 'Supertramp', 'Status Quo',
    'Eddie Money', 'John Mellencamp', 'Loverboy',

    # Classic Rock
    'Pink Floyd', 'The Who', 'Creedence Clearwater Revival', 'The Doors',
    'Jimi Hendrix', 'Eagles', 'Eric Clapton', 'Santana',
    'Electric Light Orchestra', 'Thin Lizzy',
    'Simon & Garfunkel', 'The Doobie Brothers',
    'Ramones', 'Sex Pistols', 'The Clash',
    'Rush', 'Deep Purple',

    # 90er/2000er Rock - die Bekannten
    'Nirvana', 'Pearl Jam', 'Green Day', 'Red Hot Chili Peppers',
    'R.E.M.', 'Oasis', 'Linkin Park', 'Foo Fighters',
    'The Cranberries', 'The Offspring', 'Alice In Chains',
    'Beastie Boys', 'The Verve', 'Radiohead',
    'System Of A Down', 'Matchbox Twenty', 'blink-182',
    'Counting Crows', 'Savage Garden', 'The Killers',
    'Kings of Leon', 'Weezer', 'Jeff Buckley',

    # 90er/2000er Pop
    "Destiny's Child", 'TLC', '*NSYNC', 'Christina Aguilera',
    'Britney Spears', 'Milli Vanilli',

    # Eurodance / Dance - die Hits
    '2 Unlimited', 'Scooter', 'Real McCoy', 'La Bouche',
    'DJ BoBo', 'Aqua', 'Vengaboys', 'Haddaway',
    'Dr. Alban', 'Robert Miles', 'ATB', 'Darude',
    'Sash!', 'Daft Punk', 'Faithless', 'Moby',
    'The Prodigy', 'Jamiroquai', 'Fatboy Slim',
    'GIGI D\'AGOSTINO', 'Paul Elstak', 'Deee-Lite',
    'U96', 'Dune', 'Marusha', 'Snap!',
    'Technotronic', 'Ace of Base', 'Culture Beat',
    'Magic Affair', 'Corona', 'Whigfield',
    'Groove Coverage', 'Eiffel 65',
    'N-Trance', 'Coolio',

    # Rammstein
    'Rammstein',

    # Dark Wave / EBM / Industrial / Synthpop (euer Ding!)
    'Faderhead', 'Sisters of Mercy', 'Front 242', 'VNV Nation',
    'CHROM', 'The Neon Judgement', 'Bauhaus', 'DAF',
    'Nitzer Ebb', 'Ministry', 'Killing Joke', 'Fad Gadget',
    'The Mission', 'Anne Clark', 'Propaganda', 'Clan of Xymox',
    'Wolfsheim', 'Project Pitchfork', 'Diary Of Dreams',
    'Deine Lakaien', 'De/Vision', 'Covenant', 'Blutengel',
    'She Past Away', 'Peter Murphy', 'Love and Rockets',
    'Public Image Ltd.', 'Gang Of Four', 'Cabaret Voltaire',
    'Xmal Deutschland', 'The Jesus and Mary Chain', 'Pixies',
    'Martha and the Muffins', 'The Cult', 'Lebanon Hanover',
    'The KVB', 'Boy Harsher', 'Molchat Doma', 'Twin Tribes',
    'Mr.Kitty', 'Light Asylum', 'Snowy Red', 'Red Zebra',
    'Virgin Prunes', 'Kirlian Camera', 'Vicious Pink',
    'A Split-Second', 'Shriekback', 'TC Matic',
    'De Brassers', 'Executive Slacks', 'Arbeid Adelt!',
    '2 Belgen', 'The Bollock Brothers', 'Rheingold',
    'Gary Numan;Tubeway Army', 'Tubeway Army',
    'The Boomtown Rats', 'Bob Geldof',
    'The Jam', 'Morrissey', 'The Sound',
    'Sad Lovers & Giants', 'Parade Ground',
    'Massive Ego', 'ES23', 'Eisfabrik',
    'Panther Modern', 'Cold Room Society',
    'John Maus', 'Buzz Kull', 'My Manifesto',
    'Nacht Und Nebel', 'Lavvi Ebbel', 'The Scabs',
    'De Kreuners', 'Luna Twist',
    'The House of Love', 'Gene Loves Jezebel',

    # Electronic/Synth
    'Kraftwerk', 'Mike Oldfield', 'Yello', 'Enigma',
    'The Alan Parsons Project', 'Jean-Michel Jarre', 'Vangelis',
    'Jan Hammer', 'Tangerine Dream', 'Giorgio Moroder',
    'The Art Of Noise', 'Harold Faltermeyer', 'Schiller',
    'Kitaro', 'Jon & Vangelis', 'Enya',
    'Ennio Morricone', 'Klaus Schulze',
    'Boytronic', 'Laserdance', 'Koto',
    'Patrick Cowley',

    # Deutsche Hits
    'Die Fantastischen Vier', 'Udo Lindenberg', 'Peter Maffay',
    'Matthias Reim', 'Hubert Kah', 'C.C. Catch',
    'Bad Boys Blue', 'Blue System', 'Nena',
    'Neue Deutsche Welle',

    # Italo Disco
    'Ken Laszlo', 'Fancy', 'Silent Circle',
    'Valerie Dore', 'Joy', 'Miko Mission',

    # One-Hit-Wonders die jeder kennt
    '10cc', 'Adam & The Ants', 'After The Fire',
    'Afrika Bambaataa', 'Barry Manilow', 'Barry White',
    'Diana Ross', 'Eminem', 'Extreme', 'Faith No More',
    'George Harrison', 'Gloria Estefan', 'Iggy Pop',
    'Joan Jett & the Blackhearts', 'John Lennon',
    'Lenny Kravitz', 'Patti Smith', 'Vanilla Ice',
    'Will Smith', 'Take That',
    'Youssou N\'Dour', 'Zucchero', 'Dr. Dre',
    'Sixpence None The Richer', 'Tasmin Archer',
    'The Pasadenas', 'Aretha Franklin',
    'Eurythmics', 'INXS',
    'Herbie Hancock', 'Bobby Brown',
    'Lisa Stansfield', 'Soul II Soul',
    # Fehlende bekannte Artists
    '3 Doors Down', '38 Special', 'Accept', 'Ace Frehley',
    'Air Supply', 'Allman Brothers Band', 'A Taste Of Honey',
    'Aaliyah', 'Dio', 'Deep Purple', 'Lynyrd Skynyrd',
    'Rainbow', 'T. Rex', 'Janis Joplin', 'Canned Heat',
    'Traveling Wilburys', "Manfred Mann's Earth Band",
    'Barclay James Harvest', 'Smokie', 'Mike + The Mechanics',
    'Sparks', 'Donald Fagen', 'Gary Moore', 'Quiet Riot',
    'W.A.S.P.', 'Warrant', 'Great White', 'Firehouse',
    'Winger', 'Billy Squier', 'Steve Perry', 'The Tubes',
    'Robert Plant', 'Ted Nugent', 'Manowar',
    'George Thorogood & The Destroyers',
    'Daryl Braithwaite', 'Richard Marx', 'Christopher Cross',
    'Oingo Boingo', 'Flash and the Pan', 'General Public',
    'Bow Wow Wow', 'The Church', 'Split Enz',
    'Murray Head', 'Double', 'Midnight Oil',
    'Black Lace', 'Jive Bunny and the Mastermixers',
    'Goombay Dance Band', 'Eruption',
    'Mark Knopfler', 'The Hooters', 'Fischer-Z',
    'Dario G', 'Big Country', 'Marillion',
    'Alison Moyet', 'Leo Sayer',
    'Patrice Rushen', 'Anita Ward', 'Patti LaBelle',
    'Robin Gibb', 'Cheryl Lynn', 'Modjo', 'George Benson',
    'Benjamin Orr', 'The Sundays', 'Toad The Wet Sprocket',
    'Ugly Kid Joe', 'CAKE', 'Gin Blossoms', 'Del Amitri',
    'A Tribe Called Quest', 'Cypress Hill',
    'Nickelback', 'Silverchair', 'Creed', 'The Cardigans',
    'Billy Talent', 'Black Sabbath',
    'Boston', 'Kansas', 'Foreigner',
    'Joan Osborne', 'Crash Test Dummies', 'Chumbawamba',
    'Bloodhound Gang', 'Bomfunk MC\'s',
    'Gerry Rafferty', 'Kenny Rogers', 'John Travolta',
    'Elvis Presley', 'Bob Dylan', 'Cher',
    'Annie Lennox', 'Boy George', 'Peter Cetera',
    'Alan Vega', 'Grauzone',
    'Herbie Hancock', 'Hot Chocolate',
    'Irene Cara', 'Grace Jones',
    'Bruno Mars', 'Avril Lavigne', 'No Doubt',
    'David Guetta', 'Basshunter', 'Captain Jack',
    'Benny Benassi', 'DJ Sammy',
    'Corona', 'Captain Hollywood Project',
    'La Cream', 'East 17',
    'Jennifer Lopez', 'Destiny\'s Child',
    'Backstreet Boys', 'Spice Girls',
    'Britney Spears', 'Justin Timberlake',
    'Milli Vanilli',
    't.A.T.u.', 'Jennifer Paige',
    'Tone-Loc', 'Young MC',
    'Run-D.M.C.', 'Grandmaster Flash',
    'Blackstreet', 'Coolio',
    'Dr. Dre', 'Snoop Dogg', 'Eminem',
    'Will Smith', 'Cypress Hill',
    'Beastie Boys',
    'Ms. Lauryn Hill',
    'Fugees',
    'Arctic Monkeys', 'Fall Out Boy',
    'Dionne Warwick', 'Frida',
    'Cock Robin', 'Dead Kennedys',
    'Crosby, Stills & Nash', 'Derek & The Dominos',
    'Jefferson Airplane', 'Jefferson Starship',
    'Jerry Lee Lewis', 'Joe Cocker',
    'Cream', 'Bob Marley',
    'Elvis Costello & The Attractions',
    'Buzzcocks', 'Cocteau Twins',
    'Sade', 'Miami Sound Machine',
    'M/A/R/R/S', 'S\'Express', 'Yazz',
    'Ice Mc', 'Mr. President',
    'Da Buzz', 'French Affair',
    'Brooklyn Bounce', 'New Limit',
    'Party Animals', 'Leila K',
    'RMB', 'Interactive', 'Solid Base',
    'Critical Mass', 'Future Breeze',
    'Daze', 'La Bouche', 'DJ BoBo',
    '2 Brothers On The 4th Floor',
    'Charly Lownoise & Mental Theo',
    'Dr. Motte & WestBam present',
    'Modern Talking;Eric Singleton',
    'Jermaine Stewart', 'Hue and Cry',
    'The Housemartins', 'Roachford',
    'Colonel Abrams', 'Womack & Womack',
    'Luther Vandross', 'Mel & Kim',
    'Jeffrey Osborne',
    'The Commitments;Andrew Strong',
    'Danny Wilson', 'Alexander O\'Neal',
    'Ibo', 'Fancy', 'Ken Laszlo', 'Silent Circle',
    'Piano Fantasia', 'Black', 'Lime', 'Cerrone',
    'Moon Ray', 'Koto', 'Boytronic', 'Laserdance',
    'Valerie Dore', 'Joy', 'Miko Mission',
    'Ed Starink', 'Futureworld Orchestra',
    'Breakfast Club', 'Night School', 'Delight',
    'Rendez Vous',
    'Vive La Fête',
    'Patrick Hernandez;Hervé Tholance',
    'Patrick Hernandez;Snight B',
    'Gibson Brothers;New Generation',
    'Rip Gerber',
    'Black White And Co', 'Fun Fun',
    'Real McCoy', '2 Unlimited',
    'AVAO', 'Zynic',
    'R3SPAWN', 'Oh Well',
    'Hammer', 'Jarre',
    'Alain Morisod', 'Moroder', 'Sergio Presto',
    'London Starlight Orchestra',
    'Enya',
    'Hot Butter', 'Cusco',
    'Brad Fiedel', 'Danny Elfman',
    'Delerium', 'John Foxx',
    'Julian Lennon', 'Kajagoogoo',
    'Enigma', 'Schiller',

    # Bekannte Collabs (Spotify-Schreibweise mit ;)
    'Eurythmics;Annie Lennox;Dave Stewart',
    'Eurythmics;Annie Lennox;Dave Stewart;Aretha Franklin',
    'Daryl Hall & John Oates',
    'Elton John;Kiki Dee', 'Elton John;Dua Lipa;PNAU',
    'Lionel Richie;Diana Ross', 'Philip Bailey;Phil Collins',
    'Bill Medley;Jennifer Warnes', 'Patrick Swayze;Wendy Fraser',
    'The Bangles;Susanna Hoffs', 'Miami Sound Machine;Gloria Estefan',
    'Pet Shop Boys;Dusty Springfield',
    'Lisa Stansfield;Ian Devaney;Andy Morris',
    'Soul II Soul;Caron Wheeler',
    'Tears For Fears;Dave Bascombe', 'Tears For Fears;Oleta Adams',
    'Tom Jones;Mousse T.',
    'Run\u2013D.M.C.;Aerosmith',
    'Coolio;L.V.', 'Dr. Dre;Snoop Dogg',
    'N-Trance;Ricardo Da Force', 'N-Trance;Rod Stewart',
    'Aretha Franklin;George Michael',
    'Will Smith;Dru Hill;Kool Moe Dee',
    'Youssou N\'Dour;Neneh Cherry', 'Zucchero;Paul Young',
    'C & C Music Factory;Freedom Williams',
    'Technotronic;Felly',
    'Eiffel 65;Gabry Ponte',
    'Alice Deejay',
    'Jason Donovan;Kylie Minogue',
    'Take That;Lulu',
    'Gloria Estefan;Miami Sound Machine',
    'Adamski;Seal',
    'Joan Jett & the Blackhearts',
    'Afrika Bambaataa;The Soulsonic Force',
    'Fugees;Ms. Lauryn Hill;Wyclef Jean;Pras',
    'Purple Disco Machine;Sophie and the Giants',
    'Majestic;Boney M.',
    'Roxette;Peter Bostr\u00f6m',
    'Charly Lownoise & Mental Theo',
    'Party Animals;Flamman & Abraxas',
    'Bl\u00fcmchen',
    "Mark 'Oh", 'Ti\u00ebsto',
    'SRNDE;one more cig', 'SRNDE;Kin Alura',
    'Daft Punk;Julian Casablancas',
    'Daft Punk;Pharrell Williams;Nile Rodgers',
    'M\u00f6tley Cr\u00fce',
    'Vive La F\u00eate',
    'C\u00e9line Dion',
}

# ─── Genres die IMMER bleiben (Dark Wave / EBM / Industrial / Synthpop) ──────
KEEP_GENRES = {
    'darkwave', 'dark wave', 'cold wave',
    'ebm', 'industrial', 'industrial metal', 'industrial rock',
    'synthpop', 'new wave', 'post-punk',
    'gothic rock', 'deathrock',
    'neue deutsche welle', 'ndw',
    'electro', 'krautrock',
    'italo disco',
    'madchester',
    'punk',
}

def has_keep_genre(genre_str):
    """Prüft ob mindestens ein Genre in der Keep-Liste ist."""
    if not genre_str.strip():
        return False
    genres = [g.strip().lower() for g in genre_str.split(',')]
    return any(g in KEEP_GENRES for g in genres)


# ─── Hauptfilter ─────────────────────────────────────────────────────────────
def should_keep(artist, genre_str):
    """Entscheidet ob ein Song behalten wird."""
    # Hauptartist (vor ;)
    main_artist = artist.split(';')[0].strip()

    # 1. Bekannter Artist → immer behalten
    if artist in ALWAYS_KEEP_ARTISTS or main_artist in ALWAYS_KEEP_ARTISTS:
        return True, "bekannter Artist"

    # 2. Genre ist Dark Wave/EBM/Synthpop/etc → behalten
    if has_keep_genre(genre_str):
        return True, "passendes Genre"

    # 3. Genre ist komplett unpassend → raus
    if genre_should_remove(genre_str):
        return False, "unpassendes Genre"

    # 4. Bekannte Genres (disco, eurodance, etc.) mit bekannten Songs → behalten
    known_dance_genres = {'disco', 'eurodance', 'europop', 'italo dance',
                          'hi-nrg', 'post-disco', 'boogie',
                          'hard rock', 'metal', 'heavy metal',
                          'klassischer rock', 'rock', 'aor', 'arena rock',
                          'rock \'n\' roll', 'new jack swing',
                          'happy hardcore', 'hardcore', 'trance',
                          'schwedischer pop', 'dance',
                          'disco house', 'french house',
                          'britpop', 'alternative rock', 'grunge', 'post-grunge',
                          'alternative dance',
                          'pop rock', 'soft rock',
                          'funk', 'funk rock',
                          'neue deutsche welle',
                          }
    if genre_str:
        song_genres = {g.strip().lower() for g in genre_str.split(',')}
        if song_genres & known_dance_genres:
            return False, "unbekannter Artist (bekanntes Genre)"

    # 5. Rest: unbekannter Artist ohne passendes Genre → raus
    return False, "unbekannter Artist"


# ─── CSV filtern ─────────────────────────────────────────────────────────────
rows_keep = []
rows_remove = []

with open(INFILE, encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        artist = row.get('Artist Name(s)', '').strip()
        genre = row.get('Genres', '').strip()
        keep, reason = should_keep(artist, genre)
        if keep:
            rows_keep.append(row)
        else:
            rows_remove.append((row, reason))

# Neues CSV schreiben
with open(OUTFILE, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows_keep)

# Stats
kept_artists = Counter(r.get('Artist Name(s)', '').split(';')[0].strip() for r in rows_keep)
removed_by_reason = Counter(reason for _, reason in rows_remove)

print(f'=== Ergebnis ===')
print(f'Behalten: {len(rows_keep)} Songs von {len(kept_artists)} Interpreten')
print(f'Entfernt: {len(rows_remove)} Songs')
print(f'  davon: {removed_by_reason}')
print(f'\nGespeichert in: {OUTFILE}')

print(f'\n--- Entfernte Songs (Auswahl) ---')
for row, reason in sorted(rows_remove, key=lambda x: x[0].get('Artist Name(s)', '').lower())[:50]:
    a = row.get('Artist Name(s)', '').split(';')[0].strip()
    t = row.get('Track Name', '').split(' - ')[0].split(';')[0].strip()
    g = row.get('Genres', '')[:30]
    print(f'  {reason:20s}  {a:30s}  {t:35s}  [{g}]')

print(f'\n  ... und {max(0, len(rows_remove)-50)} weitere')
