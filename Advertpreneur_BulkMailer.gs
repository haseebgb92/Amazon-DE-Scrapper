// ============================================================
// ADVERTPRENEUR BULK MAILER - Google Apps Script
// Localized cold emails based on seller country code
// Columns: A=Seller Name | B=Email | C=Store Name | D=Service | E=Country
//          F=Status (auto) | G=Sent At (auto)
// ============================================================

var CONFIG = {
  SHEET_NAME:    "Sellers",
  FROM_NAME:     "Haseeb | Advertpreneur",
  FROM_EMAIL:    "haseeb@elitewebtechnology.org",
  DAILY_LIMIT:   80,
  DELAY_SECONDS: 8,
  START_ROW:     2,
  TEST_MODE:     false,
  TEST_EMAIL:    "your@email.com",
};

// ============================================================
// LANGUAGE ROUTER
// Supported local languages: DE, ES, FR, NL, RO, IT
// Everything else (CN, US, GB, HK, JP, KR, VN etc.) -> English
// ============================================================

function getLanguage(countryCode) {
  var code = (countryCode || "").toUpperCase().trim();
  var map = {
    "DE": "de", "AT": "de", "CH": "de",       // German
    "ES": "es", "MX": "es", "AR": "es",       // Spanish
    "FR": "fr", "BE": "fr",                    // French
    "NL": "nl",                                // Dutch
    "RO": "ro",                                // Romanian
    "IT": "it",                                // Italian
  };
  return map[code] || "en";
}

// ============================================================
// EMAIL SUBJECTS PER LANGUAGE
// ============================================================

function getSubject(lang) {
  var subjects = {
    en: "Free Amazon Listing Audit for Your Store",
    de: "Kostenloser Amazon-Listing-Audit für Ihren Shop",
    es: "Auditoría gratuita de listado de Amazon para tu tienda",
    fr: "Audit gratuit de votre fiche Amazon",
    nl: "Gratis Amazon-listing audit voor uw winkel",
    ro: "Audit gratuit al listingului Amazon pentru magazinul dvs.",
    it: "Audit gratuito del tuo listato Amazon",
  };
  return subjects[lang] || subjects["en"];
}

// ============================================================
// EMAIL BODIES PER LANGUAGE
// Offer: Free Audit of one ASIN, no strings attached
// About Advertpreneur: Amazon SEO, PPC, Listing Images, A+ Content
// Achievements: page 1 rankings, reduced ad spend, CVR improvements
// ============================================================

