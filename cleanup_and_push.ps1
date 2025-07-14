# Clean and push fresh repo to GitHub

# CONFIG
$repoUrl = "https://github.com/dcjoncas/mna-app.git"
$commitMessage = "Clean initial commit without secrets"

Write-Host ""
Write-Host "Removing .git folder if it exists..."
if (Test-Path ".git") {
    Remove-Item -Recurse -Force ".git"
    Write-Host ".git folder removed."
}
else {
    Write-Host "No .git folder found."
}

Write-Host ""
Write-Host "Initializing fresh git repo..."
git init

Write-Host "Adding all files..."
git add .

Write-Host "Committing..."
git commit -m "$commitMessage"

Write-Host "Setting branch to main..."
git branch -M main

Write-Host "Checking if remote origin exists..."
$remotes = git remote
if ($remotes -contains "origin") {
    Write-Host "Removing existing remote 'origin'..."
    git remote remove origin
}

Write-Host "Adding remote origin..."
git remote add origin $repoUrl

Write-Host "Force pushing to GitHub..."
git push -u --force origin main

Write-Host ""
Write-Host "Done. Check your GitHub repo at: $repoUrl"
