"""
mythos_data.py — Static reference data for the Call of Cthulhu Investigator skill.
Roaring '20s era (1920–1929). All historical organizations and persons are real;
Mythos interpretations are fictional game content.
"""

# ── US Regional Mythos Entity Associations ───────────────────────────────────
# For the Keeper to draw on when interpreting found history.

REGIONAL_ENTITIES = {
    "New England": {
        "entities": ["Deep Ones", "Shoggoths", "Byakhee", "Nightgaunts", "Dimensional Shamblers"],
        "cults": ["Esoteric Order of Dagon", "Cult of the Skull", "The Brotherhood of the Beast"],
        "flavor": (
            "Lovecraft's own territory. Ancient fishing villages hide blasphemous hybrids. "
            "Old families with too-wide mouths and bulging eyes. Miskatonic University in Arkham "
            "harbors secrets in its restricted library stacks. The sea whispers to those who listen."
        ),
        "states": ["ME", "NH", "VT", "MA", "RI", "CT"],
    },
    "Mid-Atlantic": {
        "entities": ["Dimensional Shamblers", "Byakhee", "Dark Young of Shub-Niggurath", "Hunting Horrors"],
        "cults": ["The Silver Twilight Lodge", "Ordo Templi Orientis (corrupted cell)", "The Order of the Bloated Woman"],
        "flavor": (
            "Teeming immigrant cities where Old World cults find fertile soil. Tenement basements "
            "serve as temple spaces. Corrupt Tammany politicians make deals with things older than "
            "the Republic. The docks of New York and Philadelphia hide cargoes that should never "
            "have crossed the Atlantic."
        ),
        "states": ["NY", "NJ", "PA", "DE", "MD"],
    },
    "Deep South": {
        "entities": ["Lloigor", "Dark Young of Shub-Niggurath", "Formless Spawn of Tsathoggua", "Star Vampires"],
        "cults": ["The Cult of Ghatanothoa", "Voodoo sects corrupted by Mythos contact", "The Esoteric Order of Y'ha-nthlei"],
        "flavor": (
            "Ancient bayous conceal things that predate European colonization. Voodoo traditions "
            "sometimes brush against genuine cosmic horror. New Orleans jazz clubs above, unspeakable "
            "rites below. The heat, the decay, the moss-draped oaks — all conspire to blur the line "
            "between the living and the dead."
        ),
        "states": ["LA", "MS", "AL", "GA", "SC", "FL", "AR", "TN"],
    },
    "Midwest": {
        "entities": ["Ithaqua the Wind-Walker", "Fire Vampires", "Hunting Horrors", "Mi-Go"],
        "cults": ["The Brotherhood of the Black Pharaoh", "Ithaqua death-cults", "Grain cult survivals"],
        "flavor": (
            "Flat horizons where something enormous could approach unseen. Prairie storms that seem "
            "to have intent. Isolated farmsteads where families have worshipped wrongly for generations. "
            "Chicago's slaughterhouses mask a different kind of sacrifice. The Mississippi river system "
            "carries things downstream that defy description."
        ),
        "states": ["IL", "IN", "OH", "MI", "WI", "MN", "IA", "MO", "ND", "SD", "NE", "KS"],
    },
    "Mountain West": {
        "entities": ["Mi-Go", "Elder Things (remnants)", "Chthonians", "Sand Dwellers"],
        "cults": ["The Cult of the Bloody Tongue", "Mi-Go mining operations (disguised as legitimate mines)"],
        "flavor": (
            "The Rockies and desert Southwest are geologically ancient — some of those formations "
            "are not entirely natural. Native American legends contain warnings that white men "
            "dismiss as superstition. Mi-Go have mined these mountains since before human memory. "
            "Mining camps disappear. Survey parties return missing members."
        ),
        "states": ["MT", "ID", "WY", "CO", "UT", "NV", "AZ", "NM"],
    },
    "Pacific Coast": {
        "entities": ["Star Spawn of Cthulhu", "Deep Ones", "Mi-Go", "Lloigor", "Gnoph-Keh"],
        "cults": ["The Esoteric Order of Dagon (West Coast cells)", "Tcho-Tcho communities", "Chinese tong fronts for deeper cults"],
        "flavor": (
            "The Pacific is vast and R'lyeh sleeps beneath it. San Francisco's Chinatown conceals "
            "knowledge from the East. The logging camps of the Pacific Northwest have their own "
            "horrors among the ancient trees. Theosophy and occultism flourish in California's "
            "warm climate, some practitioners stumbling onto genuine power."
        ),
        "states": ["CA", "OR", "WA"],
    },
    "Southwest": {
        "entities": ["Cthugha", "Formless Spawn", "Chthonians", "Sand Dwellers"],
        "cults": ["Fire cult survivals", "Pre-Columbian Mythos cults with living descendants"],
        "flavor": (
            "Ancient desert civilizations left more than pottery shards. The Anasazi did not simply "
            "'disappear.' Oil prospectors sometimes drill into things that should remain sealed. "
            "The border between the US and Mexico is also the border between two worlds of folklore, "
            "both pointing at the same underlying truths."
        ),
        "states": ["TX", "OK"],
    },
}

