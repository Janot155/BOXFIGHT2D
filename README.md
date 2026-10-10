# Box Fight 2D

Windowsová fanouškovská hra Box Fight 2D s kontrolou aktualizací přes GitHub Releases.

## První sestavení

1. Potřebuješ Windows a Python 3.10 nebo novější.
2. V této složce spusť `VYROBIT_EXE.bat`.
3. Výsledný soubor je `dist/BoxFight2D.exe`.
4. Na GitHubu otevři **Releases → Draft a new release**.
5. Tag nastav na `v1.0.0`, název na `Box Fight 2D v1.0.0`.
6. Nahraj soubor `dist/BoxFight2D.exe` jako asset a publikuj normální release (ne draft/prerelease).
7. Rozdej hráčům toto první EXE. Starší EXE bez aktualizačního mechanismu se samo aktualizovat neumí.

## Další aktualizace

1. Uprav `index.html` nebo zdrojový program.
2. V `game.py` zvyš `APP_VERSION`, například na `1.0.1`.
3. Spusť `VYROBIT_EXE.bat`.
4. Vytvoř GitHub Release s tagem `v1.0.1`, připoj nový `BoxFight2D.exe` a release publikuj.
5. Hráči, kteří už mají EXE s updaterem, po spuštění zkontrolují novou verzi a mohou kliknout na aktualizaci.

## Pro správnou funkci updateru

- `GITHUB_OWNER` je nastaven na `Janot155` a `GITHUB_REPO` na `BOXFIGHT2D` v `game.py`.
- Repozitář a vydání musí zůstat veřejné.
- Asset v každém release musí mít přesný název `BoxFight2D.exe`.
- Tagy/verze mají růst: `v1.0.0`, `v1.0.1`, `v1.0.2`...
- Při sestavení se používá Windows; v jiném systému tento `.bat` nespustíš.
- Doporučené umístění EXE je složka uživatele, do které lze zapisovat, například na Ploše. `Program Files` může vyžadovat práva správce.

## Upozornění

Automatické aktualizace jsou jednoduché a stahují EXE z veřejného GitHub Release. Před zveřejněním otestuj každou novou verzi a chraň svůj GitHub účet. Tento zdrojový repozitář neobsahuje hotové EXE; sestav ho na Windows a vlož do Release.
