#!/usr/bin/env python3
"""Heuristischer Silbenzähler für deutsche Verse.

Python >= 3.10

Aufruf:
    python silben.py "Vers eins" "Vers zwei"
    python silben.py gedicht.txt
    python silben.py -f gedicht.txt --target 8
    python silben.py -f gedicht.txt --target 8 --lexikon ausnahmen.txt
    echo "Ein Vers" | python silben.py

Korrekturlexikon:
    Orient=3
    Queue=1
    Code=1

Grundidee:
    Gezählt werden möglichst die GESPROCHENEN Silben, nicht bloß
    orthografische Trennstellen.

    Schwierige Fälle werden mit ? markiert. Wenn mehrere Silbenzahlen
    plausibel sind, wird ein Bereich ausgegeben, z. B.:

        Orient(3?/2–3)

    Ein Eintrag aus dem Korrekturlexikon erscheint mit *:

        Queue(1*)

pyphen:
    pyphen ist optional und wird ausschließlich zur Anzeige möglicher
    orthografischer Trennstellen verwendet. Seine Trennstellen gelten
    NICHT als Referenz für die gesprochene bzw. metrische Silbenzahl.

Grenzen:
    Aussprachevarianten, Eigennamen, Fremdwörter, Abkürzungen,
    dichterische Elisionen und Synizesen lassen sich aus der
    Schreibweise allein nicht immer sicher bestimmen.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Grunddaten
# ---------------------------------------------------------------------------

BASE_VOWELS = set("aeiou")
GERMAN_VOWELS = set("aeiouäöü")

# Die robustesten deutschen Diphthonge.
CORE_DIPHTHONGS = {
    "ai",
    "au",
    "äu",
    "ei",
    "eu",
}

# Meist ein langer Vokal.
DOUBLE_VOWELS = {
    "aa",
    "ee",
    "oo",
}

# Unicode-Buchstaben, dazu Binnenapostrophe und Bindestrich-Komposita.
WORD_RE = re.compile(
    r"[^\W\d_]+"
    r"(?:['’][^\W\d_]+)*"
    r"(?:[-‐-‒–—][^\W\d_]+(?:['’][^\W\d_]+)*)*",
    re.UNICODE,
)

HYPHEN_RE = re.compile(r"[-‐-‒–—]+")
APOSTROPHE_RE = re.compile(r"['’]")


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class Estimate:
    """Geschätzte Silbenzahl eines Wortes."""

    best: int
    minimum: int
    maximum: int
    reasons: list[str] = field(default_factory=list)
    source: str = "heuristic"

    @property
    def uncertain(self) -> bool:
        return (
            self.minimum != self.maximum
            or bool(self.reasons)
        )


@dataclass
class WordAnalysis:
    word: str
    estimate: Estimate
    pyphen: str | None = None


@dataclass
class LineAnalysis:
    line: str
    words: list[WordAnalysis]
    reasons: list[str] = field(default_factory=list)

    @property
    def best(self) -> int:
        return sum(w.estimate.best for w in self.words)

    @property
    def minimum(self) -> int:
        return sum(w.estimate.minimum for w in self.words)

    @property
    def maximum(self) -> int:
        return sum(w.estimate.maximum for w in self.words)

    @property
    def uncertain(self) -> bool:
        return (
            bool(self.reasons)
            or any(w.estimate.uncertain for w in self.words)
        )


# ---------------------------------------------------------------------------
# Unicode / Vokalerkennung
# ---------------------------------------------------------------------------

def nfc_lower(text: str) -> str:
    return unicodedata.normalize("NFC", text).lower()


def raw_vowel_symbol(ch: str) -> str | None:
    """Gibt den zugrunde liegenden Vokal zurück.

    Auch Buchstaben wie é, ó, â usw. werden als Vokale erkannt.
    """

    c = nfc_lower(ch)

    if c in GERMAN_VOWELS:
        return c

    if c == "y":
        return "y"

    decomp = unicodedata.normalize("NFD", c)

    if decomp and decomp[0] in BASE_VOWELS:
        return decomp[0]

    return None


def is_non_y_vowel(ch: str) -> bool:
    value = raw_vowel_symbol(ch)
    return value is not None and value != "y"


def effective_vowel_symbol(word: str, i: int) -> str | None:
    """Erkennt, ob das Zeichen an Position i einen Silbenkern bilden kann."""

    symbol = raw_vowel_symbol(word[i])

    if symbol is None:
        return None

    # Deutsches quV:
    #
    # Quelle  /kvɛlə/
    # Quadrat /kvaːdʁaːt/
    #
    # Das <u> ist hier kein eigener Silbenkern.
    if symbol == "u" and i > 0 and word[i - 1] == "q":
        if i + 1 < len(word) and is_non_y_vowel(word[i + 1]):
            return None

    # y:
    #
    # Typ, System -> vokalisch
    # Yoga, Maya  -> eher /j/
    #
    # Rein orthografisch ist das nicht vollständig lösbar.
    if symbol == "y":
        prev_vowel = (
            i > 0
            and is_non_y_vowel(word[i - 1])
        )
        next_vowel = (
            i + 1 < len(word)
            and is_non_y_vowel(word[i + 1])
        )

        if prev_vowel or next_vowel:
            return None

        return "y"

    return symbol


# ---------------------------------------------------------------------------
# Positions-/Mustererkennung
# ---------------------------------------------------------------------------

def position_in_pattern(
    word: str,
    i: int,
    pattern: str,
    pair_offset: int,
) -> bool:
    """Prüft eine Vokalgrenze innerhalb eines bekannten Wortmusters.

    Das Muster darf auch innerhalb eines Kompositums auftreten.

    Dadurch funktionieren z. B.:

        kooperativ
        unkooperativ
        Forschungskooperation
    """

    start = word.find(pattern)

    while start >= 0:
        if i == start + pair_offset:
            return True

        start = word.find(pattern, start + 1)

    return False


# ---------------------------------------------------------------------------
# Bekannte Hiatusfälle
# ---------------------------------------------------------------------------

def forced_hiatus(
    word: str,
    i: int,
    pair: str,
) -> tuple[bool, bool, str | None]:
    """Bestimmt, ob zwei benachbarte Vokale getrennt zählen.

    Rückgabe:
        hiatus
        mehrdeutig
        Begründung
    """

    # ---------------------------------------------------------------
    # Feen, Seen, Ideen, Museen, Alleen ...
    #
    # Das <ee> wird hier nicht wie in "Meer" als ein Kern behandelt.
    # ---------------------------------------------------------------

    if pair == "ee" and word[i:i + 3] == "een":
        return True, False, None

    # ---------------------------------------------------------------
    # Museum, Petroleum, Mausoleum, Lyzeum ...
    #
    # <eu> ist hier nicht der deutsche Diphthong wie in "Feuer".
    # ---------------------------------------------------------------

    if pair == "eu" and re.match(r"eum(?:s|$)", word[i:]):
        return True, False, None

    # Geläufige -eum-Stämme auch in Komposita erkennen.
    for stem in ("museum", "petroleum", "mausoleum"):
        start = word.find(stem)

        while start >= 0:
            if i == start + stem.index("eu"):
                return True, False, None

            start = word.find(stem, start + 1)

    # ---------------------------------------------------------------
    # Orient
    #
    # Es existieren unterschiedliche standardsprachliche Realisierungen.
    # ---------------------------------------------------------------

    if (
        pair == "ie"
        and position_in_pattern(word, i, "orient", 2)
    ):
        return (
            True,
            True,
            "Aussprache von ‚Orient…‘ kann die Vokalfolge verschleifen",
        )

    # ---------------------------------------------------------------
    # -rien
    #
    # Batterien, Serien, Materien, Ferien usw.
    #
    # In Komposita ist die Morphemgrenze nicht aus der Schreibweise
    # ableitbar:
    #
    #   Serien|nummer
    #   Industrie|nation
    # ---------------------------------------------------------------

    if (
        pair == "ie"
        and i > 0
        and word[i - 1] == "r"
        and word[i:i + 3] == "ien"
    ):
        rest = word[i + 3:]

        if rest:
            return (
                True,
                True,
                "-rien- im Kompositum: "
                "Morphemgrenze kann die Silbenzahl ändern",
            )

        return True, False, None

    # ---------------------------------------------------------------
    # Bestimmte Nomen auf -rie:
    #
    # Serie    [ ... iə ]
    # Materie  [ ... iə ]
    #
    # aber:
    #
    # seriell    [ ... i̯ɛl ]
    # materiell  [ ... i̯ɛl ]
    # ---------------------------------------------------------------

    rie_bases = (
        ("serie", 3),
        ("materie", 5),
        ("kurie", 3),
        ("furie", 3),
        ("historie", 6),
    )

    for base, offset in rie_bases:
        start = word.find(base)

        while start >= 0:
            if (
                i == start + offset
                and not word.startswith(base + "ll", start)
            ):
                return True, False, None

            start = word.find(base, start + 1)

    # ---------------------------------------------------------------
    # Ion selbst ist aussprachevariabel.
    # ---------------------------------------------------------------

    if pair == "io" and i == 0 and word.startswith("ion"):
        return (
            True,
            True,
            "‚Ion…‘ hat mehrere mögliche Standardaussprachen",
        )

    # ---------------------------------------------------------------
    # Wort-/Morphemmuster, bei denen eine scheinbare
    # Diphthongfolge tatsächlich getrennt wird.
    #
    # Der Offset bezeichnet den ersten Vokal der fraglichen Folge.
    # ---------------------------------------------------------------

    patterns = (
        # be-/ge- + vokalischer Wortstamm
        ("beend", 1),
        ("beerd", 1),
        ("beeng", 1),
        ("beei", 1),
        ("beirr", 1),
        ("beur", 1),
        ("beun", 1),
        ("beinhal", 1),

        ("geehr", 1),
        ("geerb", 1),
        ("geeign", 1),
        ("geirr", 1),
        ("geimpf", 1),
        ("geur", 1),

        # ko-o...
        ("kooper", 1),
        ("koordin", 1),
        ("koopt", 1),

        # kre-i...
        ("kreier", 2),

        # Fremdwörter
        ("naiv", 1),
        ("mosaik", 3),

        ("protein", 4),
        ("koffein", 4),
        ("coffein", 4),
        ("kasein", 3),
        ("casein", 3),

        # io mit zwei Silbenkernen
        ("spion", 2),
        ("pion", 1),
        ("trio", 2),

        # ie mit zwei Silbenkernen
        ("klient", 2),
        ("piet", 1),

        # -e-ist / -a-ist ...
        ("atheist", 3),
        ("theist", 2),
        ("deist", 1),
    )

    for pattern, offset in patterns:
        if position_in_pattern(word, i, pattern, offset):
            return True, False, None

    return False, False, None


# ---------------------------------------------------------------------------
# Gleitlautregeln
# ---------------------------------------------------------------------------

def ion_glide(word: str, i: int) -> bool:
    """Erkennt produktives -ion mit unsilbischem i.

    Nation, Region, Million, Stadion usw.
    """

    if word[i:i + 3] != "ion":
        return False

    # Reines Pion/Spion/Ion wird bereits durch forced_hiatus behandelt.
    #
    # Für produktives -ion muss davor wenigstens ein Vokalkern
    # vorhanden sein.
    if not any(
        effective_vowel_symbol(word, j) is not None
        for j in range(i)
    ):
        return False

    after = word[i + 3:]

    if not after:
        return True

    # Direkt folgender Konsonant:
    #
    # Nations-
    # Aktions-
    if raw_vowel_symbol(after[0]) is None:
        return True

    # Häufige Fortsetzungen.
    return after.startswith(
        (
            "en",
            "al",
            "är",
            "ell",
            "ismus",
            "ist",
            "istisch",
        )
    )


def ial_glide(word: str, i: int) -> bool:
    """Material, sozial, genial usw."""

    if word[i:i + 3] != "ial":
        return False

    after = word[i + 3:]

    if not after:
        return True

    if after in {
        "e",
        "en",
        "er",
        "es",
        "em",
        "ien",
        "iens",
    }:
        return True

    return after.startswith(
        (
            "ität",
            "ismus",
            "istisch",
        )
    )


def ium_glide(word: str, i: int) -> bool:
    """Behandelt -ium vorsichtig.

    Beispiele mit Gleitlaut:
        Studium
        Podium
        Medium
        Helium
        Gymnasium

    Nach r dagegen normalerweise getrennt:
        Aquarium
        Kriterium
        Natrium
        Ministerium
    """

    if word[i:i + 3] != "ium":
        return False

    after = word[i + 3:]

    if after not in ("", "s"):
        return False

    if i > 0 and word[i - 1] == "r":
        return False

    return True


def known_io_glide(word: str, i: int) -> bool:
    """Geläufige io-Wortfamilien mit Gleitlaut.

    Radio, Radiologie, Radiosender
    Studio, Aufnahmestudio
    Audio ...
    """

    for stem in ("radio", "studio", "audio"):
        start = word.find(stem)

        while start >= 0:
            local_i = stem.find("io")

            if (
                local_i >= 0
                and i == start + local_i
            ):
                return True

            start = word.find(stem, start + 1)

    return False


# ---------------------------------------------------------------------------
# eigentliche Wortzählung
# ---------------------------------------------------------------------------

def count_part(part: str) -> Estimate:
    w = nfc_lower(part)

    if not w:
        return Estimate(0, 0, 0)

    best = 0
    minimum = 0
    maximum = 0

    reasons: list[str] = []

    # Nichtdeutsche Diakritika sind ein guter Hinweis auf
    # ausspracheabhängige Fremdwörter/Namen.
    if any(
        ord(c) > 127 and c not in "äöüß"
        for c in w
    ):
        reasons.append(
            "Fremdzeichen/Diakritika: Aussprache prüfen"
        )

    i = 0

    while i < len(w):
        v1 = effective_vowel_symbol(w, i)

        if v1 is None:
            i += 1
            continue

        if i + 1 < len(w):
            v2 = effective_vowel_symbol(w, i + 1)
        else:
            v2 = None

        pair = v1 + v2 if v2 is not None else None

        # -----------------------------------------------------------
        # Zwei benachbarte Vokale
        # -----------------------------------------------------------

        if pair is not None:

            hiatus, ambiguous, reason = forced_hiatus(
                w,
                i,
                pair,
            )

            if hiatus:
                # Wichtig:
                #
                # Nur den ERSTEN Vokal verbrauchen.
                #
                # Beispiel:
                #
                #   ge-eig-net
                #
                # Nach e|e darf das zweite e noch mit i den
                # Diphthong ei bilden.
                best += 1

                if ambiguous:
                    minimum += 0
                else:
                    minimum += 1

                maximum += 1

                if reason:
                    reasons.append(reason)

                i += 1
                continue

            # Sichere deutsche Diphthonge / Doppelvokale / Standard-ie.
            if (
                pair in CORE_DIPHTHONGS
                or pair in DOUBLE_VOWELS
                or pair == "ie"
            ):
                best += 1
                minimum += 1
                maximum += 1

                i += 2
                continue

            # -ion
            if pair == "io" and (
                ion_glide(w, i)
                or known_io_glide(w, i)
            ):
                best += 1
                minimum += 1
                maximum += 1

                i += 2
                continue

            # -ial / -iard
            if pair == "ia" and (
                ial_glide(w, i)
                or w[i:i + 4] == "iard"
            ):
                best += 1
                minimum += 1
                maximum += 1

                i += 2
                continue

            # -ium
            if pair == "iu" and ium_glide(w, i):
                best += 1
                minimum += 1
                maximum += 1

                i += 2
                continue

            # oi ist in Fremdwörtern nicht zuverlässig.
            if pair == "oi":
                best += 1
                minimum += 1
                maximum += 2

                reasons.append(
                    "Vokalfolge ‚oi‘ ist in Fremdwörtern "
                    "ausspracheabhängig"
                )

                i += 2
                continue

            # ou ebenfalls.
            if pair == "ou":
                best += 1
                minimum += 1
                maximum += 2

                reasons.append(
                    "Vokalfolge ‚ou‘ ist in Fremdwörtern "
                    "ausspracheabhängig"
                )

                i += 2
                continue

            # ui:
            #
            # Pfui/Hui -> meist ein Kern
            # Ruine    -> zwei
            if pair == "ui":
                if w.startswith(("pfui", "hui", "duis")):
                    best += 1
                else:
                    best += 2

                minimum += 1
                maximum += 2

                reasons.append(
                    "Vokalfolge ‚ui‘ kann Diphthong "
                    "oder Hiatus sein"
                )

                i += 2
                continue

            # Alle anderen direkt benachbarten Vokale:
            #
            # Standardmäßig getrennt zählen, aber kennzeichnen.
            reasons.append(
                f"Vokalfolge ‚{pair}‘ getrennt gezählt; "
                "Aussprache prüfen"
            )

        # -----------------------------------------------------------
        # einzelner Silbenkern
        # -----------------------------------------------------------

        best += 1
        minimum += 1
        maximum += 1

        i += 1

    # ------------------------------------------------------------------
    # Englische Schreibungen wie Byte, Hype, Style
    #
    # Das finale e ist häufig stumm.
    # ------------------------------------------------------------------

    if "y" in w and w.endswith("e") and best >= 2:

        positions = [
            j
            for j in range(len(w))
            if effective_vowel_symbol(w, j) is not None
        ]

        if (
            len(positions) == 2
            and raw_vowel_symbol(w[positions[0]]) == "y"
            and len(w) <= 6
        ):
            # Byte:
            #
            # Schrift-Heuristik zunächst 2,
            # wahrscheinlich gesprochen 1.
            maximum = max(maximum, best)

            best -= 1
            minimum = min(minimum, best)

        else:
            minimum = min(
                minimum,
                max(0, best - 1),
            )

        reasons.append(
            "Fremdwort mit <y...e>: finales <e> kann stumm sein"
        )

    # ------------------------------------------------------------------
    # hm, psst, pff ...
    # ------------------------------------------------------------------

    if best == 0:
        best = 1
        minimum = 0
        maximum = 1

        reasons.append(
            "kein Vokalbuchstabe erkannt: "
            "Interjektion/Abkürzung prüfen"
        )

    # Gründe deduplizieren.
    reasons = list(dict.fromkeys(reasons))

    return Estimate(
        best=best,
        minimum=minimum,
        maximum=maximum,
        reasons=reasons,
    )


# ---------------------------------------------------------------------------
# Korrekturlexikon
# ---------------------------------------------------------------------------

def load_lexicon(
    path: Path | None,
) -> dict[str, int]:

    if path is None:
        return {}

    result: dict[str, int] = {}

    for lineno, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        # Kommentare erlauben:
        #
        # Queue=1  # englische Aussprache
        line = raw.split("#", 1)[0].strip()

        if not line:
            continue

        if "=" in line:
            word, value = line.split("=", 1)

        else:
            parts = line.split()

            if len(parts) != 2:
                raise ValueError(
                    f"{path}:{lineno}: erwartet WORT=ZAHL"
                )

            word, value = parts

        word = nfc_lower(word.strip())

        try:
            count = int(value.strip())

        except ValueError as exc:
            raise ValueError(
                f"{path}:{lineno}: ungültige Silbenzahl"
            ) from exc

        if count < 0:
            raise ValueError(
                f"{path}:{lineno}: Silbenzahl muss >= 0 sein"
            )

        result[word] = count

    return result


# ---------------------------------------------------------------------------
# pyphen
# ---------------------------------------------------------------------------

def get_pyphen(enabled: bool):

    if not enabled:
        return None

    try:
        import pyphen  # type: ignore

        return pyphen.Pyphen(lang="de_DE")

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Wortanalyse
# ---------------------------------------------------------------------------

def analyze_word(
    word: str,
    lexicon: dict[str, int],
    dic=None,
) -> WordAnalysis:

    key = nfc_lower(word)

    # Benutzerlexikon hat immer Vorrang.
    if key in lexicon:
        n = lexicon[key]

        estimate = Estimate(
            n,
            n,
            n,
            source="lexicon",
        )

    else:
        # Bindestrich-Komposita:
        #
        # Nacht-und-Nebel ...
        hyphen_parts = [
            p
            for p in HYPHEN_RE.split(word)
            if p
        ]

        # Apostrophe NICHT als eigene Wörter behandeln.
        #
        # geht's     -> gehts
        # heil'ge    -> heilge
        # rock'n'roll -> rocknroll
        parts = [
            APOSTROPHE_RE.sub("", part)
            for part in hyphen_parts
        ]

        estimates = [
            count_part(part)
            for part in parts
            if part
        ]

        estimate = Estimate(
            best=sum(e.best for e in estimates),
            minimum=sum(e.minimum for e in estimates),
            maximum=sum(e.maximum for e in estimates),
            reasons=[
                reason
                for e in estimates
                for reason in e.reasons
            ],
        )

        if "'" in word or "’" in word:
            estimate.reasons.append(
                "Apostroph/Elision: tatsächliche Lesung prüfen"
            )

        estimate.reasons = list(
            dict.fromkeys(estimate.reasons)
        )

    hyphenation = (
        dic.inserted(word)
        if dic is not None
        else None
    )

    return WordAnalysis(
        word=word,
        estimate=estimate,
        pyphen=hyphenation,
    )


# ---------------------------------------------------------------------------
# Zeilenanalyse
# ---------------------------------------------------------------------------

def analyze_line(
    line: str,
    lexicon: dict[str, int],
    dic=None,
) -> LineAnalysis:

    words = WORD_RE.findall(line)

    reasons: list[str] = []

    # Zahlen werden absichtlich nicht geraten:
    #
    # 1999 könnte z. B. verschieden ausgesprochen werden.
    if re.search(r"\d", line):
        reasons.append(
            "Ziffern erkannt: Zahlwort ausschreiben "
            "oder manuell prüfen"
        )

    # CD, EU, USA, NATO usw.:
    #
    # Akronym vs. Buchstabieren ist aus der Schreibung
    # nicht allgemein ableitbar.
    #
    # Ausnahme: In geistlicher Dichtung ist die Versalschreibung
    # des Gottesnamens (HERR fuer JHWH) gaengige Tradition und
    # wird ganz normal gesprochen. Solche Woerter loesen keine
    # Warnung aus.
    sacral_caps = {"HERR", "HERRN", "GOTT", "JHWH", "JAHWE", "ICH", "DU", "ER"}

    caps_tokens = set(re.findall(r"\b[A-ZÄÖÜ]{2,}\b", line))

    if caps_tokens - sacral_caps:
        reasons.append(
            "VERSALIEN/Abkürzung erkannt: "
            "Buchstaben- oder Akronymaussprache prüfen"
        )

    analyses = [
        analyze_word(
            word,
            lexicon,
            dic,
        )
        for word in words
    ]

    return LineAnalysis(
        line=line,
        words=analyses,
        reasons=reasons,
    )


# ---------------------------------------------------------------------------
# Formatierung
# ---------------------------------------------------------------------------

def format_estimate(e: Estimate) -> str:

    if e.minimum == e.maximum:

        if e.source == "lexicon":
            return f"{e.best}*"

        if e.reasons:
            return f"{e.best}?"

        return str(e.best)

    return (
        f"{e.best}?/"
        f"{e.minimum}–{e.maximum}"
    )


def format_word(
    analysis: WordAnalysis,
    show_pyphen: bool,
) -> str:

    text = (
        f"{analysis.word}"
        f"({format_estimate(analysis.estimate)})"
    )

    if (
        show_pyphen
        and analysis.pyphen
        and analysis.pyphen != analysis.word
    ):
        text += f"[{analysis.pyphen}]"

    return text


# ---------------------------------------------------------------------------
# Eingabe
# ---------------------------------------------------------------------------

def read_lines(args) -> list[str]:

    if args.file:
        return args.file.read_text(
            encoding="utf-8"
        ).splitlines()

    if args.inputs:

        # Rückwärtskompatibel:
        #
        # python silben.py gedicht.txt
        if len(args.inputs) == 1:
            p = Path(args.inputs[0])

            try:
                if p.is_file():
                    return p.read_text(
                        encoding="utf-8"
                    ).splitlines()

            except OSError:
                # Ein sehr langer einzelner Vers kann als
                # Dateiname ungültig sein. Dann einfach als
                # Texteingabe behandeln.
                pass

        return args.inputs

    return sys.stdin.read().splitlines()


# ---------------------------------------------------------------------------
# Selbsttest
# ---------------------------------------------------------------------------

def run_self_test() -> int:

    cases = {
        # normales Deutsch
        "Haus": 1,
        "Liebe": 2,
        "Beamte": 3,
        "Feuer": 2,
        "Theater": 3,
        "Ruhe": 2,

        # ie / ee
        "Familie": 3,
        "Familien": 3,
        "Serie": 3,
        "Serien": 3,
        "Materie": 4,
        "Materien": 4,
        "Antimaterie": 6,
        "Batterie": 3,
        "Batterien": 4,
        "Ferien": 3,
        "Museen": 3,
        "Seen": 2,
        "Ideen": 3,

        # qu / y
        "Quelle": 2,
        "Quadrat": 2,
        "Qualität": 3,
        "Yoga": 2,
        "Typ": 1,
        "System": 2,
        "Maya": 2,

        # -ion
        "Nation": 2,
        "Nationen": 3,
        "Information": 4,
        "national": 3,
        "Million": 2,
        "Spion": 2,
        "Pion": 2,
        "Pionier": 3,

        # -ium
        "Studium": 2,
        "Podium": 2,
        "Medium": 2,
        "Helium": 2,
        "Aquarium": 4,
        "Kriterium": 4,
        "Natrium": 3,
        "Ministerium": 5,
        "Gymnasium": 3,

        # -ial
        "Material": 3,
        "Materialien": 4,
        "materiell": 3,
        "materielle": 4,
        "Milliarde": 3,
        "Dialekt": 3,

        # Fremdwörter
        "Museum": 3,
        "Petroleum": 4,
        "Klient": 2,
        "Pietät": 3,
        "naiv": 2,
        "Mosaik": 3,
        "Mosaiken": 4,
        "Protein": 3,
        "Proteine": 4,
        "Koffein": 3,

        # Präfixe
        "beinhalten": 4,
        "geurteilt": 3,
        "beeinflussen": 4,
        "kooperieren": 5,
        "beurteilen": 4,
        "geeignet": 3,
        "kreieren": 3,

        # Komposita
        "unkooperativ": 6,
        "Forschungskooperation": 7,

        # io
        "Radio": 2,
        "Radiosender": 4,
        "Radiologie": 4,
        "Studio": 2,
        "Aufnahmestudio": 5,
        "Audio": 2,
        "Video": 3,
        "Trio": 2,
        "Geheimspion": 4,

        # weitere
        "Kurie": 3,
        "Furie": 3,
        "Historie": 4,
        "Ruine": 3,

        # englische Schreibheuristik
        "Byte": 1,
    }

    failed = 0

    for word, expected in cases.items():

        estimate = count_part(word)

        if estimate.best != expected:

            failed += 1

            print(
                f"FEHLER {word:<22} "
                f"erwartet {expected}, "
                f"erhalten {estimate.best} "
                f"({estimate})"
            )

    # Aussprachebereich Orient.
    orient = count_part("Orient")

    if (
        orient.best,
        orient.minimum,
        orient.maximum,
    ) != (3, 2, 3):

        failed += 1

        print(
            f"FEHLER Orient-Bereich: {orient}"
        )

    # Apostroph darf kein künstliches
    # zusätzliches Wort erzeugen.
    contraction = analyze_word(
        "geht's",
        {},
        None,
    ).estimate

    if contraction.best != 1:

        failed += 1

        print(
            f"FEHLER geht's: "
            f"erwartet 1, erhalten {contraction}"
        )

    # Industrie|nation vs. Industrien|...
    # ist orthografisch-morphologisch mehrdeutig.
    compound = count_part("Industrienation")

    if not (
        compound.minimum
        <= 5
        <= compound.maximum
    ):

        failed += 1

        print(
            "FEHLER Industrienation: "
            f"5 nicht im Bereich {compound}"
        )

    # Sakral-Versalien duerfen keine Warnung ausloesen,
    # echte Akronyme weiterhin schon.
    sacral_line = analyze_line("Der HERR ist mein Hirte", {})

    if sacral_line.reasons:

        failed += 1

        print(
            "FEHLER HERR-Versalien: "
            f"unerwartete Warnung {sacral_line.reasons}"
        )

    acronym_line = analyze_line("Die NATO tagt heute", {})

    if not acronym_line.reasons:

        failed += 1

        print(
            "FEHLER NATO-Versalien: Warnung erwartet, keine erhalten"
        )

    total = len(cases) + 5

    print(
        f"Selbsttest: "
        f"{total - failed}/{total} korrekt."
    )

    return 1 if failed else 0


# ---------------------------------------------------------------------------
# Kommandozeile
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Heuristischer Silbenzähler "
            "für deutsche Verse"
        )
    )

    parser.add_argument(
        "inputs",
        nargs="*",
        help=(
            "Verszeilen oder, als einzelnes Argument, "
            "eine Textdatei"
        ),
    )

    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Textdatei, eine Verszeile pro Zeile",
    )

    parser.add_argument(
        "-t",
        "--target",
        type=int,
        help="gewünschte Silbenzahl pro Vers",
    )

    parser.add_argument(
        "-l",
        "--lexikon",
        type=Path,
        help="Korrekturlexikon im Format WORT=ZAHL",
    )

    parser.add_argument(
        "--pyphen",
        action="store_true",
        help=(
            "pyphen-Trennstellen zusätzlich anzeigen "
            "(nur Anschauung)"
        ),
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="eingebaute Regressionstests ausführen",
    )

    return parser


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main() -> int:

    args = build_parser().parse_args()

    if args.self_test:
        return run_self_test()

    # ---------------------------------------------------------------
    # Lexikon
    # ---------------------------------------------------------------

    try:
        lexicon = load_lexicon(
            args.lexikon
        )

    except (OSError, ValueError) as exc:

        print(
            f"Fehler im Lexikon: {exc}",
            file=sys.stderr,
        )

        return 2

    # ---------------------------------------------------------------
    # Zielwert
    # ---------------------------------------------------------------

    if (
        args.target is not None
        and args.target < 0
    ):
        print(
            "Fehler: --target muss >= 0 sein.",
            file=sys.stderr,
        )

        return 2

    # ---------------------------------------------------------------
    # Zeilen
    # ---------------------------------------------------------------

    try:
        lines = [
            line
            for line in read_lines(args)
            if line.strip()
        ]

    except OSError as exc:

        print(
            f"Fehler beim Lesen: {exc}",
            file=sys.stderr,
        )

        return 2

    if not lines:
        print(
            "Keine Verszeilen übergeben."
        )

        return 0

    # ---------------------------------------------------------------
    # pyphen
    # ---------------------------------------------------------------

    dic = get_pyphen(
        args.pyphen
    )

    if args.pyphen and dic is None:
        print(
            "HINWEIS: pyphen nicht verfügbar; "
            "Trennstellen werden nicht angezeigt.\n"
        )

    # ---------------------------------------------------------------
    # Analyse
    # ---------------------------------------------------------------

    analyses = [
        analyze_line(
            line,
            lexicon,
            dic,
        )
        for line in lines
    ]

    # ---------------------------------------------------------------
    # Ausgabe
    # ---------------------------------------------------------------

    for idx, analysis in enumerate(
        analyses,
        1,
    ):

        if (
            analysis.minimum
            != analysis.maximum
        ):
            head = (
                f"{analysis.best:>2}? Silben "
                f"({analysis.minimum}–"
                f"{analysis.maximum})"
            )

        elif analysis.uncertain:

            head = (
                f"{analysis.best:>2}? Silben"
            )

        else:

            head = (
                f"{analysis.best:>2} Silben"
            )

        print(
            f"{idx:>3}. "
            f"{head:<22} "
            f"{analysis.line.strip()}"
        )

        print(
            "     "
            + " | ".join(
                format_word(
                    word,
                    args.pyphen,
                )
                for word in analysis.words
            )
        )

        # Zeilenwarnungen.
        for reason in dict.fromkeys(
            analysis.reasons
        ):
            print(
                f"       ? Zeile: {reason}"
            )

        # Wortwarnungen.
        for word in analysis.words:

            for reason in dict.fromkeys(
                word.estimate.reasons
            ):
                print(
                    f"       ? "
                    f"{word.word}: "
                    f"{reason}"
                )

    print()

    # ---------------------------------------------------------------
    # Sollwert bestimmen
    # ---------------------------------------------------------------

    target = args.target

    if target is None:

        # Sichere Verse sollten die automatische
        # Mustererkennung stärker bestimmen als
        # bereits als unsicher erkannte Verse.
        certain_counts = [
            analysis.best
            for analysis in analyses
            if not analysis.uncertain
        ]

        all_counts = [
            analysis.best
            for analysis in analyses
        ]

        basis = (
            certain_counts
            if certain_counts
            else all_counts
        )

        frequency = Counter(basis)

        max_frequency = max(
            frequency.values()
        )

        modes = sorted(
            count
            for count, freq in frequency.items()
            if freq == max_frequency
        )

        if len(modes) == 1:

            target = modes[0]

            if certain_counts:
                print(
                    "Häufigste sichere "
                    f"Silbenzahl: {target}."
                )

            else:
                print(
                    f"Häufigste Silbenzahl: "
                    f"{target}."
                )

        else:

            print(
                "Silbenfolge: "
                f"{all_counts} "
                "(kein eindeutiger "
                "häufigster Wert)."
            )

    # ---------------------------------------------------------------
    # Vergleich mit Sollwert
    # ---------------------------------------------------------------

    if target is not None:

        exact: list[int] = []
        possible: list[int] = []
        off: list[int] = []

        for idx, analysis in enumerate(
            analyses,
            1,
        ):

            if (
                analysis.best == target
                and analysis.minimum
                == analysis.maximum
                and not analysis.uncertain
            ):
                exact.append(idx)

            elif (
                analysis.minimum
                <= target
                <= analysis.maximum
            ):
                possible.append(idx)

            else:
                off.append(idx)

        if off:
            print(
                f"Abweichend von {target}: "
                "Vers "
                + ", ".join(
                    map(str, off)
                )
                + "."
            )

        if possible:
            print(
                f"Unsicher, aber {target} "
                "Silben möglich: Vers "
                + ", ".join(
                    map(str, possible)
                )
                + "."
            )

        if not off and not possible:
            print(
                "Alle Verse haben nach "
                f"dieser Zählung {target} Silben."
            )

    print(
        "Hinweis: Gleiche Silbenzahl bedeutet "
        "noch kein gleiches Versmaß; "
        "Betonungen werden nicht geprüft."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