function getBody(name, store, lang) {
  var storePart = store ? store : "your store";

  if (lang === "de") {
    var storeDE = store ? store : "Ihrem Shop";
    return (
      "Hallo " + name + ",\n\n" +
      "ich bin auf " + storeDE + " bei Amazon gestoßen und wollte kurz Kontakt aufnehmen.\n\n" +
      "Wir sind Advertpreneur, eine auf Amazon spezialisierte Agentur. Wir helfen Verkäufern dabei, ihre organischen Rankings zu verbessern, die Werbeausgaben zu senken und die Conversion-Rate durch professionelle Listings, A+ Content und gezieltes PPC-Management zu steigern.\n\n" +
      "Was wir für unsere Kunden erreicht haben:\n" +
      "- Seite 1 Rankings für Haupt-Keywords innerhalb von 4 bis 8 Wochen\n" +
      "- Senkung des ACOS um durchschnittlich 30 Prozent durch saubere Kampagnenstruktur\n" +
      "- Steigerung der Conversion-Rate um 15 bis 25 Prozent durch optimierte Bilder und A+ Content\n\n" +
      "Ich würde Ihnen gerne einen kostenlosen Audit eines Ihrer ASINs anbieten. Ich schaue mir Ihre Listings an und zeige Ihnen konkret, wo Optimierungspotenzial besteht. Kein Verkaufsgespräch, nur ehrliches Feedback.\n\n" +
      "Haben Sie Interesse?\n\n" +
      "Mit freundlichen Grüßen\n" +
      "Haseeb\n" +
      "Advertpreneur | Amazon SEO und PPC\n" +
      "advertpreneur.com"
    );
  }

  if (lang === "es") {
    var storeES = store ? store : "tu tienda";
    return (
      "Hola " + name + ",\n\n" +
      "me encontré con " + storeES + " en Amazon y quería ponerme en contacto contigo.\n\n" +
      "Somos Advertpreneur, una agencia especializada en Amazon. Ayudamos a vendedores a mejorar su posicionamiento orgánico, reducir el gasto en publicidad y aumentar la tasa de conversión mediante listados optimizados, contenido A+ y gestión profesional de PPC.\n\n" +
      "Lo que hemos logrado para nuestros clientes:\n" +
      "- Posición en la primera página para palabras clave principales en 4 a 8 semanas\n" +
      "- Reducción del ACOS en un promedio del 30 por ciento con estructura de campañas limpia\n" +
      "- Aumento de la tasa de conversión del 15 al 25 por ciento con imágenes y A+ Content optimizados\n\n" +
      "Me gustaría ofrecerte una auditoría gratuita de uno de tus ASINs. Revisaré tus listings y te mostraré exactamente dónde hay margen de mejora. Sin compromiso, solo feedback honesto.\n\n" +
      "Te parece bien?\n\n" +
      "Un saludo,\n" +
      "Haseeb\n" +
      "Advertpreneur | Amazon SEO y PPC\n" +
      "advertpreneur.com"
    );
  }

  if (lang === "fr") {
    var storeFR = store ? store : "votre boutique";
    return (
      "Bonjour " + name + ",\n\n" +
      "j'ai découvert " + storeFR + " sur Amazon et je souhaitais vous contacter.\n\n" +
      "Nous sommes Advertpreneur, une agence spécialisée Amazon. Nous aidons les vendeurs à améliorer leur positionnement organique, réduire leurs dépenses publicitaires et augmenter leur taux de conversion grâce à des fiches optimisées, du contenu A+ et une gestion professionnelle du PPC.\n\n" +
      "Ce que nous avons accompli pour nos clients:\n" +
      "- Première page pour les mots-clés principaux en 4 à 8 semaines\n" +
      "- Réduction de l'ACOS de 30 pour cent en moyenne grâce à une structure de campagne propre\n" +
      "- Augmentation du taux de conversion de 15 à 25 pour cent grâce à des visuels et un A+ Content optimisés\n\n" +
      "Je vous propose un audit gratuit d'un de vos ASINs. J'analyserai vos fiches et vous indiquerai précisément les axes d'amélioration. Sans engagement, juste un retour honnête.\n\n" +
      "Seriez-vous intéressé?\n\n" +
      "Cordialement,\n" +
      "Haseeb\n" +
      "Advertpreneur | Amazon SEO et PPC\n" +
      "advertpreneur.com"
    );
  }

  if (lang === "nl") {
    var storeNL = store ? store : "uw winkel";
    return (
      "Hallo " + name + ",\n\n" +
      "ik ben " + storeNL + " tegengekomen op Amazon en wilde even contact opnemen.\n\n" +
      "Wij zijn Advertpreneur, een op Amazon gespecialiseerd bureau. We helpen verkopers hun organische rankings te verbeteren, advertentiekosten te verlagen en de conversieratio te verhogen via geoptimaliseerde listings, A+ Content en professioneel PPC-beheer.\n\n" +
      "Wat we voor onze klanten hebben bereikt:\n" +
      "- Pagina 1 rankings voor hoofd-zoekwoorden binnen 4 tot 8 weken\n" +
      "- Gemiddeld 30 procent lagere ACOS door een schone campagnestructuur\n" +
      "- 15 tot 25 procent hogere conversieratio door geoptimaliseerde afbeeldingen en A+ Content\n\n" +
      "Ik bied u graag een gratis audit aan van een van uw ASINs. Ik bekijk uw listings en laat u precies zien waar verbetering mogelijk is. Geen verkooppraatje, gewoon eerlijke feedback.\n\n" +
      "Heeft u interesse?\n\n" +
      "Met vriendelijke groet,\n" +
      "Haseeb\n" +
      "Advertpreneur | Amazon SEO en PPC\n" +
      "advertpreneur.com"
    );
  }

  if (lang === "ro") {
    var storeRO = store ? store : "magazinul dvs.";
    return (
      "Buna ziua " + name + ",\n\n" +
      "am dat peste " + storeRO + " pe Amazon si am vrut sa iau legatura cu dvs.\n\n" +
      "Suntem Advertpreneur, o agentie specializata in Amazon. Ajutam vanzatorii sa isi imbunatateasca pozitionarea organica, sa reduca cheltuielile publicitare si sa creasca rata de conversie prin listing-uri optimizate, continut A+ si gestionare profesionala a PPC.\n\n" +
      "Ce am realizat pentru clientii nostri:\n" +
      "- Prima pagina pentru cuvintele cheie principale in 4 pana la 8 saptamani\n" +
      "- Reducerea ACOS cu 30 la suta in medie printr-o structura curata a campaniilor\n" +
      "- Cresterea ratei de conversie cu 15 pana la 25 la suta prin imagini si A+ Content optimizate\n\n" +
      "As dori sa va ofer un audit gratuit al unuia dintre ASIN-urile dvs. Voi analiza listing-urile si va voi arata exact unde exista potential de imbunatatire. Fara obligatii, doar feedback sincer.\n\n" +
      "Sunteti interesat?\n\n" +
      "Cu stima,\n" +
      "Haseeb\n" +
      "Advertpreneur | Amazon SEO si PPC\n" +
      "advertpreneur.com"
    );
  }

  if (lang === "it") {
    var storeIT = store ? store : "il tuo negozio";
    return (
      "Salve " + name + ",\n\n" +
      "ho trovato " + storeIT + " su Amazon e volevo mettermi in contatto con te.\n\n" +
      "Siamo Advertpreneur, un'agenzia specializzata in Amazon. Aiutiamo i venditori a migliorare il posizionamento organico, ridurre la spesa pubblicitaria e aumentare il tasso di conversione tramite listing ottimizzati, contenuto A+ e gestione professionale del PPC.\n\n" +
      "Cosa abbiamo ottenuto per i nostri clienti:\n" +
      "- Prima pagina per le parole chiave principali in 4 o 8 settimane\n" +
      "- Riduzione dell'ACOS del 30 per cento in media con una struttura delle campagne pulita\n" +
      "- Aumento del tasso di conversione dal 15 al 25 per cento con immagini e A+ Content ottimizzati\n\n" +
      "Ti offro volentieri un audit gratuito di uno dei tuoi ASIN. Analizzerò i tuoi listing e ti mostrero esattamente dove c'e margine di miglioramento. Nessun impegno, solo un feedback onesto.\n\n" +
      "Sei interessato?\n\n" +
      "Cordiali saluti,\n" +
      "Haseeb\n" +
      "Advertpreneur | Amazon SEO e PPC\n" +
      "advertpreneur.com"
    );
  }

  // Default: English
  return (
    "Hi " + name + ",\n\n" +
    "I came across " + storePart + " on Amazon and wanted to reach out.\n\n" +
    "We are Advertpreneur, an Amazon-focused agency. We help sellers improve organic rankings, reduce ad spend, and increase conversion rates through optimized listings, A+ Content, and professional PPC management.\n\n" +
    "What we have achieved for our clients:\n" +
    "- Page 1 rankings for main keywords within 4 to 8 weeks\n" +
    "- Average 30 percent reduction in ACOS through clean campaign structure\n" +
    "- 15 to 25 percent increase in conversion rate through optimized images and A+ Content\n\n" +
    "I would like to offer you a free audit of one of your ASINs. I will look at your listings and show you exactly where there is room for improvement. No sales pitch, just honest feedback.\n\n" +
    "Would you be interested?\n\n" +
    "Best regards,\n" +
    "Haseeb\n" +
    "Advertpreneur | Amazon SEO and PPC\n" +
    "advertpreneur.com"
  );
}

