# Deutsche Dichtkunst

**Persönliche deutsche Gedichte schreiben und überarbeiten – mit Prüfung von Versmaß, Reimen und Silben.**

Für Weihnachtskarten, Advent, Geburtstage, Hochzeiten und andere Anlässe. Der Skill arbeitet mit einer Drei-Spalten-Methode (WORT – REIM – VERBINDUNG), einer Kontrollschleife und Nachschlagewerken. Er unterstützt klassische, formgebundene Gedichte und ihre Analyse.

## Ein Weihnachtsgedicht aus drei Erinnerungen

> „Schreibe ein Weihnachtsgedicht für meine Eltern. Darin sollen der Apfelbaum, die Werkbank und euer selbst gebackenes Sonntagsbrot vorkommen. Weltlich, persönlich, zwei Vierzeiler.“

```text
Der Apfelbaum steht weiß im Schnee,
ich denk an euch, wohin ich geh.
Die Werkbank ruht; das Licht bleibt an,
weil ich bei euch noch Kind sein kann.

Das Sonntagsbrot, von euch gemacht,
hat Wärme in mein Herz gebracht.
Zum Fest komm ich zu euch nach Haus
und pack die alten Träume aus.
```

Vorbereitete, redaktionell bearbeitete Demonstration; kein Vergleichstest. [Drei vollständige Beispiele mit Aufträgen und Formhinweisen](examples/WEIHNACHTEN.md).

## Was der Skill unterstützt

- Gedichte aus persönlichen Erinnerungen, Pflichtwörtern oder Quelltexten entwerfen.
- Holpernde Verse überarbeiten, Strophen ergänzen und bestehende Texte umdichten.
- Versmaß, Betonungen, Reime, Kadenzen und Stilmittel eines Gedichts untersuchen.
- Ton und Anlass berücksichtigen: weltlich, humorvoll, feierlich oder christlich.

Die Methode wurzelt in der Tradition geistlicher Lieder und Psalmnachdichtungen. Religiöse Motive folgen dem Auftrag; weltliche Aufträge bleiben weltlich.

## So wird geprüft

Ein Python-Skript schätzt die gesprochenen Silben und kennzeichnet manche Unsicherheiten. Reime, natürliche Betonungen und Kadenzen werden zusätzlich sprachlich geprüft. Gleiche Silbenzahl allein ist noch kein passendes Versmaß.

**Grenzen:** Das Skript ist heuristisch; Modellurteile können falsch sein. Bei Eigennamen, Fremdwörtern und Aussprachevarianten ist besondere Aufmerksamkeit nötig. Lies ein Gedicht vor seiner Verwendung laut vor. Wenn die Umgebung keine Python-Ausführung erlaubt, kennzeichnet der Skill seine Silbenprüfung ausdrücklich als manuell.

## Nutzung

### ChatGPT und Codex

Das Repository enthält ein OpenAI-Paket zur Einreichung. **Es gibt noch keinen veröffentlichten Eintrag im OpenAI-Plugin-Verzeichnis und keinen bestätigten ChatGPT-Installationslink.**

Paket lokal bauen:

```bash
python3 scripts/package_openai.py
```

Das ZIP entsteht unter `../output/deutsche-dichtkunst-1.1.0-openai.zip`. [Einreichungsanleitung und offene Schritte](docs/START.md).

Für einen lokalen Codex-Test kann der vollständige Ordner `skills/deutsche-dichtkunst/` in einen von Codex erkannten Skill-Ordner kopiert werden, etwa `~/.agents/skills/deutsche-dichtkunst/`. Anschließend eine neue Sitzung starten und den Skill ausdrücklich mit `$deutsche-dichtkunst` aufrufen. Eine solche lokale Installation veröffentlicht kein Plugin.

### Claude Code

```bash
claude plugin marketplace add integrenns-ae/deutsche-dichtkunst
claude plugin install deutsche-dichtkunst@integrenns
```

Alternativ das Repository klonen und mit `claude --plugin-dir ./deutsche-dichtkunst` laden oder den vollständigen Skill-Ordner nach `~/.claude/skills/` kopieren.

## Silbenzähler separat verwenden

Python ab Version 3.10 reicht aus; es sind keine zusätzlichen Pakete erforderlich. `pyphen` ist ausschließlich eine optionale Hilfe zur Anzeige orthografischer Trennstellen.

```bash
python3 skills/deutsche-dichtkunst/scripts/silben.py --self-test
python3 skills/deutsche-dichtkunst/scripts/silben.py --target 8 --file examples/eltern.txt
```

Für besondere Aussprachen unterstützt `--lexikon ausnahmen.txt` Einträge wie `Queue=1`. Das Skript überprüft weder Wortbetonungen noch Reimqualität.

## Qualität und Feedback

[Prüfprotokoll](docs/VALIDIERUNG.md) · [Zehn Aufträge für einen Vergleich mit und ohne Skill](evals/README.md)

Konkrete Rückmeldungen helfen: Welche Zeile holpert? Welcher Reim klingt unrein? Welcher persönliche Inhalt ging verloren? Bitte nutze [GitHub Issues](https://github.com/integrenns-ae/deutsche-dichtkunst/issues) mit anonymisierten Beispielen.

## Daten und Lizenz

Das Paket enthält keinen eigenen Server und keine Telemetrie. Der Plugin-Code sendet keine Eingaben an den Herausgeber. Chats und Dateien unterliegen den Bedingungen und Einstellungen der jeweils verwendeten KI-Plattform. [Datenverarbeitung](PRIVACY.md).

MIT – siehe [LICENSE](LICENSE).

## English summary

Deutsche Dichtkunst is an open skill for writing, revising and analyzing classical German poetry. It combines a structured drafting method with checks for meter, stress, rhyme and cadence, plus a heuristic Python syllable estimator. It supports personal Christmas poems, Advent, birthdays and other occasions.

The repository includes Claude packaging and a prepared OpenAI plugin manifest. Publication in the OpenAI directory and an end-to-end ChatGPT installation test are still pending. The examples are edited demonstrations, not benchmark results. The skill reports manual syllable checking when code execution is unavailable.
