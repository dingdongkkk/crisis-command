"""Multilingual phrase lexicon for the deterministic rule adapter (English, Hindi, Hinglish).

Each pattern is a phrase that *by itself* supports one value of one fact, so the matched
span is valid evidence (decision 0002 rule 2). Negation is expressed as explicit phrases
("not breathing", "saans nahi"), never as a generic "negation nearby" heuristic.
Devanagari patterns avoid ``\\b`` because word boundaries are unreliable with matras.
This is a demonstration lexicon, not a clinical instrument.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FLAGS = re.IGNORECASE | re.UNICODE


def _p(*patterns: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p, FLAGS) for p in patterns)


# fact key -> value -> patterns
FACT_PATTERNS: dict[str, dict[str, tuple[re.Pattern[str], ...]]] = {
    "breathing_normally": {
        "no": _p(
            r"\bnot breathing\b",
            r"\bisn'?t breathing\b",
            r"\bstopped breathing\b",
            r"\bno breath(?:ing)?\b",
            r"\bcan(?:no|')?t breathe\b",
            r"\bunable to breathe\b",
            r"\bgasping\b",
            r"\bstruggling to breathe\b",
            r"\bsaa?ns? (?:nahi|nahin|nhi|na) (?:le|aa)\w*",
            r"\bsaa?ns? (?:band|ruk)\w*",
            r"साँस नहीं",
            r"सांस नहीं",
            r"साँस बंद",
            r"सांस बंद",
            r"साँस रुक",
            r"सांस रुक",
        ),
        "yes": _p(
            r"\bbreathing (?:normally|fine|okay|ok|normal)\b",
            r"\bis breathing\b",
            r"\bbreathing is (?:normal|fine|ok)\b",
            r"\bsaa?ns? (?:le )?(?:raha|rahi|rahe) (?:hai|he|hain)\b",
            r"\bsaa?ns? theek\b",
            r"साँस ले रह",
            r"सांस ले रह",
            r"साँस ठीक",
            r"सांस ठीक",
        ),
    },
    "conscious": {
        "no": _p(
            r"\bunconscious\b",
            r"\bnot conscious\b",
            r"\bpassed out\b",
            r"\bfainted\b",
            r"\bnot responding\b",
            r"\bunresponsive\b",
            r"\bnot waking up\b",
            r"\bwon'?t wake up\b",
            r"\bbehosh\b",
            r"\bhosh (?:nahi|nahin|nhi)\b",
            r"\bjawab (?:nahi|nahin|nhi) de\w*",
            r"बेहोश",
            r"होश नहीं",
            r"जवाब नहीं दे",
        ),
        "yes": _p(
            r"\bis conscious\b",
            r"\bconscious and (?:talking|responding|alert)\b",
            r"\bawake\b",
            r"\btalking to (?:me|us)\b",
            r"\bis responding\b",
            r"\bhosh (?:mein|me|mai) (?:hai|he|hain)\b",
            r"\bbaat kar (?:raha|rahi|rahe)\b",
            r"होश में है",
            r"होश में हैं",
            r"बात कर रह",
        ),
    },
    "chest_pain": {
        "yes": _p(
            r"\bchest pain\b",
            r"\bpain in (?:his|her|my|the) chest\b",
            r"\bheart attack\b",
            r"\bchest (?:is )?hurting\b",
            r"\bseene? (?:mein|me|mai) (?:\w+ )?dard\b",
            r"\bchhati (?:mein|me|mai) (?:\w+ )?dard\b",
            r"\bchest (?:is )?(?:tight|hurts|hurting)\b",
            r"\bdil ka daura\b",
            r"सीने में (?:\S+ )?दर्द",
            r"छाती में दर्द",
            r"दिल का दौरा",
        ),
        "no": _p(
            r"\bno chest pain\b", r"\bseene? (?:mein|me) dard (?:nahi|nahin)\b", r"सीने में दर्द नहीं"
        ),
    },
    "severe_bleeding": {
        "yes": _p(
            r"\bbleeding (?:heavily|a lot|badly|profusely)\b",
            r"\bheavy bleeding\b",
            r"\b(?:a )?lot of blood\b",
            r"\bblood everywhere\b",
            r"\bbahut khoon\b",
            r"\bkhoon beh\w*",
            r"\bkhoon nikal\w*",
            r"बहुत खून",
            r"खून बह",
            r"खून निकल",
        ),
        "no": _p(
            r"\bno bleeding\b",
            r"\bnot bleeding\b",
            r"\b(?:small|minor|little|tiny|slight) (?:cut|scratch|graze|wound)\b",
            r"\bkhoon (?:nahi|nahin)\b",
            r"खून नहीं",
        ),
    },
    "trapped": {
        "yes": _p(
            r"\btrapped\b",
            r"\bstuck (?:under|inside|in the|in a)\b",
            r"\bpinned\b",
            r"\bcan(?:no|')?t get out\b",
            r"\bunable to get out\b",
            r"\bburied\b",
            r"\bstuck in (?:the )?(?:water|flood\w*|mud)\b",
            r"\bstuck (?:on|at) the (?:\w+ )?(?:floor|roof|terrace|balcony)\b",
            r"\b(?:under|beneath) (?:the )?(?:debris|rubble)\b",
            r"\bpaani (?:mein|me) phans\w*",
            r"पानी में फंस",
            r"\bphans(?:e|a|i|ay)\b",
            r"\bdab(?:e|a|i) (?:hue|hua|hui)\b",
            r"फँस",
            r"फंस",
            r"दबे हुए",
            r"दबा हुआ",
            r"दबी हुई",
        ),
        "no": _p(
            r"\bnot trapped\b",
            r"\bnobody (?:is )?trapped\b",
            r"\bno one (?:is )?trapped\b",
            r"\beveryone (?:is |got )?out\b",
            r"\bsab bahar\b",
            r"कोई नहीं फंसा",
            r"सब बाहर",
        ),
    },
    "fire_or_smoke": {
        "yes": _p(
            r"\bfire\b(?! brigade)",
            r"\bsmoke\b",
            r"\bflames?\b",
            r"\bburning\b",
            r"\bon fire\b",
            r"\baag\b",
            r"\bdhu[aā]n\b",
            r"आग",
            r"धुआं",
            r"धुआँ",
        ),
        "no": _p(r"\bno fire\b", r"\bno smoke\b", r"\baag (?:nahi|nahin)\b", r"आग नहीं"),
    },
    "gas_smell": {
        "yes": _p(
            r"\bgas leak\w*",
            r"\bgas (?:is )?leaking\b",
            r"\bsmell(?:s|ing)? (?:of )?gas\b",
            r"\bgas smell\b",
            r"\bleaking gas\b",
            r"\bgas ki (?:badbu|smell|gandh)\b",
            r"गैस",
            r"गैस की गंध",
        ),
        "no": _p(
            r"\bno gas smell\b", r"\bno smell of gas\b", r"\bgas (?:ki )?badbu (?:nahi|nahin)\b"
        ),
    },
    "water_rising": {
        "yes": _p(
            r"\bwater (?:is )?(?:still )?rising\b",
            r"\bwater level (?:is )?(?:rising|increasing|going up)\b",
            r"\bflood(?:ing|ed)?\b",
            r"\bwater (?:is )?(?:entering|coming in(?:side|to)?)\b",
            r"\bwater up to\b",
            r"\bpaani badh\w*",
            r"\bpaani bhar\w*",
            r"\bpaani andar\b",
            r"पानी बढ़",
            r"पानी भर",
            r"बाढ़",
        ),
        "no": _p(r"\bwater (?:is )?(?:receding|going down)\b", r"\bpaani kam\b", r"पानी कम"),
    },
    "caller_in_danger": {
        "yes": _p(
            r"\bi am (?:trapped|stuck|in danger)\b",
            r"\bi'?m (?:trapped|stuck|in danger)\b",
            r"\bwe are (?:trapped|stuck|in danger)\b",
            r"\bfollowing (?:me|us)\b",
            r"\b(?:attacking|threatening|chasing) (?:me|us)\b",
            r"\bwith a (?:knife|gun|weapon)\b",
            r"\b(?:i'?m|i am|we are|we'?re) hiding\b",
            r"\bmujhe bachao\b",
            r"\bhume bachao\b",
            r"\bbachao\b",
            r"मुझे बचाओ",
            r"बचाओ",
        ),
        "no": _p(
            r"\bi am safe\b",
            r"\bi'?m safe\b",
            r"\bwe are safe\b",
            r"\bmain surakshit\b",
            r"मैं सुरक्षित",
        ),
    },
}

HUMAN_REQUEST = _p(
    r"\b(?:talk|speak) to (?:a |an )?(?:human|person|operator|real person|someone)\b",
    r"\b(?:human|operator) please\b",
    r"\bconnect me to (?:a |an )?(?:human|person|operator)\b",
    r"\binsaan se baat\w*",
    r"\bkisi (?:insaan )?se baat\w*",
    r"\bkisi aadmi se baat\w*",
    r"\boperator se baat\w*",
    r"किसी इंसान से बात",
    r"किसी से बात",
    r"इंसान से बात",
)

# Words that signal a possibly critical situation. If the model is unavailable and one of
# these appears outside every evidence span, the rules could not classify it: escalate.
CRITICAL_KEYWORDS = _p(
    r"\bblood\b",
    r"\bbleed\w*",
    r"\bbreath\w*",
    r"\bunconscious\b",
    r"\bfaint\w*",
    r"\bheart\b",
    r"\bchest\b",
    r"\btrapped\b",
    r"\bfire\b",
    r"\bsmoke\b",
    r"\bgas\b",
    r"\bcollaps\w*",
    r"\bdrown\w*",
    r"\belectrocut\w*",
    r"\bpoison\w*",
    r"\boverdose\b",
    r"\bseizure\w*",
    r"\bfits?\b",
    r"\bstroke\b",
    r"\bsuicid\w*",
    r"\bchoking\b",
    r"\bkhoon\b",
    r"\bsaans\b",
    r"\bbehosh\b",
    r"\bdaura\b",
    r"\baag\b",
    r"\bzeher\b",
    r"\bdoob\w*",
    r"\bkarant\b",
    r"खून",
    r"साँस",
    r"सांस",
    r"बेहोश",
    r"दौरा",
    r"आग",
    r"ज़हर",
    r"जहर",
    r"डूब",
    r"करंट",
)

# Instruction-like text aimed at a model. Its presence discards model output for the report.
INJECTION_MARKERS = _p(
    r"\bignore (?:all |the |your )?(?:previous|prior|above) (?:instructions|rules|prompts?)\b",
    r"\bdisregard (?:all |the )?(?:previous|prior|above)\b",
    r"\bsystem prompt\b",
    r"\byou are now\b",
    r"\b(?:mark|set|classify|record) (?:the |this |all )?(?:\w+ ){0,3}(?:as|to) (?:no|yes|unknown|safe|non[- ]emergency|low)\b",
    r"\bjson\b.*\b(?:value|key)\b",
    r"</?\w+>",
)


@dataclass(frozen=True)
class KindRule:
    kind: str
    category: str
    patterns: tuple[re.Pattern[str], ...]


# Ordered: the first matching rule wins. Kind hints are display/intake hints; assessment
# (CC-05) derives severity and needs from facts, not from these words alone.
KIND_RULES: tuple[KindRule, ...] = (
    KindRule(
        "information_request",
        "information_request",
        _p(
            r"\b(?:is|are)\b.{0,40}\b(?:road|roads|route|ORR|bridge|flyover|highway|underpass)\b.{0,25}\b(?:open|closed|blocked|clear|jammed|motorable|flooded|waterlogged|submerged)\b",
            r"\b(?:can|should) (?:we|i) (?:take|use)\b.{0,40}\b(?:road|route|ORR|flyover|highway)\b",
            r"\b(?:road|route|ORR|flyover|highway|underpass)\b.{0,30}\b(?:can|should) (?:we|i) (?:take|use)\b",
            r"\broad status\b",
            r"\b(?:any|is there)\b.{0,15}\b(?:waterlogging|traffic|jam|congestion|diversion|road ?block)\b.{0,60}\?",
            r"\bwhen will (?:the )?(?:power|electricity|current|water supply)\b",
            r"\bkya\b.{0,40}\b(?:jam|traffic|band|khula)\b.{0,10}\bhai\b.{0,5}\?",
            r"क्या .{0,40}(?:जाम|ट्रैफिक|बंद|खुला|खुली) है",
            r"\bwhich (?:road|route)\b",
            r"\btraffic (?:update|status)\b",
            r"\b(?:road|rasta|raasta) .{0,20}(?:khula|band) hai\b",
            r"रास्ता .{0,20}(?:खुला|बंद) है",
            r"सड़क .{0,20}(?:खुली|बंद)",
        ),
    ),
    KindRule(
        "structural_collapse",
        "emergency",
        _p(
            r"\b(?:roof|building|wall|ceiling|house|school) (?:has )?(?:collapsed|fell|caved in|came down)\b",
            r"\bcollapse\w*\b",
            r"\b(?:chhat|chat|deewar|imarat|building) gir\w*",
            r"(?:छत|दीवार|इमारत) गिर",
        ),
    ),
    KindRule(
        "gas_leak_evacuation",
        "emergency",
        _p(
            r"\bgas leak\w*",
            r"\bgas (?:is )?leaking\b",
            r"\bsmell(?:s|ing)? (?:of )?gas\b",
            r"\bgas smell\b",
            r"\bgas ki (?:badbu|smell|gandh)\b",
            r"गैस",
        ),
    ),
    KindRule(
        "flood_stranded_vehicle",
        "emergency",
        _p(
            r"\b(?:car|vehicle|bus|auto|bike)\b.{0,40}\b(?:water|flood\w*)\b",
            r"\b(?:water|flood\w*)\b.{0,40}\b(?:car|vehicle|bus|auto)\b",
            r"\b(?:gaadi|gadi|car)\b.{0,30}\bpaani\b",
            r"(?:गाड़ी|कार).{0,30}पानी",
        ),
    ),
    KindRule(
        "road_accident_injuries",
        "emergency",
        _p(
            r"\b(?:accident|crash|collision|hit by|run over|overturned)\b",
            r"\bdurghatna\b",
            r"\btakkar\b",
            r"दुर्घटना",
            r"टक्कर",
            r"एक्सीडेंट",
        ),
    ),
    KindRule(
        "fire",
        "emergency",
        _p(
            r"\bon fire\b",
            r"(?<!\bno )(?<!\bnot a )\bfire\b(?! brigade)",
            r"\baag lag\w*",
            r"आग लग",
        ),
    ),
    KindRule(
        "cardiac_chest_pain",
        "emergency",
        _p(
            r"\bchest pain\b",
            r"\bheart attack\b",
            r"\bpain in (?:his|her|my|the) chest\b",
            r"\bseene? (?:mein|me) dard\b",
            r"\bdil ka daura\b",
            r"सीने में दर्द",
            r"दिल का दौरा",
        ),
    ),
    KindRule(
        "medical_emergency",
        "emergency",
        _p(
            r"\bunconscious\b",
            r"\bnot breathing\b",
            r"\bfainted\b",
            r"\bseizure\b",
            r"\bbleeding\b",
            r"\binjured\b",
            r"\bbehosh\b",
            r"\bsaa?ns? (?:nahi|nahin)\b",
            r"बेहोश",
            r"सांस नहीं",
            r"साँस नहीं",
            r"घायल",
            r"\bghayal\b",
        ),
    ),
    KindRule(
        "vehicle_breakdown",
        "non_emergency_assist",
        _p(
            r"\b(?:flat|punctured?) (?:tyre|tire)\b",
            r"\bpuncture\b",
            r"\b(?:tyre|tire) (?:is )?(?:flat|burst|puncture\w*)\b",
            r"\bbreak ?down\b",
            r"\bbroke down\b",
            r"\b(?:battery|engine) (?:is )?(?:dead|died|down|failed)\b",
            r"\bjump ?start\b",
            r"\bout of (?:fuel|petrol|diesel)\b",
            r"\btree (?:fell|has fallen) on (?:my|the|a|our) (?:parked )?(?:car|bike|vehicle)\b",
            r"\bpankchar\b",
            r"पंक्चर",
        ),
    ),
)

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "hundred": 100,
    "ek": 1,
    "do": 2,
    "teen": 3,
    "char": 4,
    "chaar": 4,
    "paanch": 5,
    "panch": 5,
    "chhe": 6,
    "saat": 7,
    "aath": 8,
    "nau": 9,
    "das": 10,
    "bees": 20,
    "pachaas": 50,
    "sau": 100,
    "एक": 1,
    "दो": 2,
    "तीन": 3,
    "चार": 4,
    "पांच": 5,
    "पाँच": 5,
    "छह": 6,
    "सात": 7,
    "आठ": 8,
    "नौ": 9,
    "दस": 10,
    "बीस": 20,
}
PEOPLE_NOUNS = (
    r"people|persons?|children|kids|students|injured|residents|passengers|victims|workers|men|women|adults|"
    r"log|logo|bacche|bachche|aadmi|yatri|लोग|बच्चे|आदमी|यात्री|घायल|of us|of them"
)
_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
COUNT_PATTERN = re.compile(
    r"(?P<approx>\b(?:about|around|approx(?:imately)?|nearly|roughly|lagbhag|kareeb)\s+|लगभग\s+|करीब\s+)?"
    r"(?P<num>[0-9०-९]+|"
    + "|".join(sorted(map(re.escape, NUMBER_WORDS), key=len, reverse=True))
    + r")"
    r"\s+(?:\w+\s+)?(?P<noun>" + PEOPLE_NOUNS + r")",
    FLAGS,
)
COUNT_UNKNOWN = _p(
    r"\bdon'?t know how many\b",
    r"\bnot sure how many\b",
    r"\bunknown number\b",
    r"\bpata nahi kitne\b",
    r"\bkitne (?:log )?(?:hain )?pata nahi\b",
    r"पता नहीं कितने",
    r"कितने .{0,10}पता नहीं",
)


def parse_number(token: str) -> int | None:
    token = token.translate(_DIGITS).lower()
    if token.isdigit():
        return int(token)
    return NUMBER_WORDS.get(token)
