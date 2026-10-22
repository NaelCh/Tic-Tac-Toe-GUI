# Έκδοση κινητού

Εγκαταστάσιμη εφαρμογή web (PWA) για Android και iPhone, στο ίδιο repository με
την εφαρμογή υπολογιστή. Δεν χρειάζεται server παιχνιδιού ή συνδρομή φιλοξενίας:
τα στατικά αρχεία δημοσιεύονται στο GitHub Pages. Οι δύο παίκτες μοιράζονται την
ίδια συσκευή. Δεν υπάρχει ακόμη online αναμέτρηση.

## Εγκατάσταση

Άνοιξε https://naelch.github.io/Tic-Tac-Toe-GUI/ με Chrome στο Android ή Safari
στο iPhone. Πρόσθεσε την εφαρμογή στην αρχική οθόνη από το κουμπί εγκατάστασης
ή το μενού του browser (στο Safari: Κοινοποίηση → Προσθήκη στην οθόνη Αφετηρίας).
Περίμενε την ένδειξη «Έτοιμο για offline» πριν αποσυνδεθείς. Τα αρχεία ήχου και
το παιχνίδι αποθηκεύονται από τον service worker. Αν ο browser διαγράψει τα
δεδομένα του site, χρειάζεται μία ακόμη φόρτωση με σύνδεση.

## Ανάπτυξη και έλεγχοι

Από τη ρίζα του repository, με Node.js 22+:

```sh
node --test web/tests/*.test.js
node web/build.mjs
python3 -m http.server 8000 --directory dist-mobile
```

Άνοιξε το `http://localhost:8000` για τοπική ανάπτυξη. Το `dist-mobile` είναι
παραγόμενο πακέτο και δεν αποθηκεύεται στο Git. Σε πραγματικό κινητό χρειάζεται
HTTPS για service worker και εγκατάσταση· το GitHub Pages το παρέχει.

Ο έλεγχος browser χρειάζεται Python, `playwright==1.62.0` και εγκατεστημένο
Chrome/Chromium. Δεν χρειάζεται Node dependency ή λήψη browser από το Playwright:

```sh
python3 -m pip install playwright==1.62.0
CHROMIUM_PATH=/usr/bin/chromium python3 web/test_browser.py
```

Ο έλεγχος σερβίρει το production πακέτο κάτω από `/Tic-Tac-Toe-GUI/`, όπως στο
GitHub Pages, και ελέγχει αφή, μικρές/οριζόντιες οθόνες, σκορ, AI, ρυθμίσεις,
διαλόγους και πλήρη offline παρτίδα. Δεν αντικαθιστά δοκιμή εγκατάστασης σε
πραγματική συσκευή και Safari.

## Δημοσίευση και ενημερώσεις

Το workflow `Mobile web app` εκτελείται σε αλλαγές του `web/` στο `master` ή
χειροκίνητα από Actions. Ελέγχει, δημιουργεί το `dist-mobile`, το δημοσιεύει
μέσω GitHub Pages και επαληθεύει μέσω HTTPS το commit και τους πόρους PWA.
Στις ρυθμίσεις repository, το **Settings → Pages → Source** πρέπει να είναι
**GitHub Actions**. Το workflow επιχειρεί την αρχική ενεργοποίηση αυτόματα.
Τα production αρχεία διατίθενται επίσης ως artifact `mobile-web`.

Κάθε build υπολογίζει έκδοση cache από κώδικα, εικονίδια και ήχους. Ο παίκτης
βλέπει ειδοποίηση όταν υπάρχει νεότερη έκδοση και επιλέγει πότε θα ανανεωθεί
το παιχνίδι. Το ενεργό HTML και τα scripts παραμένουν από την ίδια έκδοση.
Δεν υπάρχουν εξωτερικά scripts, analytics, λογαριασμοί ή προσωπικά δεδομένα.

Τα WAV αντιγράφονται από το `assets/sounds` της εφαρμογής υπολογιστή και οι
γνωστοποιήσεις αδειών από το `THIRD_PARTY.md`. Η μηχανή JavaScript ακολουθεί
τις ίδιες δυσκολίες με την Python και ελέγχεται σε όλες τις προσπελάσιμες θέσεις.
