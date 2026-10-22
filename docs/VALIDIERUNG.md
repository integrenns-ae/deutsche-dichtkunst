# Prüfstand 1.1.0

Datum: 22. Oktober 2026. Ausgangsstand: `05949fbf167cdba8a1011e2b8e70e0e7ca8ac129` aus `integrenns-ae/deutsche-dichtkunst`.

## Ausgeführt

| Prüfung | Ergebnis | Aussagegrenze |
| --- | --- | --- |
| Bestehender Silbenzähler-Selbsttest mit `python3 -I -S` | 87/87 bestanden | Prüft die vorhandenen Skriptfälle, kein Modellbenchmark |
| Drei Beispieltexte, je acht Verse, Ziel acht Silben | 24/24 Verse mit acht Silben geschätzt | Beweist weder richtige Betonung noch natürliches Vorlesen |
| Gebündelter OpenAI-Plugin-Validator | Bestanden | Lokales Paketschema; keine Freigabe durch das Verzeichnis |
| Gebündelter Skill-Validator | Bestanden | Frontmatter und Struktur, keine Qualitätsgarantie |

Die Beispiele wurden mit der Skill-Methode entworfen, auf Reimpaare, Kadenzen und geplantes Metrum sprachlich geprüft und redaktionell überarbeitet. Eine unabhängige menschliche Vortragsbewertung steht aus.

Für die beiden Validatoren wurde PyYAML 6.0.3 ausschließlich in einer temporären Prüfumgebung installiert. Das ausgelieferte Silbenskript verwendet für seinen Kernbetrieb nur die Python-Standardbibliothek. Es wurde nicht verändert.

## Reproduzieren

```bash
python3 -I -S skills/deutsche-dichtkunst/scripts/silben.py --self-test
python3 -I -S skills/deutsche-dichtkunst/scripts/silben.py --target 8 --file examples/eltern.txt
python3 -I -S skills/deutsche-dichtkunst/scripts/silben.py --target 8 --file examples/advent.txt
python3 -I -S skills/deutsche-dichtkunst/scripts/silben.py --target 8 --file examples/weihnachtsfeier.txt
python3 scripts/package_openai.py
```

## Offen

- Upload und automatische Prüfungen im OpenAI-Portal.
- Installation und tatsächlicher Aufruf in einer neuen ChatGPT-Unterhaltung, einschließlich Ressourcenauflösung und Skriptausführung.
- Zehn Vergleichsaufträge aus `evals/cases.json`: vorbereitet, nicht ausgeführt.
- Menschliche Bewertung und Rückmeldungen erster Nutzer.
- Zustimmung des Herausgebers zu den Angaben zur Datenverarbeitung sowie die erforderlichen Erklärungen im Portal.

Die Paketbeschreibung verlinkt vorerst die Datenschutzdatei auf dem Arbeitszweig `codex/openai-launch`. Nach Übernahme in den Hauptzweig kann der Link auf `main` umgestellt und das ZIP neu gebaut werden.
