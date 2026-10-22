# Veröffentlichung vorbereiten

## Vorbereitet

- OpenAI-Manifest unter `.codex-plugin/plugin.json`, bestehendes Claude-Format bleibt verfügbar.
- Deutscher Skill mit klarer Pfadauflösung und transparenter manueller Prüfung, wenn Python nicht verfügbar ist.
- Vorhandenes Icon, drei Weihnachtsdemonstrationen, zehn Vergleichsaufträge und Texte für die Bewerbung.
- Technische Beschreibung der Datenverarbeitung in `PRIVACY.md`.

## Einreichung

1. Das ZIP aus `python3 scripts/package_openai.py` verwenden. Es enthält das OpenAI-Manifest, das Icon, den Skill mit Skript und Referenzen sowie README, Lizenz, Datenschutzbeschreibung und Beispiele.
2. Unter [OpenAI Plugins](https://platform.openai.com/plugins) anmelden, passende Organisation bzw. Projekt auswählen und eine verifizierte Entwickleridentität verwenden.
3. Ein neues Plugin mit ausschließlich Skills anlegen und das ZIP hochladen. Die Bezeichnung der Schaltflächen kann variieren.
4. Automatische Ergebnisse unter „Metadata & Skills“ prüfen. Wenn ein Feld oder Skill beanstandet wird, die Meldung vollständig kopieren, das Paket korrigieren und erneut hochladen.
5. Den importierten Skill in einer neuen Unterhaltung testen. Die Skriptprüfung muss tatsächlich ausgeführt werden oder die Antwort muss ihre manuelle Prüfung kennzeichnen. Installation und Ausführung in ChatGPT sind durch lokale Skripttests noch nicht nachgewiesen.
6. Herausgeberangaben und Datenverarbeitung bestätigen; dann die im Portal erforderlichen Erklärungen prüfen und zur Begutachtung einreichen. Nach Freigabe wird die Veröffentlichung separat ausgelöst.

Die Aufnahme oder eine bestimmte Bearbeitungsdauer ist nicht zugesichert. Ein GitHub-Repository oder Pull Request ist noch kein veröffentlichter Verzeichniseintrag.

## Listing

Die offiziellen Hinweise sehen Englisch in den Basisfeldern vor; der Markenname und die drei Beispielaufträge bleiben deutsch. Die deutsche Beschreibung steht in `LAUNCH.md`. Übersetzungsmetadaten werden laut Dokumentation zurzeit importiert, ändern aber noch nicht die Anzeige im Verzeichnis; deshalb wird keine deutsche Anzeige versprochen.

Ein reines Skill-Paket braucht laut Einreichungsdokumentation keine MCP-Testkonten, keine fünf MCP-Positivfälle und keinen MCP-Demofilm. Die zehn Aufträge in `evals/cases.json` dienen unserer eigenen Qualitätsprüfung.

## Noch ausstehend

- Zugang und Identitätsprüfung im OpenAI-Portal.
- Import, automatische Portalprüfung und ein echter Test der installierten Version in ChatGPT.
- Unabhängiger Vergleich mit und ohne Skill und Feedback von Testpersonen.
- Prüfung und Bestätigung der Angaben zur Datenverarbeitung durch den Herausgeber.
- Einreichung, Freigabe und Veröffentlichung. Erst danach einen echten Installationslink in README und Bewerbung ergänzen.

## Quellen

- [Claude-Plugins importieren](https://developers.openai.com/plugins/guides/submit-claude-plugin)
- [Einreichung und Metadaten](https://developers.openai.com/plugins/deploy/submission)
- [Plugin-Richtlinien](https://developers.openai.com/plugins/plugin-guidelines)

Geprüft am 22. Oktober 2026.