# ── Real Occult Organizations Active in the 1920s ────────────────────────────

OCCULT_ORGS = [
    {
        "name": "Ordo Templi Orientis (OTO)",
        "founded": 1904,
        "leader": "Aleister Crowley (from 1922)",
        "us_presence": "New York, San Francisco, Detroit",
        "real_activities": "Thelemic magic, ritual sex magic, publication of occult texts",
        "mythos_twist": (
            "A corrupted cell has acquired a fragment of genuine Mythos text mistaken for Enochian "
            "correspondence. Their 'Aiwass' communications are drawing the attention of something real."
        ),
        "wiki_search": "Ordo Templi Orientis",
    },
    {
        "name": "Theosophical Society",
        "founded": 1875,
        "leader": "Annie Besant",
        "us_presence": "National headquarters in Wheaton, IL; lodges in most major cities",
        "real_activities": "Esoteric philosophy, Eastern religion study, racial evolution theories",
        "mythos_twist": (
            "Their concept of 'Root Races' occasionally stumbles close to actual Elder Thing "
            "pre-human history. Some senior members have had contact with Mi-Go posing as 'Mahatmas.'"
        ),
        "wiki_search": "Theosophical Society",
    },
    {
        "name": "Ancient Mystical Order Rosae Crucis (AMORC)",
        "founded": 1915,
        "leader": "Harvey Spencer Lewis",
        "us_presence": "San Jose, CA (headquarters); nationwide correspondence members",
        "real_activities": "Rosicrucian philosophy, mysticism, mail-order initiations",
        "mythos_twist": (
            "Their San Jose headquarters was built on land with unusual geological properties. "
            "Lewis has unwittingly incorporated fragments of De Vermis Mysteriis into their teachings."
        ),
        "wiki_search": "Ancient Mystical Order Rosae Crucis",
    },
    {
        "name": "Society for Psychical Research (American branch)",
        "founded": 1885,
        "leader": "Various academics",
        "us_presence": "Boston, New York",
        "real_activities": "Scientific investigation of paranormal phenomena, mediums, hauntings",
        "mythos_twist": (
            "They have documented three genuine Mythos incidents, filed as 'unexplained.' "
            "The investigators who worked those cases are no longer employed — or alive."
        ),
        "wiki_search": "American Society for Psychical Research",
    },
    {
        "name": "Ku Klux Klan (Second Era)",
        "founded": 1915,
        "leader": "Hiram Wesley Evans (Imperial Wizard from 1922)",
        "us_presence": "3–6 million members nationwide; especially strong in Midwest and South",
        "real_activities": "White supremacist terrorism, political corruption, cross burnings",
        "mythos_twist": (
            "A few klaverns have accidentally incorporated genuine pre-Christian ritual elements "
            "into their ceremonies. Something has taken notice and begun answering."
        ),
        "wiki_search": "Ku Klux Klan",
    },
    {
        "name": "Spiritualist Movement",
        "founded": "1840s revival; 1920s peak post-WWI",
        "leader": "Decentralized; Arthur Conan Doyle as prominent advocate",
        "us_presence": "Lily Dale Assembly (NY), Camp Chesterfield (IN), nationwide",
        "real_activities": "Séances, mediumship, communication with the dead",
        "mythos_twist": (
            "Most mediums are frauds. A small number have accidentally opened genuine channels — "
            "not to the dead, but to things that pretend to be the dead. Lily Dale has a problem."
        ),
        "wiki_search": "Spiritualism movement United States",
    },
]

