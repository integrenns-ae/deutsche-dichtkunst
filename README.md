# Deutsche Dichtkunst

**Ein Claude-Skill für klassische deutsche Dichtkunst – streng in der Disziplin des Dichtens, schön in Form.**

Dieser Skill lehrt Claude das Handwerk der klassischen deutschen Dichtung. Sein Kernsatz: **Ein Text, der sich nur reimt, ist noch kein Gedicht.** Ein Gedicht ist erst fertig, wenn Versmaß, Betonungen, Reime und Kadenzen stimmen. Die meisten KI-Gedichte scheitern genau daran – sie reimen, aber sie holpern. Dieser Skill nicht: Er enthält eine Arbeitsmethode mit eingebauter Kontrollschleife, die jedes Gedicht prüft, bevor es abgegeben wird.

## Was der Skill kann

- **Gedichte schreiben** nach der klassischen Drei-Spalten-Methode (WORT – REIM – VERBINDUNG): Gelegenheitsgedichte zu Geburtstag, Hochzeit, Jubiläum, geistlichen Anlässen; Gedichte aus Quelltexten (Predigt, Lebenslauf, Bibeltext, Rede); Gedichte mit Pflichtwörtern
- **Gedichte überarbeiten**: Strophen ergänzen, umdichten, holpernde Verse glätten
- **Gedichte analysieren**: Versfuß, Kadenzen, Reimschema (Kompaktnotation wie `A11w`), Stilmittel – jeder Befund am Text belegt

## Was ihn streng macht

- **Reime in zwei Stufen**: Standard ist der reine Reim (absoluter Gleichklang ab der letzten betonten Silbe). Zulässig daneben nur der zweisilbige unreine Reim unter engen phonetischen Bedingungen – und der wird bei der Abgabe ausdrücklich gekennzeichnet. Männliche Reime müssen immer rein sein. *offen* reimt nicht auf *Ofen*, *Herr* nicht auf *Heer*.
- **Silbenzählung per Skript** (`scripts/silben.py`): zählt gesprochene Silben, ist ehrlich bei Unsicherheit und unterstützt ein eigenes Korrekturlexikon.
- **Betonungen werden skandiert**, Silbe für Silbe – gleiche Silbenzahl allein genügt nicht. Betonungsfehler dürfen nie stehen bleiben.
- **Kadenzen** (männlich/weiblich) werden geprüft; sich reimende Verse brauchen dieselbe Kadenz.
- **Erst das Handwerk, dann der Schmuck**: Stilmittel (Metapher, Personifikation, Anapher, Alliteration …) verzieren ein handwerklich fertiges Gedicht, sie ersetzen es nicht.

Die Tradition hinter dem Skill ist das geistliche Lied (Kirchenlieder, Psalmnachdichtungen); er bevorzugt eine gehobene, würdige Sprache, folgt aber selbstverständlich auch weltlichen, humorvollen oder kindlichen Aufträgen – mit denselben handwerklichen Regeln.

## Installation

### Claude Code

```bash
claude plugin marketplace add integrenns-ae/deutsche-dichtkunst
claude plugin install deutsche-dichtkunst@integrenns
```

Oder in einer Sitzung: `/plugin install deutsche-dichtkunst --marketplace integrenns-ae/deutsche-dichtkunst`

Danach greift der Skill automatisch, sobald ein Gedicht, Verse, Reime oder eine Gedichtanalyse auf Deutsch gewünscht werden.

### Ohne Marketplace

Repo klonen und mit `claude --plugin-dir ./deutsche-dichtkunst` laden, oder den Ordner `skills/deutsche-dichtkunst/` nach `~/.claude/skills/` kopieren.

## Aufbau

```
skills/deutsche-dichtkunst/
├── SKILL.md                  # Methode, Reimregeln, Kontrollschleife, Analyse-Leitfaden
├── references/
│   ├── metrik.md             # Versfüße, Kadenzen, Zäsur, Auftakt
│   ├── reime.md              # Reinheit, Vokallänge, alle Reimschemata
│   └── stilmittel.md         # 13 Stilmittel mit Beispielen
└── scripts/
    └── silben.py             # Silbenzähler mit Korrekturlexikon
```

## Hintergrund

Der Skill destilliert eine fünfteilige Dichtschule (Der Vers · Der Reim · Die Stilmittel · Die Sprache · Die Methode) und einen Seminarvortrag über die Werkzeuge eines Dichters in eine Arbeitsanweisung, mit der Claude formstrenge und klangschöne deutsche Gedichte schreibt und prüft.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
