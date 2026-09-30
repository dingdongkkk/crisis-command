"""One targeted question per fact, in the caller's language (English, Hindi, Hinglish)."""

from __future__ import annotations

from dataclasses import dataclass

TEXT: dict[str, dict[str, str]] = {
    "conscious": {
        "en": "Is the person conscious and responding to you?",
        "hi": "क्या व्यक्ति होश में है और जवाब दे रहा है?",
        "hinglish": "Kya woh hosh mein hain aur jawab de rahe hain?",
    },
    "breathing_normally": {
        "en": "Is the person breathing normally?",
        "hi": "क्या व्यक्ति सामान्य रूप से साँस ले रहा है?",
        "hinglish": "Kya woh theek se saans le rahe hain?",
    },
    "chest_pain": {
        "en": "Is there chest pain?",
        "hi": "क्या सीने में दर्द है?",
        "hinglish": "Kya seene mein dard hai?",
    },
    "severe_bleeding": {
        "en": "Is anyone bleeding heavily?",
        "hi": "क्या किसी का बहुत खून बह रहा है?",
        "hinglish": "Kya kisi ka bahut khoon beh raha hai?",
    },
    "trapped": {
        "en": "Is anyone trapped or unable to get out?",
        "hi": "क्या कोई फँसा हुआ है या बाहर नहीं निकल पा रहा?",
        "hinglish": "Kya koi phansa hua hai ya bahar nahi nikal pa raha?",
    },
    "fire_or_smoke": {
        "en": "Is there any fire or smoke?",
        "hi": "क्या आग या धुआँ है?",
        "hinglish": "Kya aag ya dhuan hai?",
    },
    "gas_smell": {
        "en": "Can you smell gas?",
        "hi": "क्या गैस की गंध आ रही है?",
        "hinglish": "Kya gas ki badbu aa rahi hai?",
    },
    "water_rising": {
        "en": "Is the water rising?",
        "hi": "क्या पानी बढ़ रहा है?",
        "hinglish": "Kya paani badh raha hai?",
    },
    "caller_in_danger": {
        "en": "Are you in danger where you are right now?",
        "hi": "क्या आप अभी जहाँ हैं वहाँ खतरे में हैं?",
        "hinglish": "Kya aap abhi jahan hain wahan khatre mein hain?",
    },
    "people_count": {
        "en": "How many people are affected?",
        "hi": "कितने लोग प्रभावित हैं?",
        "hinglish": "Kitne log prabhavit hain?",
    },
}
ANSWERS: dict[str, tuple[str, str, str]] = {
    "en": ("Yes", "No", "Not sure"),
    "hi": ("हाँ", "नहीं", "पता नहीं"),
    "hinglish": ("Haan", "Nahi", "Pata nahi"),
}


@dataclass(frozen=True)
class Question:
    fact_key: str
    language: str
    text: str
    answers: tuple[str, str, str]  # labels for yes / no / unknown ("Not sure")
    numeric: bool = False


def question_for(fact_key: str, language: str) -> Question:
    lang = language if language in ANSWERS else "en"
    return Question(
        fact_key, lang, TEXT[fact_key][lang], ANSWERS[lang], numeric=fact_key == "people_count"
    )