# ── Key Historical Figures (CoC NPC Seeds) ───────────────────────────────────

HISTORICAL_NPCS = [
    {
        "name": "Aleister Crowley",
        "born": 1875, "died": 1947,
        "occupation": "Occultist, writer, mountaineer",
        "location_1920s": "New York, then Paris and various",
        "real_claim_to_fame": "Founded Thelema; wrote extensively on ceremonial magic",
        "coc_role": (
            "Knows more than he lets on. Has had genuine Mythos contact but interprets it through "
            "his own framework. Useful contact but deeply untrustworthy. Has enemies in three "
            "dimensions, not all of them human."
        ),
        "skills": ["Occult 95", "Library Use 80", "Persuade 70", "Cthulhu Mythos 25"],
    },
    {
        "name": "Harry Houdini",
        "born": 1874, "died": 1926,
        "occupation": "Escape artist, magician, fraud debunker",
        "location_1920s": "New York; touring nationally",
        "real_claim_to_fame": "Greatest escape artist of his era; collaborated with Lovecraft",
        "coc_role": (
            "Actively investigating fraudulent mediums — but has encountered one or two genuine cases "
            "he cannot explain and will not speak of publicly. Would make a remarkable ally. "
            "Actually co-wrote a story with Lovecraft in 1924."
        ),
        "skills": ["Lockpicking 99", "Spot Hidden 75", "Psychology 65", "Cthulhu Mythos 8"],
    },
    {
        "name": "Edgar Cayce",
        "born": 1877, "died": 1945,
        "occupation": "Psychic, faith healer",
        "location_1920s": "Dayton, OH then Virginia Beach, VA",
        "real_claim_to_fame": "The 'Sleeping Prophet'; gave thousands of trance readings",
        "coc_role": (
            "In trance, Cayce accesses something genuine — but it is not the Akashic Records he "
            "believes it to be. His readings occasionally contain accurate Mythos geography (Atlantis "
            "as R'lyeh analogue, the Hall of Records beneath the Sphinx). He has no idea."
        ),
        "skills": ["Psychoanalysis 60", "Medicine 45", "Cthulhu Mythos 15 (unwitting)"],
    },
    {
        "name": "H.P. Lovecraft",
        "born": 1890, "died": 1937,
        "occupation": "Writer, amateur journalist",
        "location_1920s": "Providence, RI; briefly New York (1924–1926)",
        "real_claim_to_fame": "Created the Cthulhu Mythos in fiction",
        "coc_role": (
            "His stories are not entirely fiction. He dreams things, then writes them down as "
            "'weird tales.' His knowledge of Mythos geography and entity behavior is uncannily "
            "accurate. He is also a reclusive eccentric who will not believe his own nightmares "
            "are real, even when confronted with evidence."
        ),
        "skills": ["Library Use 90", "History 85", "Write (English) 80", "Cthulhu Mythos 35"],
    },
    {
        "name": "Charles Fort",
        "born": 1874, "died": 1932,
        "occupation": "Writer, anomalist",
        "location_1920s": "New York City; London",
        "real_claim_to_fame": "Catalogued thousands of unexplained phenomena; coined 'teleportation'",
        "coc_role": (
            "Fort's files contain dozens of genuine Mythos incidents, carefully documented but "
            "attributed to his general theory of cosmic prankstering. His notebooks are a goldmine "
            "for investigators who can separate signal from noise."
        ),
        "skills": ["Library Use 95", "History 70", "Spot Hidden 80", "Cthulhu Mythos 40"],
    },
    {
        "name": "Manly P. Hall",
        "born": 1901, "died": 1990,
        "occupation": "Occultist, author",
        "location_1920s": "Los Angeles, CA",
        "real_claim_to_fame": "Published 'The Secret Teachings of All Ages' (1928)",
        "coc_role": (
            "Young, brilliant, and dangerously close to genuine Mythos knowledge in his research. "
            "His 1928 encyclopedia synthesizes material that should never have been combined. "
            "Something in Los Angeles has taken an interest in him."
        ),
        "skills": ["Occult 85", "Library Use 90", "History 75", "Cthulhu Mythos 20"],
    },
]

