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
```

## DVC Nextcloud Share

Zuerst sollte für den Ordner `DVC_Repo` ein Share Link mit einem Passwort
erstellt werden. Das Ablaufdatum sollte weit genug in der Zukunft liegen.
Es muss auch ein Passwort gesetzt werden und die Berechtigungen müssen auf
"Hochladen und Bearbeiten erlauben" gesetzt werden.

Man sollte jetzt folgendes haben:

```text
Link: https://cloud.h-da.de/s/zPfHbGGTx7A7MgB
Password: 78HJDWUB435345
```

Der Teil nach `/s/` ist die Share ID, die man als Benutzernamen nutzt für
den Zugriff über WebDAV (Erfordert `dvc-webdav`).

```bash
DVC_SHARE_ID="zPfHbGGTx7A7MgB"
# -d make default remote, otherwise: dvc pull -r cloud_remote
# --local write to a git ignored file, so that it stays private
dvc remote add cloud_remote --local "https://cloud.h-da.de/remote.php/webdav/"
dvc remote modify cloud_remote --local user "$DVC_SHARE_ID"
 dvc remote modify cloud_remote --local password "78HJDWUB435345"
```

## DVC Nutzung

```bash
# Restore the last results from the DVC remote (uses results.dvc reference)
dvc pull
dvc checkout

# See current status of the DVC tracked files
dvc status

# Old versions can be found by rolling back the results.dvc file with git
# and then running dvc checkout again.

# Add a new version
dvc add results
git add results.dvc # and every other file that changed
git commit -m "Changes here."
dvc push # Pushes the new version to the remote
git push # Pushes the new version of results.dvc to the remote
```
