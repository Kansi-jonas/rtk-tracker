# git-update.ps1
# Automatisches Git-Update für dein RTK-Projekt

# 1. In den Projektordner wechseln
$projectPath = "C:\Users\Jobec\OneDrive\Desktop\rtk-tracker"
cd $projectPath

# 2. Git Status anzeigen
Write-Host "📄 Checking Git status..."
git status

# 3. Änderungen hinzufügen
Write-Host "➕ Staging all changes..."
git add .

# 4. Commit-Nachricht abfragen
$commitMsg = Read-Host "📝 Commit-Nachricht eingeben"
if (-not $commitMsg) {
    Write-Host "❌ Abgebrochen: Keine Commit-Nachricht eingegeben." -ForegroundColor Red
    exit
}

# 5. Commit ausführen
git commit -m $commitMsg

# 6. Push nach GitHub
Write-Host "📤 Push zu GitHub..."
git push

Write-Host "`n✅ Update abgeschlossen!" -ForegroundColor Green
