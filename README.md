Ha feltölt és a táblákban van adat, a seed kész. Egy feltöltő szkriptnél a „nem szép” szinte mindig azt jelenti, hogy egy hosszú függvényben van tíz beszúrás. Ez itt elfogadható, a dolgozat nem ettől lesz jobb.

Amit később, ha van kedved, érdemes leválasztani: minden táblához egy insert_patients(cur), insert_encounters(cur, ...) függvény, és a fill_prod_database csak sorrendben hívja őket. Egy kapcsolat legyen a truncate-hez és a feltöltéshez, try/finally-ben bezárva. A véletlenmagot kapcsold vissza.

Három apróság, ami nem szépség, hanem adat:

Az invoices-nál a total_amount-ot kétszer húzod gauss-szal: a paid_amount az elsőből számolódik, a beszúrásba a második kerül. Használd ugyanazt a változót.

A diagnoses-nél for _ in encounter_ids után random.choice(encounter_ids) van, tehát nem minden ellátáshoz lesz diagnózis, néhányhoz viszont kettő. Ha 1:1-et akarsz, a ciklusváltozót tedd be encounter_id-nek.

A patient_ids a RETURNING miatt [(1,), (2,), ...] forma. Ha a címeknél/biztosításnál mégis működik, a Postgres lenyeli a tuple-t — tisztább row[0]-val kiszedni, mint a labornál.

Ezeket nem kell most újraírni. Ha a következő lépés a staging DDL vagy a 2. mérföldkő, arra válts.