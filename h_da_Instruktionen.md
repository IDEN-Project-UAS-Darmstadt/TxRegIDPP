# Instruktionen zur Ausführung an der h_da

Dieses Repo enthält den Code zur Vorverarbeitung der Registerdaten.

1. Platziere die `.csv`-Dateien des Exports vom Register in `resources/input`.
2. Öffnen des Repos als Development Container in VS Code.
3. Warten bis das Setup Skript nach Starten des Containers abgeschlossen ist.

Je nachdem, wo der Devcontainer ausgeführt wird, kann es sein, dass die
Rechte des Projekt Ordners nicht der ausführende Benutzer, sondern
`root` mit 777 Rechten sind. Damit ist DVC nicht ausführbar. In diesem
Fall sollte DVC außerhalb des Containers ausgeführt werden.

Um die letzten Ergebnisse zu laden oder diese mit neuen zu ersetzen, muss
das DVC remote Repository konfiguriert werden. Dies erfolgt enweder
über einen lokalen Ordner, der mit der Nextcloud synchronisiert wird,
oder direkt über eine Nextcloud Share mit einem Passwort.

## DVC Lokaler Ordner

Hierfür wird lokaler Pfad zum DVC Repo benötigt. Bei mir z. B.:
`/mnt/d/h_da\ Nextcloud/FBI\ Forschungsprojekt\ IDEN/DVC_Repo/`.
Dieses enthält einen Ordner mit dem Namen `files`.

Dieser kann jetzt als remote zu DVC hinzugefügt werden:

```bash
PATH_TO_DVC_REPO="/mnt/d/h_da\ Nextcloud/FBI\ Forschungsprojekt\ IDEN/DVC_Repo/"
# -d make default remote, otherwise: dvc pull -r local_remote
# --local write to a git ignored file, so that it stays private
dvc remote add -d local_remote --local "$PATH_TO_DVC_REPO"

# Restore the last results from the DVC remote (uses results.dvc reference)
dvc pull
dvc checkout

# Old versions can be found by rolling back the results.dvc file with git
# and then running dvc pull again.
```