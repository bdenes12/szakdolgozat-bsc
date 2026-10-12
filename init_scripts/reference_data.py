PRACTITIONERS_PER_DEPARTMENT = 5

INSURERS = [
    "NEAK", "Generali", "Union Biztosító", "Allianz Hungária",
    "Signal Iduna", "Uniqa", "Groupama", "MediHelp International",
]
COVERAGE_TYPES = ["ALAP", "BŐVÍTETT", "PRÉMIUM", "VÁLLALATI"]

# havi díj tartomány fedezettípusonként (Ft)
PREMIUM_RANGES = {
    "ALAP": (8000, 15000),
    "BŐVÍTETT": (15000, 30000),
    "PRÉMIUM": (30000, 70000),
    "VÁLLALATI": (12000, 25000),
}
POLICY_DURATIONS_YEARS = [1, 2, 5]

ENCOUNTER_TYPES = [("járóbeteg", 60), ("sürgősségi", 25), ("fekvőbeteg", 15)]

TRIAGE_LEVELS = [(1, 3), (2, 12), (3, 40), (4, 30), (5, 15)]

# ellátástípusonként a bennfekvés napjainak tartománya
STAY_DAYS_BY_TYPE = {
    "járóbeteg": (0, 0),
    "sürgősségi": (0, 1),
    "fekvőbeteg": (2, 14),
}

DEPARTMENTS_DATA = [
    ("Belgyógyászat", "A", 2, "201"),
    ("Sebészet", "A", 3, "305"),
    ("Kardiológia", "B", 1, "112"),
    ("Neurológia", "B", 2, "224"),
    ("Ortopédia", "C", 1, "130"),
    ("Sürgősségi Betegellátó Osztály", "A", 0, "100"),
    ("Gyermekgyógyászat", "C", 2, "240"),
    ("Radiológia", "B", 0, "105")
]

SPECIALTIES_BY_DEPARTMENT = {
    "Belgyógyászat": ["belgyógyászat", "endokrinológia", "gasztroenterológia", "nefrológia"],
    "Sebészet": ["általános sebészet", "érsebészet", "mellkassebészet"],
    "Kardiológia": ["kardiológia", "invazív kardiológia"],
    "Neurológia": ["neurológia", "stroke-ellátás"],
    "Ortopédia": ["ortopédia", "traumatológia"],
    "Sürgősségi Betegellátó Osztály": ["sürgősségi orvostan", "aneszteziológia"],
    "Gyermekgyógyászat": ["gyermekgyógyászat", "neonatológia"],
    "Radiológia": ["radiológia", "ultrahang-diagnosztika"],
}

PAYMENT_STATUSES = ["kifizetett", "részben fizetett", "függőben", "törölt"]

LAB_TESTS = [
    ("Hemoglobin",        "g/L",    140.0, 15.0),
    ("Fehérvérsejtszám",  "10^9/L",   7.0,  2.0),
    ("Vérlemezkeszám",    "10^9/L", 250.0, 60.0),
    ("Éhomi vércukor",    "mmol/L",   5.4,  1.1),
    ("HbA1c",             "%",        5.8,  0.9),
    ("Összkoleszterin",   "mmol/L",   5.2,  1.0),
    ("HDL-koleszterin",   "mmol/L",   1.4,  0.3),
    ("LDL-koleszterin",   "mmol/L",   3.2,  0.9),
    ("Triglicerid",       "mmol/L",   1.6,  0.8),
    ("Kreatinin",         "umol/L",  80.0, 20.0),
    ("Karbamid",          "mmol/L",   5.5,  1.8),
    ("Nátrium",           "mmol/L", 140.0,  3.0),
    ("Kálium",            "mmol/L",   4.2,  0.4),
    ("CRP",               "mg/L",     6.0, 12.0),
    ("TSH",               "mIU/L",    2.0,  1.0),
    ("ALT",               "U/L",     28.0, 14.0),
    ("AST",               "U/L",     26.0, 12.0),
    ("Bilirubin",         "umol/L",  12.0,  5.0),
]

