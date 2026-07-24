"""
WiseBudget AI - lightweight interface translations (i18n).

Design goals:
  * English is the source of truth. Every translatable string is stored and
    looked up BY ITS ENGLISH TEXT, so anything without a translation simply
    falls back to English (the app never shows a blank or a raw key).
  * Adding a language = adding one dict below. Adding a string = adding one
    English key and its translations. No key bookkeeping to keep in sync.
  * We translate the INTERFACE (navigation, headings, labels, buttons,
    disclaimers) only. The saving-opportunity advice, rule text and AI output
    stay in English for now so their carefully-worded, education-only phrasing
    is never altered by a loose translation.

Usage:
    import i18n
    i18n.t("Dashboard", "es")   # -> "Panel"
    i18n.t("Anything untranslated", "es")  # -> "Anything untranslated"
"""

# Display name of each language, shown in its own language, keyed by code.
# English first; the rest alphabetical by English name.
LANGUAGES = {
    "en": "English",
    "cs": "Čeština",
    "nl": "Nederlands",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pl": "Polski",
    "pt": "Português",
    "ro": "Română",
    "es": "Español",
    "sv": "Svenska",
}

# English string -> {lang_code: translation}. Only the interface skeleton is
# covered so far; unlisted strings fall back to English automatically.
_STRINGS = {
    # ---- Navigation & chrome ----
    "Navigation": {
        "es": "Navegación", "fr": "Navigation", "de": "Navigation", "it": "Navigazione",
        "pt": "Navegação", "nl": "Navigatie", "pl": "Nawigacja", "ro": "Navigare",
        "sv": "Navigering", "cs": "Navigace",
    },
    "Language": {
        "es": "Idioma", "fr": "Langue", "de": "Sprache", "it": "Lingua",
        "pt": "Idioma", "nl": "Taal", "pl": "Język", "ro": "Limbă",
        "sv": "Språk", "cs": "Jazyk",
    },
    "Demo Mode": {
        "es": "Modo demo", "fr": "Mode démo", "de": "Demo-Modus", "it": "Modalità demo",
        "pt": "Modo demo", "nl": "Demomodus", "pl": "Tryb demo", "ro": "Mod demo",
        "sv": "Demoläge", "cs": "Režim demo",
    },
    "Dashboard": {
        "es": "Panel", "fr": "Tableau de bord", "de": "Übersicht", "it": "Pannello",
        "pt": "Painel", "nl": "Overzicht", "pl": "Panel", "ro": "Panou",
        "sv": "Översikt", "cs": "Přehled",
    },
    "Add Income": {
        "es": "Añadir ingreso", "fr": "Ajouter un revenu", "de": "Einnahme hinzufügen",
        "it": "Aggiungi entrata", "pt": "Adicionar rendimento", "nl": "Inkomsten toevoegen",
        "pl": "Dodaj przychód", "ro": "Adaugă venit", "sv": "Lägg till inkomst",
        "cs": "Přidat příjem",
    },
    "Add Expense": {
        "es": "Añadir gasto", "fr": "Ajouter une dépense", "de": "Ausgabe hinzufügen",
        "it": "Aggiungi spesa", "pt": "Adicionar despesa", "nl": "Uitgave toevoegen",
        "pl": "Dodaj wydatek", "ro": "Adaugă cheltuială", "sv": "Lägg till utgift",
        "cs": "Přidat výdaj",
    },
    "WiseBudget AI Coach": {
        "es": "Asesor WiseBudget AI", "fr": "Coach WiseBudget AI", "de": "WiseBudget AI Coach",
        "it": "Coach WiseBudget AI", "pt": "Assistente WiseBudget AI", "nl": "WiseBudget AI-coach",
        "pl": "Asystent WiseBudget AI", "ro": "Asistent WiseBudget AI", "sv": "WiseBudget AI-coach",
        "cs": "Asistent WiseBudget AI",
    },
    "Savings Goals": {
        "es": "Objetivos de ahorro", "fr": "Objectifs d'épargne", "de": "Sparziele",
        "it": "Obiettivi di risparmio", "pt": "Metas de poupança", "nl": "Spaardoelen",
        "pl": "Cele oszczędnościowe", "ro": "Obiective de economisire", "sv": "Sparmål",
        "cs": "Cíle spoření",
    },
    "Projections": {
        "es": "Proyecciones", "fr": "Projections", "de": "Prognosen", "it": "Proiezioni",
        "pt": "Projeções", "nl": "Prognoses", "pl": "Prognozy", "ro": "Proiecții",
        "sv": "Prognoser", "cs": "Projekce",
    },
    "Investment Learning Hub": {
        "es": "Centro de aprendizaje de inversión", "fr": "Espace apprentissage de l'investissement",
        "de": "Lernbereich Investieren", "it": "Centro didattico sugli investimenti",
        "pt": "Centro de aprendizagem de investimento", "nl": "Leercentrum beleggen",
        "pl": "Centrum nauki o inwestowaniu", "ro": "Centru de învățare despre investiții",
        "sv": "Läromodul om investeringar", "cs": "Vzdělávací centrum investování",
    },
    "Feedback": {
        "es": "Comentarios", "fr": "Retour d'expérience", "de": "Feedback", "it": "Feedback",
        "pt": "Comentários", "nl": "Feedback", "pl": "Opinie", "ro": "Feedback",
        "sv": "Feedback", "cs": "Zpětná vazba",
    },
    "App menu": {
        "es": "Menú de la app", "fr": "Menu de l'app", "de": "App-Menü", "it": "Menu dell'app",
        "pt": "Menu da app", "nl": "App-menu", "pl": "Menu aplikacji", "ro": "Meniul aplicației",
        "sv": "App-meny", "cs": "Nabídka aplikace",
    },
    "Go to page": {
        "es": "Ir a la página", "fr": "Aller à la page", "de": "Zur Seite", "it": "Vai alla pagina",
        "pt": "Ir para a página", "nl": "Ga naar pagina", "pl": "Przejdź do strony",
        "ro": "Mergi la pagină", "sv": "Gå till sida", "cs": "Přejít na stránku",
    },
    "AI Settings": {
        "es": "Ajustes de IA", "fr": "Paramètres IA", "de": "KI-Einstellungen",
        "it": "Impostazioni IA", "pt": "Definições de IA", "nl": "AI-instellingen",
        "pl": "Ustawienia AI", "ro": "Setări IA", "sv": "AI-inställningar", "cs": "Nastavení AI",
    },

    # ---- Hero ----
    "Take control of your spending": {
        "es": "Toma el control de tus gastos", "fr": "Prenez le contrôle de vos dépenses",
        "de": "Behalte deine Ausgaben im Griff", "it": "Prendi il controllo delle tue spese",
        "pt": "Assuma o controlo dos seus gastos", "nl": "Krijg grip op je uitgaven",
        "pl": "Przejmij kontrolę nad wydatkami", "ro": "Preia controlul asupra cheltuielilor tale",
        "sv": "Ta kontroll över dina utgifter", "cs": "Převezměte kontrolu nad svými výdaji",
    },
    "Track your money, spot saving opportunities, and learn better financial habits.": {
        "es": "Controla tu dinero, detecta oportunidades de ahorro y aprende mejores hábitos financieros.",
        "fr": "Suivez votre argent, repérez des occasions d'économiser et adoptez de meilleures habitudes financières.",
        "de": "Behalte dein Geld im Blick, finde Sparmöglichkeiten und lerne bessere Finanzgewohnheiten.",
        "it": "Tieni traccia dei tuoi soldi, individua opportunità di risparmio e impara abitudini finanziarie migliori.",
        "pt": "Acompanhe o seu dinheiro, encontre oportunidades de poupança e aprenda melhores hábitos financeiros.",
        "nl": "Volg je geld, ontdek bespaarkansen en leer betere financiële gewoonten.",
        "pl": "Śledź swoje pieniądze, znajduj okazje do oszczędzania i ucz się lepszych nawyków finansowych.",
        "ro": "Urmărește-ți banii, descoperă oportunități de economisire și învață obiceiuri financiare mai bune.",
        "sv": "Håll koll på dina pengar, hitta sparmöjligheter och lär dig bättre ekonomiska vanor.",
        "cs": "Sledujte své peníze, najděte příležitosti k úsporám a osvojte si lepší finanční návyky.",
    },
    "Local-first": {
        "es": "Local primero", "fr": "Local d'abord", "de": "Lokal zuerst", "it": "Prima locale",
        "pt": "Local primeiro", "nl": "Lokaal eerst", "pl": "Najpierw lokalnie", "ro": "Local mai întâi",
        "sv": "Lokalt först", "cs": "Nejdřív lokálně",
    },
    "Education only": {
        "es": "Solo educación", "fr": "Éducation uniquement", "de": "Nur zu Bildungszwecken",
        "it": "Solo a scopo didattico", "pt": "Apenas educação", "nl": "Alleen educatie",
        "pl": "Tylko edukacja", "ro": "Doar educație", "sv": "Endast utbildning",
        "cs": "Pouze vzdělávání",
    },
    "Estimates, not guarantees": {
        "es": "Estimaciones, no garantías", "fr": "Des estimations, pas des garanties",
        "de": "Schätzungen, keine Garantien", "it": "Stime, non garanzie",
        "pt": "Estimativas, não garantias", "nl": "Schattingen, geen garanties",
        "pl": "Szacunki, nie gwarancje", "ro": "Estimări, nu garanții",
        "sv": "Uppskattningar, inga garantier", "cs": "Odhady, nikoli záruky",
    },
    "Demo Mode: using example data only": {
        "es": "Modo demo: usando solo datos de ejemplo",
        "fr": "Mode démo : données d'exemple uniquement",
        "de": "Demo-Modus: nur Beispieldaten", "it": "Modalità demo: solo dati di esempio",
        "pt": "Modo demo: a usar apenas dados de exemplo", "nl": "Demomodus: alleen voorbeeldgegevens",
        "pl": "Tryb demo: tylko przykładowe dane", "ro": "Mod demo: doar date exemplu",
        "sv": "Demoläge: endast exempeldata", "cs": "Režim demo: pouze ukázková data",
    },

    # ---- Dashboard & common ----
    "Period": {
        "es": "Periodo", "fr": "Période", "de": "Zeitraum", "it": "Periodo", "pt": "Período",
        "nl": "Periode", "pl": "Okres", "ro": "Perioadă", "sv": "Period", "cs": "Období",
    },
    "All time": {
        "es": "Todo el tiempo", "fr": "Depuis le début", "de": "Gesamter Zeitraum",
        "it": "Sempre", "pt": "Desde o início", "nl": "Alle tijd", "pl": "Cały okres",
        "ro": "Tot timpul", "sv": "All tid", "cs": "Za celou dobu",
    },
    "Total Income": {
        "es": "Ingresos totales", "fr": "Revenu total", "de": "Gesamteinnahmen",
        "it": "Entrate totali", "pt": "Rendimento total", "nl": "Totale inkomsten",
        "pl": "Całkowity dochód", "ro": "Venit total", "sv": "Total inkomst", "cs": "Celkový příjem",
    },
    "Total Expenses": {
        "es": "Gastos totales", "fr": "Dépenses totales", "de": "Gesamtausgaben",
        "it": "Spese totali", "pt": "Despesas totais", "nl": "Totale uitgaven",
        "pl": "Całkowite wydatki", "ro": "Cheltuieli totale", "sv": "Totala utgifter",
        "cs": "Celkové výdaje",
    },
    "Remaining Balance": {
        "es": "Saldo restante", "fr": "Solde restant", "de": "Verbleibender Saldo",
        "it": "Saldo rimanente", "pt": "Saldo restante", "nl": "Resterend saldo",
        "pl": "Pozostałe saldo", "ro": "Sold rămas", "sv": "Återstående saldo",
        "cs": "Zbývající zůstatek",
    },
    "Savings Rate": {
        "es": "Tasa de ahorro", "fr": "Taux d'épargne", "de": "Sparquote", "it": "Tasso di risparmio",
        "pt": "Taxa de poupança", "nl": "Spaarpercentage", "pl": "Stopa oszczędności",
        "ro": "Rata de economisire", "sv": "Sparkvot", "cs": "Míra úspor",
    },
    "Income recorded for this period": {
        "es": "Ingresos registrados en este periodo", "fr": "Revenus enregistrés pour cette période",
        "de": "In diesem Zeitraum erfasste Einnahmen", "it": "Entrate registrate per questo periodo",
        "pt": "Rendimento registado neste período", "nl": "Inkomsten geregistreerd voor deze periode",
        "pl": "Dochód zapisany w tym okresie", "ro": "Venit înregistrat pentru această perioadă",
        "sv": "Inkomst registrerad för denna period", "cs": "Příjem zaznamenaný za toto období",
    },
    "Spending recorded for this period": {
        "es": "Gastos registrados en este periodo", "fr": "Dépenses enregistrées pour cette période",
        "de": "In diesem Zeitraum erfasste Ausgaben", "it": "Spese registrate per questo periodo",
        "pt": "Gastos registados neste período", "nl": "Uitgaven geregistreerd voor deze periode",
        "pl": "Wydatki zapisane w tym okresie", "ro": "Cheltuieli înregistrate pentru această perioadă",
        "sv": "Utgifter registrerade för denna period", "cs": "Výdaje zaznamenané za toto období",
    },
    "Income minus expenses": {
        "es": "Ingresos menos gastos", "fr": "Revenus moins dépenses", "de": "Einnahmen minus Ausgaben",
        "it": "Entrate meno spese", "pt": "Rendimento menos despesas", "nl": "Inkomsten min uitgaven",
        "pl": "Dochód minus wydatki", "ro": "Venit minus cheltuieli", "sv": "Inkomst minus utgifter",
        "cs": "Příjmy minus výdaje",
    },
    "Money kept after living costs": {
        "es": "Dinero que queda tras los gastos de vida", "fr": "Argent conservé après les frais de subsistance",
        "de": "Geld nach den Lebenshaltungskosten", "it": "Denaro rimasto dopo le spese di vita",
        "pt": "Dinheiro que sobra após os custos de vida", "nl": "Geld over na levenskosten",
        "pl": "Pieniądze pozostałe po kosztach życia", "ro": "Bani rămași după costurile de trai",
        "sv": "Pengar kvar efter levnadskostnader", "cs": "Peníze zbylé po životních nákladech",
    },
    "Your Top 3 Money Actions": {
        "es": "Tus 3 principales acciones de dinero", "fr": "Vos 3 actions financières prioritaires",
        "de": "Deine 3 wichtigsten Geld-Aktionen", "it": "Le tue 3 principali azioni sul denaro",
        "pt": "As suas 3 principais ações de dinheiro", "nl": "Jouw top 3 geldacties",
        "pl": "Twoje 3 najważniejsze działania finansowe", "ro": "Primele tale 3 acțiuni pentru bani",
        "sv": "Dina 3 viktigaste pengaåtgärder", "cs": "Vaše 3 hlavní finanční kroky",
    },
    "Smart Saving Opportunities": {
        "es": "Oportunidades inteligentes de ahorro", "fr": "Opportunités d'économies intelligentes",
        "de": "Clevere Sparmöglichkeiten", "it": "Opportunità di risparmio intelligenti",
        "pt": "Oportunidades inteligentes de poupança", "nl": "Slimme bespaarkansen",
        "pl": "Inteligentne okazje do oszczędzania", "ro": "Oportunități inteligente de economisire",
        "sv": "Smarta sparmöjligheter", "cs": "Chytré příležitosti k úsporám",
    },
    "Spending by Category": {
        "es": "Gasto por categoría", "fr": "Dépenses par catégorie", "de": "Ausgaben nach Kategorie",
        "it": "Spese per categoria", "pt": "Gastos por categoria", "nl": "Uitgaven per categorie",
        "pl": "Wydatki według kategorii", "ro": "Cheltuieli pe categorii", "sv": "Utgifter per kategori",
        "cs": "Výdaje podle kategorie",
    },
    "Income vs Expenses by Month": {
        "es": "Ingresos frente a gastos por mes", "fr": "Revenus et dépenses par mois",
        "de": "Einnahmen und Ausgaben pro Monat", "it": "Entrate e spese per mese",
        "pt": "Rendimento vs despesas por mês", "nl": "Inkomsten vs uitgaven per maand",
        "pl": "Dochód a wydatki według miesiąca", "ro": "Venituri și cheltuieli pe lună",
        "sv": "Inkomster mot utgifter per månad", "cs": "Příjmy a výdaje podle měsíce",
    },
    "Savings Goals Overview": {
        "es": "Resumen de objetivos de ahorro", "fr": "Aperçu des objectifs d'épargne",
        "de": "Überblick der Sparziele", "it": "Panoramica degli obiettivi di risparmio",
        "pt": "Resumo das metas de poupança", "nl": "Overzicht spaardoelen",
        "pl": "Przegląd celów oszczędnościowych", "ro": "Prezentare generală a obiectivelor de economisire",
        "sv": "Översikt över sparmål", "cs": "Přehled cílů spoření",
    },
    "Records & export": {
        "es": "Registros y exportación", "fr": "Données et export", "de": "Datensätze & Export",
        "it": "Dati ed esportazione", "pt": "Registos e exportação", "nl": "Gegevens en export",
        "pl": "Rekordy i eksport", "ro": "Înregistrări și export", "sv": "Poster och export",
        "cs": "Záznamy a export",
    },
    "Budget snapshot": {
        "es": "Resumen del presupuesto", "fr": "Aperçu du budget", "de": "Budget-Überblick",
        "it": "Riepilogo del budget", "pt": "Resumo do orçamento", "nl": "Budgetoverzicht",
        "pl": "Migawka budżetu", "ro": "Instantaneu al bugetului", "sv": "Budgetöversikt",
        "cs": "Přehled rozpočtu",
    },
    "Quick checks": {
        "es": "Comprobaciones rápidas", "fr": "Vérifications rapides", "de": "Schnellchecks",
        "it": "Controlli rapidi", "pt": "Verificações rápidas", "nl": "Snelle checks",
        "pl": "Szybkie sprawdzenia", "ro": "Verificări rapide", "sv": "Snabbkontroller",
        "cs": "Rychlé kontroly",
    },
    "Generate AI saving plan": {
        "es": "Generar plan de ahorro con IA", "fr": "Générer un plan d'épargne IA",
        "de": "KI-Sparplan erstellen", "it": "Genera piano di risparmio IA",
        "pt": "Gerar plano de poupança com IA", "nl": "AI-bespaarplan genereren",
        "pl": "Wygeneruj plan oszczędzania AI", "ro": "Generează plan de economisire cu IA",
        "sv": "Skapa AI-sparplan", "cs": "Vytvořit plán úspor s AI",
    },
}


def t(text, lang="en"):
    """Translate an English UI string into `lang`, falling back to English."""
    if lang == "en" or not lang:
        return text
    return _STRINGS.get(text, {}).get(lang, text)