// ============================================================
// MAIN SEND FUNCTION
// Columns: A=Name | B=Email | C=Store | D=Service | E=Country
//          F=Status | G=Sent At
// ============================================================

function sendBulkEmails() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Sheet "' + CONFIG.SHEET_NAME + '" not found.');
    return;
  }

  var lastRow      = sheet.getLastRow();
  var sentCount    = 0;
  var skippedCount = 0;
  var failedCount  = 0;

  for (var i = CONFIG.START_ROW; i <= lastRow; i++) {
    if (sentCount >= CONFIG.DAILY_LIMIT) {
      Logger.log("Daily limit reached.");
      break;
    }

    var name    = sheet.getRange(i, 1).getValue().toString().trim();
    var email   = sheet.getRange(i, 2).getValue().toString().trim();
    var store   = sheet.getRange(i, 3).getValue().toString().trim();
    var country = sheet.getRange(i, 5).getValue().toString().trim();
    var status  = sheet.getRange(i, 6).getValue().toString().trim();

    if (status === "Sent" || status === "Skipped") { skippedCount++; continue; }
    if (!email || !isValidEmail(email)) {
      sheet.getRange(i, 6).setValue("Skipped - Invalid Email");
      sheet.getRange(i, 7).setValue(new Date());
      skippedCount++;
      continue;
    }
    if (!name) name = "there";

    var lang      = getLanguage(country);
    var subject   = getSubject(lang);
    var body      = getBody(name, store, lang);
    var recipient = CONFIG.TEST_MODE ? CONFIG.TEST_EMAIL : email;

    try {
      GmailApp.sendEmail(recipient, subject, body, {
        name: CONFIG.FROM_NAME,
        from: CONFIG.FROM_EMAIL
      });
      sheet.getRange(i, 6).setValue("Sent (" + lang.toUpperCase() + ")");
      sheet.getRange(i, 7).setValue(new Date());
      sentCount++;
      Logger.log("Sent [" + lang + "] to: " + recipient + " (" + name + ")");
      if (i < lastRow) Utilities.sleep(CONFIG.DELAY_SECONDS * 1000);
    } catch(e) {
      sheet.getRange(i, 6).setValue("Failed: " + e.message);
      sheet.getRange(i, 7).setValue(new Date());
      failedCount++;
    }
  }

  SpreadsheetApp.getUi().alert(
    "Done!\n\nSent:    " + sentCount +
    "\nSkipped: " + skippedCount +
    "\nFailed:  " + failedCount
  );
}