ICD_CODES_DATA= [
    ("A09",   "Fertőzéses eredetű gastroenteritis",      "Fertőző betegségek",        False),
    ("B34.9", "Nem meghatározott vírusfertőzés",         "Fertőző betegségek",        False),
    ("C34.9", "Hörgő és tüdő rosszindulatú daganata",    "Daganatok",                 True),
    ("C50.9", "Emlő rosszindulatú daganata",             "Daganatok",                 True),
    ("D50.9", "Vashiányos vérszegénység",                "Vérképzőszervi betegségek", False),
    ("E03.9", "Pajzsmirigy-alulműködés",                 "Endokrin betegségek",       True),
    ("E11.9", "2-es típusú cukorbetegség",               "Endokrin betegségek",       True),
    ("E66.9", "Elhízás",                                 "Endokrin betegségek",       True),
    ("E78.0", "Tiszta hypercholesterinaemia",            "Endokrin betegségek",       True),
    ("F32.1", "Közepesen súlyos depressziós epizód",     "Mentális betegségek",       False),
    ("F41.1", "Generalizált szorongásos zavar",          "Mentális betegségek",       True),
    ("G20",   "Parkinson-kór",                           "Idegrendszeri betegségek",  True),
    ("G40.9", "Epilepszia",                              "Idegrendszeri betegségek",  True),
    ("G43.9", "Migrén",                                  "Idegrendszeri betegségek",  True),
    ("I10",   "Esszenciális magas vérnyomás",            "Keringési betegségek",      True),
    ("I20.0", "Instabil angina pectoris",                "Keringési betegségek",      False),
    ("I21.9", "Akut szívizominfarktus",                  "Keringési betegségek",      False),
    ("I48.0", "Pitvarfibrilláció",                       "Keringési betegségek",      True),
    ("I50.0", "Pangásos szívelégtelenség",               "Keringési betegségek",      True),
    ("I63.9", "Agyi infarktus",                          "Keringési betegségek",      False),
    ("I83.9", "Alsó végtagi visszértágulat",             "Keringési betegségek",      True),
    ("J06.9", "Felső légúti fertőzés",                   "Légzőszervi betegségek",    False),
    ("J18.9", "Tüdőgyulladás",                           "Légzőszervi betegségek",    False),
    ("J44.9", "Krónikus obstruktív tüdőbetegség",        "Légzőszervi betegségek",    True),
    ("J45.9", "Asztma",                                  "Légzőszervi betegségek",    True),
    ("K21.0", "Reflux nyelőcsőgyulladással",             "Emésztőszervi betegségek",  True),
    ("K29.7", "Gyomorhurut",                             "Emésztőszervi betegségek",  False),
    ("K35.8", "Heveny vakbélgyulladás",                  "Emésztőszervi betegségek",  False),
    ("K57.3", "Vastagbél-diverticulosis",                "Emésztőszervi betegségek",  True),
    ("K80.2", "Epekő epehólyag-gyulladás nélkül",        "Emésztőszervi betegségek",  False),
    ("L03.1", "Végtag cellulitisze",                     "Bőrbetegségek",             False),
    ("M17.1", "Térdízületi arthrosis",                   "Mozgásszervi betegségek",   True),
    ("M51.1", "Porckorongsérv gyöki tünetekkel",         "Mozgásszervi betegségek",   False),
    ("M54.5", "Derékfájás",                              "Mozgásszervi betegségek",   False),
    ("M81.0", "Posztmenopauzális csontritkulás",         "Mozgásszervi betegségek",   True),
    ("N18.3", "Krónikus vesebetegség, 3. stádium",       "Húgyúti betegségek",        True),
    ("N20.0", "Vesekő",                                  "Húgyúti betegségek",        False),
    ("N39.0", "Húgyúti fertőzés",                        "Húgyúti betegségek",        False),
    ("R10.4", "Hasi fájdalom",                           "Tünetek és panaszok",       False),
    ("R51",   "Fejfájás",                                "Tünetek és panaszok",       False),
    ("S06.0", "Agyrázkódás",                             "Sérülések",                 False),
    ("S52.5", "Orsócsont alsó végének törése",           "Sérülések",                 False),
    ("S83.5", "Térdszalag-szakadás",                     "Sérülések",                 False),
    ("Z00.0", "Általános orvosi kivizsgálás",            "Egyéb",                     False),
]