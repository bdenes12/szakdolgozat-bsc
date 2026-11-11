# Konfigurációvezérelt adatanonimizáció és automatizált validáció ETL folyamatokban

A szakdolgozat célja egy olyan rendszer kialakítása, amely éles adatbázisból származó adatokat továbbít fejlesztői környezetbe úgy, hogy közben automatikusan elvégzi és ellenőrzi az érzékeny adatok anonimizálását. 
A rendszer alapja egy többlépcsős (production, staging, dev) ETL folyamat. A production adatbázisból az adatok a staging rétegbe kerülnek, ahol PostgreSQL Anonymizer segítségével, szerepkör-alapú maszkolás történik. Staging környezeten két út van. Az egyik, hogy support felhasználóként a public séma tábláit olvassuk dinamikus maszkolással, A másik út az, hogy analytics felhasználóként az analytics séma materializált nézeteit olvassuk, amik statikusan vannak maszkolva. A dev adatbázisba ezután már statikusan anonimizált adatok kerülnek át.

## Követelmények

- Docker
- Python 3.10+
- kitöltött `.env` (lásd alább)

## Gyors indítás

0. másold a `.env.example`-t `.env`-be és töltsd ki
1. `docker compose up -d --build`
2. `docker compose exec web python manage.py createsuperuser`
3. `docker compose exec web python manage.py seed_policies --scenario alap`
    A `--scenario` lehetséges értékei:
    | Szcenárió | Mit mutat be |
    |---|---|
    | `alap` (default) | vegyes állapot: MAGAS, KÖZEPES és ALACSONY kockázatú táblák |
    | `hibatlan` | a patients és invoices tábla teljesen lefedve, ezeknél kockázat NINCS |
    | `szivargas` | maszkolatlan közvetlen azonosítók, MAGAS kockázatú táblák |
    | `szigoru_stat` | szigorú statisztikai küszöbök, KÖZEPES kockázatú táblák |
    | `hianyos` | nincs szabály, csak MISSING_POLICY riasztások jönnek létre |
    | `staging` | az `alap` kiegészítve SUPPORT és ANALYTICS szerepkörös STAGING szabályokkal |
    | `analytics` | dev és analytics k-anonimitás bemutatása, általánosított materialized view-k az elemző számára |
4. `docker compose exec web python init_scripts/seed_production.py --patients 500`
(Mérés: `powershell -Command "Measure-Command { docker compose exec web python init_scripts/seed_production.py --patients 5000 | Out-Default }"`)
5. böngésző: `http://127.0.0.1:8000/pipelines/` (belépés: `http://127.0.0.1:8000/admin/login/`)

A `migrate` a `web` konténer indulásakor lefut; a demóhoz nem kell hostos `runserver`.

**Leállítás:** `docker compose down` megőrzi az adatokat. Tiszta 0-ról indítás (üres sémák): `docker compose down -v`, majd újra az 1–5. lépés.

**Hálózat:** a négy adatbázis külön Docker-hálózaton van (csillag topológia), egymást nem érik el. Az ETL-t a mind a négy hálózatra kapcsolt `web` végzi. A host a táblázatban lévő portokon továbbra is csatlakozhat a DB-khez.

## Környezeti változók

- `SECRET_KEY`, `ADMIN_DB_NAME`, `ADMIN_DB_USER`, `ADMIN_DB_PASSWORD`, `ADMIN_DB_HOST`, `ADMIN_DB_PORT`, `PRODUCTION_DSN`, `STAGING_DSN`, `DEV_DSN`, `STAGING_ANALYST_DSN`

## Portok

| szolgáltatás | port |
|---|---|
| Django | 8000 |
| admin Postgres | 5438 |
| prod | 5437 |
| staging (Anonymizer) | 5435 |
| dev | 5436 |

## Használat

- ETL előtt: 
    - Django administration -> POLICIES -> Masking strategies
        - A maszkolási függvények előre definiáltak ezt POLICIES -> Anon functions menüponton tudjuk megtekinteni
        - Itt létre tudunk hozni saját maszkolási stratégiát a kiválasztott maszkolási függvénnyel és, ha szükséges a megadott paraméterrel, amit később egy tábla egy oszlopán tudunk érvényesíteni
    - Django administration -> POLICIES -> Column policies
        - Itt tudjuk beállítani a kiválasztott tábla egy oszlopára a szabályunkat, meg kell adni a séma-, tábla-, oszlop nevet, a környezetet, ahol érvényesíteni szeretnénk a szabályt, az adatvédelmi kategóriát, a maszkolási stratégiát, STAGING környezet esetén a felhasználót ki kell választani, akire érvényes legyen a szabály és, hogy az alapértelmezetten végrehajtott validációs vizsgálaton felül kell-e statisztikai vagy értékátfedés vizsgálat
        - STAGING + SUPPORT: dinamikus maszk a `public` sémán; STAGING + ANALYTICS: materialized view az `analytics` sémában (`public`-ot az analyst nem olvashatja)
        - K-anonimitás csak DEVELOPMENT-en, vagy STAGING + ANALYTICS-en, `generalize_*` kezdetű anonimizáló függvények csak STAGING + ANALYTICS beállítással érvényes
        - A beállított séma/tábla/oszlopnak léteznie kell a production adatbázisban
        - Van lehetőség a program által generálni oszlop szabályokat is az adatbázisra, ezt a GENERATE SUGGESTION gomb megnyomásával lehet

- Főoldal:
    - ETL indítása! gomb egyszeri megnyomásával elindítjuk a folyamatot, ezzel érvénybe lépnek a környezeteken beállított szabályok
    - Amikor az ETL folyamat befejezte a futását, akkor a Futások listában megjelenik, innen tovább tudunk lépni a validációs eredményeket összefoglaló nézetre, valamint a HTML riport nézetre

- Riport
    - Egy adott validációs futás részletes nézete, az eredmények tábla szinten csoportosítva vannak, az adott táblához hozzá van rendelve a kockázati szintje is

- Alertek:
    - Itt láthatjuk a futások során létrejövő összes alert-et, a kiválasztott alert-et a RESOLVE gomb megnyomásával megoldottra tudjuk állítani, ennek hatására eltűnik a listából

## Tesztek

`docker compose exec web pytest -q`
A jelenlegi tesztek a tiszta logikát és a webes nézeteket fedik, adatbázis-kapcsolat nélkül.
DSN/ETL nincs a pytestben.

## Projektstruktúra 

- `config/` — Django beállítások
- `policies/` — ColumnPolicy, javaslatgenerálás, AnonFunction / stratégia
- `anonymization/` — staging címkék és dev nézetek (PostgreSQL Anonymizer)
- `pipelines/` — ETL indítás, dashboard, futás detail, riport URL
- `validations/` — checkek, ValidationRun / Result, HTML riport
- `alerts/` — riasztások és resolve
- `sql/` — prod és staging séma
- `init_scripts/` — production tesztadat feltöltése
- `templates/` — közös HTML / CSS (navbar, `app.css`)