# ── Period-Appropriate Forbidden Tomes ───────────────────────────────────────

FORBIDDEN_TOMES = [
    {
        "title": "Necronomicon",
        "author": "Abdul Alhazred (attr.)",
        "language": "Various translations; Dee's English version rumored",
        "where_found": "Locked stacks of Miskatonic University; private collectors; certain antique dealers",
        "coc_stats": "Sanity Loss 2d10 / Cthulhu Mythos +15 / Spell Multiplier ×5 / Study 52 weeks",
    },
    {
        "title": "The King in Yellow",
        "author": "Unknown",
        "language": "English (widely circulated since 1895)",
        "where_found": "Bookshops, libraries; not restricted — yet",
        "coc_stats": "Sanity Loss 1d6 / Cthulhu Mythos +3 / Spell Multiplier ×2 / Study 2 weeks",
        "note": "Masquerades as a mundane play. The second act is the problem.",
    },
    {
        "title": "De Vermis Mysteriis (Mysteries of the Worm)",
        "author": "Ludwig Prinn",
        "language": "Latin; partial translations exist",
        "where_found": "European antiquarian dealers; occasionally surfaces at estate sales",
        "coc_stats": "Sanity Loss 1d8 / Cthulhu Mythos +12 / Spell Multiplier ×4 / Study 30 weeks",
    },
    {
        "title": "Unaussprechlichen Kulten (Nameless Cults)",
        "author": "Friedrich von Junzt",
        "language": "German; Bridewall English translation (1845)",
        "where_found": "University libraries with strong German collections; occult bookshops",
        "coc_stats": "Sanity Loss 1d8 / Cthulhu Mythos +12 / Spell Multiplier ×3 / Study 26 weeks",
    },
    {
        "title": "The Secret Teachings of All Ages",
        "author": "Manly P. Hall",
        "language": "English",
        "where_found": "Widely available on publication (1928); does not appear dangerous",
        "coc_stats": "Sanity Loss 0 / Cthulhu Mythos +2 / Study 8 weeks",
        "note": "Contains accurate Mythos fragments Hall mistook for allegory.",
    },
    {
        "title": "The Pnakotic Manuscripts",
        "author": "Unknown (pre-human origin)",
        "language": "Various fragmentary translations",
        "where_found": "Miskatonic restricted stacks; certain museum basements",
        "coc_stats": "Sanity Loss 1d6 / Cthulhu Mythos +8 / Spell Multiplier ×2 / Study 20 weeks",
    },
]

# ── Real Weird Events 1900–1930 (Historical Seed Events) ─────────────────────

HISTORICAL_SEED_EVENTS = [
    {
        "event": "The Axeman of New Orleans",
        "date": "1918–1919",
        "location": "New Orleans, LA",
        "real_facts": (
            "Serial killer entered homes through chiseled-out door panels; killed with axes. "
            "Wrote a letter promising to spare any home playing jazz. Never identified. "
            "Killings stopped as suddenly as they started."
        ),
        "mythos_angle": "The axeman was not human. The jazz demand was a specific frequency requirement.",
    },
    {
        "event": "The Vanishing of the Flannan Isles Lighthouse Keepers",
        "date": "December 1900",
        "location": "Scotland (but widely reported in US press)",
        "real_facts": "Three lighthouse keepers vanished without explanation. Half-eaten meal left. Chairs overturned.",
        "mythos_angle": "Deep One contact. The keepers saw something in the water.",
    },
    {
        "event": "The Bath School Disaster",
        "date": "May 18, 1927",
        "location": "Bath Township, MI",
        "real_facts": (
            "Andrew Kehoe, a school board treasurer, bombed an elementary school killing 38 children "
            "and 6 adults — the deadliest mass murder at a US school. His motive remains debated."
        ),
        "mythos_angle": "Kehoe's farm had an underground feature he refused to explain. His diaries were never fully published.",
    },
    {
        "event": "The Black Tom explosion",
        "date": "July 30, 1916",
        "location": "Black Tom Island, NJ",
        "real_facts": (
            "German saboteurs destroyed a major US munitions depot. The explosion was felt as far "
            "as Philadelphia and Maryland. The Statue of Liberty's torch was permanently damaged."
        ),
        "mythos_angle": "The German agents were looking for something stored in the munitions facility. They found it.",
    },
    {
        "event": "The Great Molasses Flood",
        "date": "January 15, 1919",
        "location": "Boston, MA",
        "real_facts": (
            "A 2.3-million-gallon molasses tank exploded in Boston's North End. A wave 25 feet high "
            "traveling 35 mph killed 21 and injured 150. Locals claim they can still smell molasses on hot days."
        ),
        "mythos_angle": "The tank was not well-maintained because management feared what workers would find in the sediment.",
    },
    {
        "event": "Spiritualism boom post-WWI",
        "date": "1918–1928",
        "location": "Nationwide",
        "real_facts": (
            "Millions of Americans turned to spiritualism after WWI losses. Mediums flourished. "
            "Lily Dale (NY) became a major spiritualist community. Houdini spent his final years "
            "debunking fraudulent mediums."
        ),
        "mythos_angle": "The desperate grief of millions created a genuine psychic resonance that something old noticed.",
    },
    {
        "event": "The Radium Girls",
        "date": "1917–1924",
        "location": "Orange, NJ and Ottawa, IL",
        "real_facts": (
            "Young women who painted radium watch dials were encouraged to point brushes with lips. "
            "Developed radiation sickness, bone necrosis, jaw disintegration. US Radium Corp. covered it up."
        ),
        "mythos_angle": "The factory floor glowed at night. Not all of it was radium.",
    },
]

