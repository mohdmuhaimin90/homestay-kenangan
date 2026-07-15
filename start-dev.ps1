$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
Set-Location "C:\Users\mohdm\OneDrive\Documents\New OpenCode Project"
npm run dev
