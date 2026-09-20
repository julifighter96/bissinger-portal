# Wartungsvertrag

für die Software **"ElbaBot"** (automatisierte Auftragsannahme im Portal *Elbaverwaltung*)

---

zwischen

**[Name/Firma Auftragnehmer]**
[Straße, Hausnummer]
[PLZ, Ort]
– nachfolgend **„Auftragnehmer"** genannt –

und

**[Name/Firma Auftraggeber]**
[Straße, Hausnummer]
[PLZ, Ort]
– nachfolgend **„Auftraggeber"** genannt –

wird folgender Wartungsvertrag geschlossen:

---

## § 1 Vertragsgegenstand

(1) Der Auftragnehmer hat für den Auftraggeber die Software **ElbaBot** entwickelt. Diese automatisiert die Annahme von Aufträgen im Portal „Elbaverwaltung" auf Bildschirmebene mittels Bilderkennung (Template Matching) und Maussteuerung, ohne Eingriff in die Portal-Software selbst.

(2) Gegenstand dieses Vertrags ist die Wartung, Pflege und der technische Support dieser Software durch den Auftragnehmer nach Maßgabe der nachfolgenden Bestimmungen. Die Erstellung der ursprünglichen Software ist nicht Gegenstand dieses Vertrags.

## § 2 Leistungsumfang

(1) Der Auftragnehmer erbringt im Rahmen dieses Vertrags folgende Leistungen:

a) **Fehlerbehebung**: Behebung von Fehlfunktionen der Software, die deren vertragsgemäße Nutzung beeinträchtigen (z. B. fehlerhafte Klick-Erkennung, Programmabstürze, fehlerhafte Bildschirmerkennung).

b) **Anpassung bei Portal-Änderungen**: Anpassung der hinterlegten Referenzbilder (Templates) und Suchbereiche, wenn sich die Oberfläche des Portals „Elbaverwaltung" ändert und die automatische Erkennung dadurch nicht mehr funktioniert.

c) **Überwachung**: Einrichtung und Pflege der Heartbeat-Überwachung (ntfy.sh) sowie Unterstützung bei Fernneustarts des Bots im Störungsfall.

d) **Updates**: Einspielen von Aktualisierungen, die für die weitere Lauffähigkeit der Software erforderlich sind (z. B. bei Änderungen der Systemumgebung, Windows-Updates, Abhängigkeiten).

e) **Support**: Telefonische oder elektronische Unterstützung bei Rückfragen zur Bedienung und zum Betrieb der Software im Umfang von bis zu **[X]** Stunden pro Monat.

(2) **Nicht** von diesem Vertrag umfasst sind:

- die Entwicklung neuer Funktionen oder wesentlicher Erweiterungen der Software,
- Anpassungen aufgrund geänderter Anforderungen des Auftraggebers (Change Requests),
- Schäden, die durch unsachgemäße Bedienung, Eingriffe Dritter oder eigenmächtige Änderungen des Auftraggebers am System entstehen,
- die Wartung der zugrunde liegenden Hardware, des Betriebssystems oder des Portals „Elbaverwaltung" selbst.

Leistungen nach Satz 1 können gesondert nach Aufwand beauftragt werden (Stundensatz gemäß § 5 Abs. 3).

## § 3 Reaktions- und Bearbeitungszeiten

(1) Der Auftragnehmer verpflichtet sich, gemeldete Störungen innerhalb folgender Fristen zu bearbeiten:

| Priorität | Beschreibung | Reaktionszeit | Bearbeitung |
|---|---|---|---|
| Kritisch | Bot läuft nicht / nimmt keine Aufträge an | [4] Stunden (werktags) | unverzüglich |
| Hoch | Einzelne Schritte fehlerhaft, Workaround möglich | [1] Werktag | [3] Werktage |
| Niedrig | Sonstige Anfragen, kleinere Optimierungen | [3] Werktage | nach Vereinbarung |

(2) Die Meldung von Störungen erfolgt per [E-Mail/Telefon/ntfy] an [Kontaktadresse].

(3) Die genannten Fristen gelten für Meldungen innerhalb der Geschäftszeiten ([Mo–Fr, 9–17 Uhr]).

## § 4 Mitwirkungspflichten des Auftraggebers

(1) Der Auftraggeber stellt sicher, dass der Auftragnehmer bei Bedarf Fernzugriff auf das System erhält, auf dem die Software betrieben wird (z. B. per Remote-Desktop oder vergleichbarer Software).

(2) Der Auftraggeber meldet Störungen unverzüglich und so detailliert wie möglich (Screenshots, Fehlermeldungen, Uhrzeit des Auftretens).