# ── 1920s Investigator Background Context ────────────────────────────────────

PERIOD_CONTEXT = {
    "newspapers": [
        "The New York Times", "The Chicago Tribune", "The Boston Globe",
        "The Los Angeles Times", "The Atlanta Constitution",
        "The Police Gazette (sensationalist, useful for weird crimes)",
        "Weird Tales magazine (launched 1923 — sometimes more accurate than it seems)",
    ],
    "institutions": {
        "Miskatonic University": "Arkham, MA — fictional but can be placed near any New England city",
        "Arkham Sanitarium": "Arkham, MA — fictional; analog for any period asylum",
        "The Pinkerton National Detective Agency": "Real; investigators sometimes hired by or opposed to",
        "Bureau of Investigation (pre-FBI)": "Real federal investigative agency; J. Edgar Hoover director from 1924",
        "The OSS predecessor": "Not yet active; but Military Intelligence Division (MID) exists",
    },
    "transportation": [
        "Automobile travel is possible but roads are poor outside cities",
        "Rail is the primary long-distance transport",
        "Air travel exists but rare and expensive",
        "Transatlantic ships take 5–7 days",
    ],
    "technology": [
        "Telephone widely available in cities; less so in rural areas",
        "Radio broadcasts begin 1920; by 1929 most homes have sets",
        "Silent films; talkies begin 1927",
        "Photography common; flash photography available",
        "Automobiles common but not universal",
    ],
    "social_tensions": [
        "Prohibition (1920–1933) and associated organized crime",
        "The Red Scare (1919–1920) and labor unrest",
        "The Great Migration of Black Americans to Northern cities",
        "Suffrage (19th Amendment, 1920) and changing gender roles",
        "Immigration restriction (Johnson-Reed Act, 1924)",
        "KKK at peak membership (1924–1925)",
        "Jazz Age cultural upheaval",
    ],
}

# ── Wikipedia Search Terms for CoC Research ──────────────────────────────────

SEARCH_TERMS = {
    "occult": [
        "occult secret society",
        "spiritualism medium séance",
        "haunted asylum sanitarium",
        "mystery disappearance unsolved",
        "cult ritual murder",
    ],
    "crime": [
        "murder unsolved 1920s",
        "prohibition gangster bootlegger",
        "kidnapping missing persons",
        "serial killer",
    ],
    "history": [
        "history folklore legend",
        "Native American legend sacred site",
        "industrial disaster accident",
        "abandoned factory mine",
    ],
}


def get_region(state_abbr: str) -> str:
    """Return the Mythos region name for a US state abbreviation."""
    for region, data in REGIONAL_ENTITIES.items():
        if state_abbr.upper() in data.get("states", []):
            return region
    return "Mid-Atlantic"  # default


def region_data(state_abbr: str) -> dict:
    """Return full regional Mythos data for a state."""
    region = get_region(state_abbr)
    return {**REGIONAL_ENTITIES.get(region, {}), "region_name": region}
