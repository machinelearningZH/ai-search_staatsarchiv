## Über diese App

Mit dieser Applikation können Dokumente der «Zentralen Serien» vom Staatsarchiv Zürich mit einer kombinierten lexikalischen und semantischen Suche durchsucht werden. Die Serien sind öffentlich zugängliche Regierungsratsbeschlüsse, Kantonsratsprotokolle sowie die Gesetzessammlung und der Textteil des Amtsblatts, die das Staatsarchiv für den Zeitraum des 19. und 20. Jahrhunderts aufbereitet hat.

Die Applikation ist Teil eines Projekts des Statistischen Amts und des Staatsarchivs des Kantons Zürich (verantwortlich: [Patrick Arnecke](mailto:patrick.arnecke@statistik.ji.zh.ch) und [Rebekka Plüss](mailto:rebekka.pluess@zh.ch)). 

Sourcecode und die detaillierte Projektdokumentation befinden sich auf einem [öffentlichen Github Repository](https://github.com/machinelearningZH/ai-search_staatsarchiv).

## 🔍 Was ist Semantische Suche?

Im Gegensatz zu einer lexikalischen Suche nach Stichworten kann eine semantische Suche auch **inhaltlich ähnliche** Worte berücksichtigen, die nicht mit dem Suchwort übereinstimmen. Die semantische Suche nach dem Wort *Essen* kann z.B. Texte finden, die die Worte *Lebensmittel*, *Nahrungsmittel*, *Milch*, *Bäckerin* oder *Brot* enthalten, ohne dass das Wort *Essen* darin vorkommt. Die Suche funktioniert auch **bilingual** in Deutsch und Englisch.

Eine semantische Suche kann zudem **Texte mittels eines Referenzdokuments finden**. Eine Suche mit einem Regierungsratsbeschluss führt zu thematisch ähnlich gelagerten Beschlüssen und Geschäften in den vier Serien.

Semantische Suche arbeitet mit statistischen Methoden und Machine Learning. Das System hat auf Basis von grossen Textmengen Wort- und Satzähnlichkeiten gelernt und kann diese Ähnlichkeiten für die Suche nach Dokumenten nutzen.<br><br>Eine semantische Suche hat viele Vorteile. Andererseits führt der Einsatz dieser Methode auch dazu, dass :red[**die Suche nicht exakt ist, sondern näherungsweise arbeitet. Suchergebnisse sind nicht zwingend vollständig, sondern können lückenhaft sein oder auch falsche Treffer enthalten.**]

Wir möchten das System kontinuierlich nach Nutzungsbedürfnissen verbessern. **Wir sind für Rückmeldungen und Anregungen jeglicher Art jederzeit dankbar und nehmen diese gerne [per Mail entgegen](mailto:staatsarchivzh@ji.zh.ch)**

## App-Versionen
- **Version 1.0 vom 5.9.2024**