(3) Der Auftraggeber nimmt keine eigenmächtigen Änderungen am Quellcode, an den Konfigurationsdateien oder den Referenzbildern der Software vor. Bei eigenmächtigen Änderungen entfällt die Gewährleistung/Haftung des Auftragnehmers für hierdurch verursachte Fehler.

## § 5 Vergütung

(1) Für die Leistungen nach § 2 Abs. 1 zahlt der Auftraggeber eine monatliche Pauschale in Höhe von

**[XXX,00] € netto zzgl. gesetzlicher Umsatzsteuer**

(2) Die Pauschale ist im Voraus, jeweils zum [1.] eines Monats, per [Überweisung/Rechnung] fällig.

(3) Leistungen, die nicht von § 2 Abs. 1 umfasst sind (siehe § 2 Abs. 2), werden nach Aufwand zu einem Stundensatz von **[XX,00] € netto** abgerechnet. Der Auftragnehmer informiert den Auftraggeber vorab über den voraussichtlichen Aufwand, sofern dieser [2] Stunden übersteigt.

(4) Fahrt- und sonstige Nebenkosten werden [gesondert nach Nachweis / sind mit der Pauschale abgegolten].

## § 6 Vertragslaufzeit und Kündigung

(1) Dieser Vertrag beginnt am **[Datum]** und läuft auf unbestimmte Zeit.

(2) Er kann von beiden Parteien mit einer Frist von **[X] Wochen/Monaten** zum Monatsende schriftlich gekündigt werden.

(3) Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt unberührt.

## § 7 Gewährleistung und Haftung

(1) Der Auftragnehmer haftet für Schäden nur bei Vorsatz oder grober Fahrlässigkeit. Bei leichter Fahrlässigkeit haftet der Auftragnehmer nur bei Verletzung wesentlicher Vertragspflichten (Kardinalpflichten) und begrenzt auf den bei Vertragsschluss vorhersehbaren, vertragstypischen Schaden.

(2) Die Haftung für entgangenen Gewinn, mittelbare Schäden sowie Schäden aus entgangenen Aufträgen aufgrund einer nicht rechtzeitig erkannten Fehlfunktion der Software ist ausgeschlossen, soweit gesetzlich zulässig.

(3) Der Auftraggeber ist sich bewusst, dass die Software auf Bilderkennung basiert und daher keine 100%ige Erkennungsgenauigkeit garantiert werden kann. Der Auftragnehmer schuldet daher keinen bestimmten Erfolg (z. B. „lückenlose Auftragsannahme"), sondern die in § 2 beschriebene Wartungsleistung.

(4) Die Haftung für Schäden aus der Verletzung des Lebens, des Körpers oder der Gesundheit sowie nach dem Produkthaftungsgesetz bleibt unberührt.

## § 8 Vertraulichkeit und Datenschutz

(1) Beide Parteien verpflichten sich, alle im Rahmen dieses Vertrags erlangten vertraulichen Informationen der jeweils anderen Partei geheim zu halten und nicht an Dritte weiterzugeben.

(2) Soweit im Rahmen der Wartung (insb. bei Fernzugriff) personenbezogene Daten verarbeitet werden, schließen die Parteien bei Bedarf eine gesonderte Vereinbarung zur Auftragsverarbeitung (AVV) nach Art. 28 DSGVO ab.

## § 9 Schlussbestimmungen

(1) Änderungen und Ergänzungen dieses Vertrags bedürfen der Schriftform. Dies gilt auch für die Änderung dieser Schriftformklausel.

(2) Sollte eine Bestimmung dieses Vertrags unwirksam sein oder werden, bleibt die Wirksamkeit der übrigen Bestimmungen unberührt.

(3) Es gilt das Recht der Bundesrepublik Deutschland.

(4) Gerichtsstand ist, soweit gesetzlich zulässig, **[Ort]**.

---

Ort, Datum: ______________________

<br>

| Auftragnehmer | Auftraggeber |
|---|---|
| _______________________ | _______________________ |
| [Name] | [Name] |

---

**Hinweis:** Dies ist ein Entwurf und stellt keine Rechtsberatung dar. Die mit Platzhaltern `[...]` gekennzeichneten Stellen (Firmennamen, Preise, Fristen, Gerichtsstand etc.) sind vor Verwendung auszufüllen bzw. anzupassen. Vor Unterzeichnung wird eine Prüfung durch einen Rechtsanwalt bzw. Steuerberater (insbesondere zu Haftungsklauseln und AGB-Konformität) empfohlen.
