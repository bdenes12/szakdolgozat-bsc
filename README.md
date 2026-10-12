# Konfigurációvezérelt adatanonimizáció és automatizált validáció ETL folyamatokban

A szakdolgozat célja egy olyan rendszer kialakítása, amely éles adatbázisból származó adatokat továbbít fejlesztői környezetbe úgy, hogy közben automatikusan elvégzi és ellenőrzi az érzékeny adatok anonimizálását. 
A rendszer alapja egy többlépcsős (production, staging, dev) ETL folyamat. A production adatbázisból az adatok a staging rétegbe kerülnek, ahol PostgreSQL Anonymizer segítségével, szerepkör-alapú (dinamikus) maszkolás történik. A dev adatbázisba ezután már statikusan anonimizált adatok kerülnek át.

## Követelmények

- Docker
- Python 3.10+
- kitöltött `.env` (lásd alább)

## Gyors indítás

1. `docker compose up -d`
2. venv + `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py createsuperuser`
5. `python manage.py seed_policies`
6. `python .\init_scripts\seed_production.py`
7. `python manage.py runserver`
8. böngésző: `http://127.0.0.1:8000/pipelines/` (belépés: `http://127.0.0.1:8000/admin/login/`)

## Környezeti változók

- `SECRET_KEY`, `ADMIN_DB_NAME`, `ADMIN_DB_USER`, `ADMIN_DB_PASSWORD`, `ADMIN_DB_HOST`, `ADMIN_DB_PORT`, `PRODUCTION_DSN`, `STAGING_DSN`, `DEV_DSN`

## Portok

| szolgáltatás | port |
|---|---|
| Django | 8000 |
| admin Postgres | 5438 |
| prod | 5437 |
| staging (Anonymizer) | 5435 |
| dest | 5436 |

## Használat

- ETL előtt: 
    - Django administration -> POLICIES -> Masking strategies
        - A maszkolási függvények előre definiáltak ezt POLICIES -> Anon functions menüponton tudjuk megtekinteni
        - Itt létre tudunk hozni saját maszkolási stratégiát a kiválasztott maszkolási függvénnyel és, ha szükséges a megadott paraméterrel, amit később egy tábla egy oszlopán tudunk érvényesíteni
    - Django administration -> POLICIES -> Column policies
        - Itt tudjuk beállítani a kiválasztott tábla egy oszlopára a szabályunkat, meg kell adni a séma-, tábla-, oszlop nevet, a környezetet, ahol érvényesíteni szeretnénk a szabályt, az adatvédelmi kategóriát, a maszkolási stratégiát, STAGING környezet esetén a felhasználót ki kell választani, akire érvényes legyen a szabály és, hogy az alapértelmezetten végrehajtott validációs vizsgálaton felül kell-e statisztikai vagy értékátfedés vizsgálat
        - Van lehetőség a program által generálni oszlop szabályokat is az adatbázsra, ezt a GENERATE SUGGESTION gomb megnyomásával lehet 
- Főoldal:
    - ETL indítása! gomb egyszeri megnyomásával elindítjuk a folyamatot, ezzel érvénybe lépnek a környezeteken beállított szabályok
    - Amikor az ETL folyamat befejezte a futását, akkor a Futások listában megjelenik, innen tuvább tudunk lépni a validációs eredményeket összefoglaló nézetre, valamint a HTML riport nézetre

- Riport
    - Egy adott validációs futás részletes nézete, az eredmények tábla szinten csoportosítva vannak, az adott táblához hozzá van rendelve a kockázati szintje is

- Alertek:
    - Itt láthatjuk a futások során létrejövő összes alert-et, a kiválasztott alert-et a RESOLVE gomb megnyomásával megoldottra tudjuk állítani, ennek hatására eltűnik a listából

## Tesztek

`pytest -q`
A jelenlegi tesztek a tiszta logikát és a webes nézeteket fedi, adatbázis-kapcsolat nélkül.
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