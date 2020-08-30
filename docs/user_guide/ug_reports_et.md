
| [![Riigi Infosüsteemi Amet](../img/ria_100_et.png)](https://www.ria.ee/et.html) [![X-TEE](../img/xroad_100_et.png)](https://www.ria.ee/et/riigi-infosusteem/andmevahetuskiht-x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_et.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-tee v6 monitooring - raportite lugemisjuhend

## Üldist

Raportid on mõeldud eelkõige isikutele, kes on märgitud [RIHAs](https://www.riha.ee/) vastava alamsüsteemi kontaktisikuteks (infosüsteemi ülematele).

Raportid võiksid anda neile ülevaate, mis üldse toimub X-teel Teie vastavas alamsüsteemis: 
- kes ja kui palju seda kasutab (**Osutatud teenused**) ning 
- kas ja kui palju Teie alamsüsteemist päringuid teistesse alamsüsteemidesse välja läheb (**Kasutatud teenused**). 

Mõlemad neist osadest on veel omakorda jagatud kaheks, eraldi nn „päris-teenused“ (**äriteenused**) ja X-tee **[metateenused](#mis-on-metateenused)**. 
Kõigis neljas tabelis on toodud päringute kaupa (Teenus) nende kasutajad (Klient/Osutaja), õnnestunud ja ebaõnnestunud päringute arvud, samuti õnnestunud päringute kestused (millisekundites) ning päringute ja vastuste suurused (baitides).

Usume, et raportitest on kasu ka oma klientidest või andmevahetuspartneritest parema ülevaate saamisel.
Raportid võiksid oma andmetes anda ülevaate enim kasutatud, kõige vigasemate, kõige kauem kestvate või kõige kiiremate, samuti kõige mahukamate päringute kohta ning olla abiks teenuste paremal disainimisel ning kasutamisel, mahuhinnangutes.

Alltoodud näidisraporti puhul näiteks on võimalik näha, et ühtede süsteemidega andmevahetus toimib (õnnestunud päringud: 687), teistega mitte (ebaõnnestunud päringud: 984, kestused ja suurused `None`).
Samuti, et sama päringu (getSecurityServerOperationalData) puhul ühelt süsteemilt saabuvad andmed keskmiselt 0,292 sekundiga, teiselt aga keskmiselt 2,039 sekundiga, st ligikaudu 7 korda aeglasemalt.

![Näidisraport](1_report_sample.png "Näidisraport")

Igal raportil on unikaalne nimeosa (koostamise hetk mikrosekundi, st miljondiku täpsusega) ja avaldamiskeskkonnas olevate raporti kohta saadetakse e-postiga vaid viide.
Avaldamiskeskkonnas on kaustapuude kaudu kõigi seal asuvate raportite vaatamine piiratud. Kokkuvõttes võiksid need enam-vähem tagada, et: 
-	iga kontaktisik näeb just talle saadetud raportit;
-	mitte keegi ei näe teistele isikutele saadetud raporteid (ühe alamsüsteemi raport selle alamsüsteemi kontaktidele on muidugi seesama);
-	asutuse uus kontaktisik ei näe vanu raporteid ilma, et kas eelmine (või olemasolev) kontakt talle neid viiteid jagaks;
-	asutusest lahkunud kontaktisik ei saa enam teavitust uute koostatud raportite kohta.

Raportid koostatakse nii arendus- (ee-dev), test- (ee-test) kui toodangukeskkonna (EE) kohta iga kalendrikuu 8-10. kuupäeval.

Juhul kui on soovitusi raporti sisu, vormi jms osas, palun lahkesti teada anda, püüame RIA poolt kaasa aidata parema selguse ja läbipaistvuse loomisele selles, mis X-tee peal tegelikult toimub. Palun andke märku aadressil help@ria.ee kõikides seotud küsimustes.

Riigi Infosüsteemi Amet avaldab üldistatud kujul X-tee kasutusstatistikat ka avaandmetena ja visualiseeritud kujul:
- toodangukeskkonna (EE) kohta aadressitel https://logs.x-tee.ee/EE/gui ja https://logs.x-tee.ee/visualizer/EE
- testkeskkonna (ee-test) kohta aadressitel https://logs.x-tee.ee/ee-dev/gui ja https://logs.x-tee.ee/visualizer/ee-test ning
- arenduskeskkonna (ee-dev) kohta aadressitel https://logs.x-tee.ee/ee-dev/gui ja https://logs.x-tee.ee/visualizer/ee-dev

Üldistatud kujud ei sisalda X-tee päringutega seotud juurdepääsupiiranguga teavet. 
Juhul, kui Teie hinnangul esineb mõnede statistiliste andmete osas asutusesiseseks kasutamiseks tunnistatud teabe avalikustamise oht, palume sellest koheselt Riigi Infosüsteemi Ametit informeerida viidates seaduses sätestatud juurdepääsupiirangu alusele.

## Korduma Kippuvad Küsimused

### Miks just MINA selle raporti sain?

Sest just Teie olete selle X-tee alamsüsteemi kontakt [RIHA](https://www.riha.ee/) andmetel. 
Palun veenduge RIHA andmete ajakohasuses (vajalik eelnev autentimine).

### Kas raportite saamise võib ka "maha võtta"? Kuidas?

Hetkel meil raportite väljasaatmise süsteemile nn "opt-out" nimekirja pole. Raportid saadetakse kõigile selle X-tee alamsüsteemi RIHAs märgitud kontaktisikutele.

Palun selgitust, miks soovite teavitustest loobuda?

- Kui Te ei ole nimetatud alamsüsteemiga enam seotud, siis lihtsaim lahendus on enda kontakti eemaldamine RIHAst;
- kui te olete küll seotud kuid ei soovi neid kirju, siis üks võimalus on ka oma e-kirjade postkastis vastav suunav filter moodustada;
- kui te olete seotud aga tahaksite näha ülevaateid mingil teisel kujul, siis ootame tagasidet, milline see parem ja sobivam vorm võiks olla;
- kui te lihtsalt ei vaja niisugust lisainfot raportite näol, siis püüame juurutada ka "opt-out" nimekirja võimaluse.

### Miks just TEMA selle raporti sai?

Sest just tema on selle X-tee alamsüsteemi kontaktisik [RIHA](https://www.riha.ee/) andmetel. 
Palun veenduge RIHA andmete ajakohasuses (vajalik eelnev autentimine).

### Miks ei ole raportit sellel viitel?

**Küsimus: Sain (eelmise kontaktisiku käest) viite raportile aga seal ei ole seda enam! Kuhu kadus?**

Kustutame süsteemist vanemad raportid kui aasta. Soovitame säilitada varem saadetud raportid Teie dokumendisüsteemis.
Juhul kui siiski on vaja raportit uuesti, siis palun pöörduge sellekohase palvega help@ria.ee.
Kindlasti atab kaasa ka see kui viitate, millisest raportist täpsemalt huvitatud olete.

### Kas ma võin mulle saadetud raporti edasi saata?

Jah, loomulikult! 
Need on andmed Teie X-tee alamsüsteemi kohta ja just Teie teate ise, kellele ja miks neid vaja võib olla.

### Ma sain raporti X-tee arenduskeskkonna (ee-dev) / testkeskkonna (ee-test) kohta. Miks ma ei saanud raportit toodangukeskkonna (EE) kohta?

Küll ta tuleb!

X-tee keskkonnad on erineva mahuga, arendus- ja testkeskkonna raportid koostatakse üldjuhul iga kuu 8.kpv öösel / varahommikul.
Toodangukeskkond on oluliselt mahukam päringute arvu poolest, raportite koostamine võtab kauem aega ja valmivad üldjuhul iga kuu 5.kpv öösel / varahommikul.
Põhjust üleküsimiseks on alles siis kui kuu 8.kpv jooksul ei ole raportit Teieni jõudnud.

### Liiga palju raporteid!

**Küsimus: Mõni meie inimene, kes rohkemate teenuste juures kontaktiks, sai neid kümnetega. Kas saaks teha ka miski koondi, kus kõik koos – st üks teavitus ja kõik raportid ühes kohas?**

Raporteid koostatakse ja saadetakse iga X-tee keskkonna iga alamsüsteemi kontaktile täpselt üks.
Raportite genereerimise loogika muutmine nii, et koostatavate raportite nimekiri tehakse kontaktisikute kaupa vajab hoopis teistsugust lähenemist ja ei ole hetke raamistikus võimalik.

Soovitame üle vaadata RIHAs iga alamsüsteemi kontaktisikud ning otsustada, kas on vajalik just selline jaotus alamsüsteemideks ja/või kas on vajalik, et üks isik on kõigi alamsüsteemide kontaktiks.

### Raportis on valed andmed!

**Küsimus: Raportist selgub, et teenust T on tarbitud X korda. Meie andmetel aga peaks päringute arv olema oluliselt suurem. Miks need ei kajastu raportis?**

Raportite koostamise aluseks on X-tee keskusele (RIA) kättesaadavad andmed liikmete X-tee turvaserveritest. Juhul kui ühel või teisel põhjusel ei ole Teie turvaserver kättesaadav, siis koostatakse Teie raporti andmed Teie andmevahetuspartnerite X-tee turvaserveritest pärineva põhjal. On võimalik, et ka osa nendest ei ole olnud kättesaadavad.

Võimalikud põhjused, miks X-tee keskus ei saa andmed mõne X-tee liikme turvaserveri(te)st on toodud osas [Tehnilist](#tehnilist).

### Mis on kestus, kuidas seda arvutatakse?

Kestus [\[EKSS\] "Eesti keele seletav sõnaraamat"](http://www.eki.ee/dict/ekss/index.cgi?Q=kestus) põhjal: "millegi ajaline kestmine; selle ajaline pikkus, vältus".

Päringute kestused fikseeritakse ja kajastatakse raportis kliendi poolelt vaadatuna, st leitakse aeg turvaserveri poolt infosüsteemile / lõppkasutajale tagastatud vastuse hetke ning infosüsteemi / lõppkasutaja poolt tehtud päringu hetke vahena (Client ResponseOutTs - Client RequestInTs).
Kestus on esitatud millisekundites.
Juhul kui andmeid Teie turvaserveris pole / ei saa, siis ei saa me neid ka raportis kajastada (on kajastatud kui `None`)

Lisatud ülevaatlik pilt, mis hetkede kellaajad eri andmevahetuspartnerite turvaserverites fikseeritakse ja mida arvutusteks kasutame.

![Timestamps](0_timestamps.png "Timestamps")

**Päringu kestus kliendi (lõppkasutaja) vaates**

X-tee päringu kestus kliendi (lõppkasutaja) vaates arvutatakse X-tee kliendi rollis oleva liikme alamsüsteemi teenindavas turvaserveris fikseeritud kliendi turvaserverist kliendi infosüsteemile vastuse saatmise aja (8) ning kliendi infosüsteemi poolt algatatud päringu kliendi turvaserverisse jõudmise aja (1) vahena.

```
totalDuration = Client responseOutTs (8) - Client requestInTs (1)
```

**Päringu kestus teenusepakkuja vaates**

X-tee päringu kestus teenusepakkuja turvaserveri vaates arvutatakse X-tee teenusepakkuja rollis oleva liikme alamsüsteemi teenindavas turvaserveris fikseeritud teenusepakkuja turvaserverist kliendi turvaserverisse vastuse saatmise aja (6) ning kliendi turvaserverist teenusepakkuja turvaserverisse saadetud päringu kohale jõudmise aja (3) vahena.

```
producerDurationProducerView = Producer responseOutTs (6) - Producer requestInTs (3)
```

### Meie raport ei näita päringute kestusi! Miks?

Raportite koostamise aluseks on X-tee keskusele (RIA) kättesaadavad andmed liikmete X-tee turvaserveritest. Juhul kui ühel või teisel põhjusel ei ole Teie turvaserver kättesaadav, siis koostatakse Teie raporti andmed Teie andmevahetuspartnerite X-tee turvaserveritest pärineva põhjal.

Kui andmeid Teie turvaserveris pole / ei saa, siis ei saa me kestusi ka raportis kajastada (on kajastatud kui `None`).

Võimalikud põhjused, miks X-tee keskus ei saa andmed mõne X-tee liikme turvaserveri(te)st on toodud osas [Tehnilist](#tehnilist).

### Kas saab paremat raportit?

**Küsimus: Saadud raport top 5 teenuse kohta jääb mõne süsteemi osas ikka tiba väheseks, pigem võiks terviklik statistikaraport olla. Kas ja kust ja millal saab?**

Tõsi, ühte raportisse on keeruline mahutada kogu X-teel toimuvat. Palun täpsustage oma soovi terviklikkuse osas. Oleme valmis koostama põhjendatud soovi korral kas muutma või juurde lisama raportite malle, valmistama neid mingil teisel, just Teile sobivaimal kujul. 

**Küsimus: Saadetud raportist pole kuigi suurt abi, et selle baasil midagi hinnata saaks. Kui üldse, siis peaks olema monitooringusüsteemile loodud konto ligipääs, mis võimaldaks seal ise teha vajaduse põhiseid analüütilisi päringuid nn enda IS teenuste osas nii ajalises kui kasutuse mõttes.**

Eraldi liikmetele mõeldud ja kontohaldusega monitooringusüsteemi (*data warehouse*) RIA-l plaanis avada pole.

Raporti koostamise aluseks olev andmestik on kättesaadav ka Teie X-tee turvaserverist ning Teie andmevahetuspartneri turvaserveri(te)st. Heameelega nõustame, mil viisil saate seda ise koondada ning ise koostada endale vajalik raport.

Raporti koostamise aluseks olev andmestik on üldjoontes kättesaadav ka avaandmetena:
- Toodangukeskkonna `EE` avaandmed on avaldatud aadressil https://logs.x-tee.ee/EE/gui/, 
- testkeskkonna `ee-test`omad aadressil https://logs.x-tee.ee/ee-test/gui/ ja 
- arenduskeskkonna `ee-dev` omad aadressil https://logs.x-tee.ee/ee-dev/gui/. 

### Mis on metateenused?

Metateenusteks nimetame teenuseid (äri)teenuste kohta. Need on abiteenused, mille abil on võimalik pärida infot andmeteenuste sooritamiseks. 
Ka X-tee raportite alusandmete, samuti erinevate nimekirjade, kataloogide, statistika ja ülevaadete jaoks kasutatakse metateenuseid, 
peamiselt päringud `listMethods`, `getWsdl` ja `getOpenAPI`.

Täpsemalt on metateenuseid kirjeldatud [X-Road: Service Metadata Protocol](https://www.x-tee.ee/docs/live/xroad/pr-meta_x-road_service_metadata_protocol.html) ja 
[X-Road: Service Metadata Protocol for REST](https://www.x-tee.ee/docs/live/xroad/pr-mrest_x-road_service_metadata_protocol_for_rest.html)

Raportite kontekstis loeme metateenusteks ka X-tee keskkonnamonitooringu kasutatava päringu `getSecurityServerMetrics` ning teenuste monitooringu kasutatavad päringud `getSecurityServerOperationalData`, `getSecurityServerHealthData`.

### Kuidas Te seda infot kogute? 

Andmete saamiseks turvaserveritest kasutame X-tee teenuste monitooringut, selle dokumentatsioon on leitav Githubist, https://github.com/nordic-institute/X-Road/tree/develop/doc/OperationalMonitoring.
Spetsiifilisemalt kasutame selleks kasutusstatistika andmed turvaserverist, päring `getSecurityServerOperationalData`. 
Päringu näidiseid ja valik võimalikke skripte on toodud ka Githubi süsteemitestide kaustas https://github.com/nordic-institute/X-Road/tree/develop/src/systemtest/op-monitoring

Kogu andmestik on kogutud ilma päringute sisu privaatsust puudutamata.

### Kas X-tee päringud käivad ikka veel läbi keskserverite?

Läbi RIA keskserveri ei käi mitte mingit X-tee tegelikku liiklust, ei ole kunagi käinud ja ei hakka ka tulevikus käima. X-tee võimaldab turvalist ja hajutatud andmevahetust teenuse kasutaja ja teenuse osutaja vahel, puudub keskne koht.

### Mis monitooringu vahendiga üldse tegu on?

Pikem ja põhjalikum kirjeldus koos paigaldusjuhendite ja lähtekoodiga on avaldatud Githubi repositooriumis https://github.com/ria-ee/X-Road-opmonitor

Tööd telliti riigihanke RHR 183990 alusel, teostaja [Tarkvara Tehnoloogia Arenduskeskus OÜ (STACC)](https://www.stacc.ee/). 
Tõenäoliselt saab ka nendelt abi juhul kui otsustate teha just Teile sobiva süsteemi.

## Tehnilist

Monitooringuandmete saamiseks Teie X-tee v6 turvaserverist palun veenduge, et:
- kasutusel on uusim versioon https://x-tee.ee/packages/, arendus- ja testkeskkond https://x-tee.ee/packages/test/
- Teie asutuse tulemüür lubab X-tee päringuid RIA monitooringusüsteemist EE IP 195.80.123.159 (ee-dev IP 195.80.123.169, ee-test IP 195.80.123.164), pordid 5500 ja 5577.

Tagamaks turvaserveri tarkvara pakettide korrektset paigaldumist, palume v6 turvaserveri uuendusi paigaldada alati käsuga (vaata ka https://www.x-tee.ee/docs/live/xroad/ig-ss_x-road_v6_security_server_installation_guide.html#45-different-versions-of-xroad--packages-after-successful-upgrade)

```
apt-get update
apt-get dist-upgrade
```

Pärast uuendust veenduge, et teenuste monitooringu pakid on paigaldatud.

```
sudo dpkg -l | egrep "xroad|xtee" | sort
```

Kui tarkvara pakk on korralikult paigaldatud, siis on mooduli nimetuse ees `ii`.

Kui on vigaselt, siis kas `iU` või `iF` vms (vaata ka https://askubuntu.com/questions/18804/what-do-the-various-dpkg-flags-like-ii-rc-mean).

Vastuses **peavad** sisalduma vaid märksõna `xroad` sisaldavad pakid. 

Vastuses **ei tohi** sisalduda märksõna `xtee` sisaldavaid pakke.

```
ii xroad-addon-hwtokens <versioon> all X-Road AddOn: hwtokens
ii xroad-addon-messagelog <versioon> all X-Road AddOn: messagelog
ii xroad-addon-metaservices <versioon> all X-Road AddOn: metaservices
ii xroad-addon-opmonitoring <versioon> all X-Road AddOn: operations monitoring service
ii xroad-addon-proxymonitor <versioon> all X-Road AddOn: proxy monitoring metaservice
ii xroad-addon-wsdlvalidator <versioon> all X-Road AddOn: wsdlvalidator
ii xroad-common <versioon> amd64 X-Road shared components
ii xroad-jetty9 <versioon> all Jetty9 for X-Road purposes
ii xroad-monitor <versioon> all X-Road monitoring service
ii xroad-opmonitor <versioon> all X-Road operations monitoring daemon
ii xroad-proxy <versioon> all X-Road security server
ii xroad-securityserver <versioon> all X-Road security server
```

X-tee turvaserverite administraatorite korduma kippuvad küsimused (KKK) ja vastused neile - https://moodle.ria.ee/mod/page/view.php?id=419