function resumeSending()  { sendBulkEmails(); }

function resetStatus() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  var ui    = SpreadsheetApp.getUi();
  var r     = ui.alert("Reset All Status?", "Clear Status and Sent At for all rows?", ui.ButtonSet.YES_NO);
  if (r === ui.Button.YES) {
    sheet.getRange(CONFIG.START_ROW, 6, sheet.getLastRow() - 1, 2).clearContent();
    ui.alert("Status reset.");
  }
}

function sendTestEmail() {
  var sheet   = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) { SpreadsheetApp.getUi().alert('Sheet not found.'); return; }
  var name    = sheet.getRange(2, 1).getValue().toString().trim() || "Test Seller";
  var store   = sheet.getRange(2, 3).getValue().toString().trim();
  var country = sheet.getRange(2, 5).getValue().toString().trim() || "US";
  var lang    = getLanguage(country);
  var subject = getSubject(lang);
  var body    = getBody(name, store, lang);
  GmailApp.sendEmail(CONFIG.TEST_EMAIL, "[TEST " + lang.toUpperCase() + "] " + subject, body, {
    name: CONFIG.FROM_NAME,
    from: CONFIG.FROM_EMAIL
  });
  SpreadsheetApp.getUi().alert("Test email sent to " + CONFIG.TEST_EMAIL + "\nLanguage used: " + lang.toUpperCase() + " (Country: " + country + ")");
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Bulk Mailer")
    .addItem("Send Emails", "sendBulkEmails")
    .addItem("Resume Sending", "resumeSending")
    .addSeparator()
    .addItem("Send Test Email", "sendTestEmail")
    .addItem("Reset Status", "resetStatus")
    .addToUi();
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function setupDailyTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) ScriptApp.deleteTrigger(triggers[i]);
  ScriptApp.newTrigger("sendBulkEmails").timeBased().everyDays(1).atHour(9).nearMinute(0).create();
  var tz = Session.getScriptTimeZone();
  SpreadsheetApp.getUi().alert("Daily trigger set!\n\nWill send at 9 AM in: " + tz);
}

function removeDailyTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) ScriptApp.deleteTrigger(triggers[i]);
  SpreadsheetApp.getUi().alert("All triggers removed.");
}
