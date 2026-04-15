KEYWORD_MAP = {
    "World": [
        "world", "global", "international", "foreign policy", "security", "diplomacy"
    ],
    "Geopolitics": [
        "sanctions", "diplomacy", "alliance", "border", "naval", "summit", "treaty", "strategic"
    ],
    "War": [
        "war", "military", "conflict", "strike", "ceasefire", "missile", "troops", "air defense"
    ],
    "Crime": [
        "crime", "cartel", "gang", "trafficking", "homicide", "smuggling", "terror"
    ],
    "India": [
        "India", "Modi", "Quad", "border", "Kashmir", "New Delhi", "Indian Ocean"
    ],
    "Taiwan": [
        "Taiwan", "Taiwan Strait", "China drills", "Taipei", "PLA"
    ],
    "Russia": [
        "Russia", "Putin", "Ukraine", "NATO", "Kremlin", "Moscow"
    ],
    "China": [
        "China", "Xi", "South China Sea", "BRI", "Beijing", "PLA Navy"
    ],
    "Japan": [
        "Japan", "East China Sea", "defense", "Tokyo", "SDF", "Okinawa"
    ],
    "Israel": [
        "Israel", "Gaza", "West Bank", "Jerusalem", "IDF", "Hamas"
    ],
    "Middle East": [
        "Iran", "Saudi", "Hormuz", "Lebanon", "Syria", "Yemen", "Qatar", "Gulf"
    ],
    "Europe": [
        "Europe", "EU", "NATO", "Hungary", "Brussels", "Poland", "Baltic"
    ],
    "USA": [
        "USA", "Trump", "Pentagon", "sanctions", "Washington", "Congress", "White House"
    ],
    "South America": [
        "Brazil", "Argentina", "Venezuela", "cartel", "Colombia", "Ecuador"
    ],
    "Africa": [
        "Sudan", "Sahel", "DRC", "Wagner", "Ethiopia", "Mali", "Niger"
    ],
    "Antarctica": [
        "Antarctica", "polar treaty", "southern ocean", "research base", "ice shelf"
    ],
}

STRATEGIC_RELEVANCE_TERMS = [
    "war", "military", "defense", "security", "missile", "nuclear", "alliance", "naval",
    "border", "ceasefire", "energy", "oil", "sanctions", "summit", "terror", "maritime",
    "indo-pacific", "quad", "china", "russia", "iran", "strait", "indian ocean", "power rivalry"
]

INDIA_IMPACT_AREAS = {
    "border_security": [
        "india", "kashmir", "ladakh", "line of actual control", "line of control", "border",
        "china", "pakistan", "terror", "cross-border"
    ],
    "regional_instability": [
        "south asia", "bangladesh", "myanmar", "sri lanka", "nepal", "maldives", "afghanistan",
        "pakistan", "regional instability"
    ],
    "energy_supply": [
        "oil", "gas", "lng", "energy", "hormuz", "saudi", "iran", "gulf", "shipping", "crude"
    ],
    "maritime_security": [
        "indian ocean", "arabian sea", "bay of bengal", "naval", "maritime", "sea lane",
        "shipping lane", "port", "submarine"
    ],
    "great_power_rivalry": [
        "indo-pacific", "quad", "china", "usa", "russia", "alliance", "strategic autonomy",
        "technology controls", "sanctions", "power rivalry"
    ],
}
SOURCE_FEEDS = [
    {"name": "The Hindu International", "url": "https://www.thehindu.com/news/international/?service=rss", "group": "india_news", "kind": "news_agency"},
    {"name": "Indian Express World", "url": "https://indianexpress.com/section/world/feed/", "group": "india_news", "kind": "news_agency"},
    {"name": "Hindustan Times World", "url": "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml", "group": "india_news", "kind": "news_agency"},
    {"name": "Global Times", "url": "https://www.globaltimes.cn/rss/outbrain.xml", "group": "china_news", "kind": "news_agency"},
    {"name": "Reuters World", "url": "https://feeds.reuters.com/Reuters/worldNews", "group": "global_news", "kind": "news_agency"},
    {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "group": "global_news", "kind": "news_agency"},
    {"name": "Observer Research Foundation", "url": "https://www.orfonline.org/feed/", "group": "india_think_tank", "kind": "think_tank"},
    {"name": "MP-IDSA", "url": "https://idsa.in/rss.xml", "group": "india_think_tank", "kind": "think_tank"},
    {"name": "Vivekananda International Foundation", "url": "https://www.vifindia.org/feed/", "group": "india_think_tank", "kind": "think_tank"},
    {"name": "Gateway House", "url": "https://www.gatewayhouse.in/feed/", "group": "india_think_tank", "kind": "think_tank"},
    {"name": "CSIS", "url": "https://www.csis.org/analysis/feed", "group": "global_strategy", "kind": "think_tank"},
    {"name": "Atlantic Council", "url": "https://www.atlanticcouncil.org/feed/", "group": "global_strategy", "kind": "think_tank"},
    {"name": "RAND", "url": "https://www.rand.org/topics/international-affairs.rss", "group": "global_strategy", "kind": "think_tank"},
    {"name": "Carnegie Russia Eurasia", "url": "https://carnegieendowment.org/rss/regions/russia-eurasia", "group": "regional_strategy", "kind": "think_tank"},
    {"name": "MERICS", "url": "https://www.merics.org/en/rss.xml", "group": "regional_strategy", "kind": "think_tank"},
    {"name": "Institute for the Study of War", "url": "https://www.understandingwar.org/rss.xml", "group": "regional_strategy", "kind": "think_tank"},
    {"name": "INSS", "url": "https://www.inss.org.il/feed/", "group": "regional_strategy", "kind": "think_tank"},
]


CATEGORY_ORDER = list(KEYWORD_MAP.keys())
