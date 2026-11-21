$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
function Step($s) { Write-Host "`n[SEOUL] $s" -ForegroundColor Cyan }
function Has($c) { return [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
}
function Install-Winget($id,$label) {
  if (-not (Has winget)) { throw "winget nao encontrado. Instale App Installer da Microsoft Store e tente novamente." }
  Step "Instalando $label pelo winget..."
  & winget install --id $id --exact --source winget --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar $label (codigo $LASTEXITCODE)." }
  Refresh-Path
}
function Python-Command {
  if (Has py) { & py -3.11 -c "import sys;exit(0 if sys.version_info >= (3,11) else 1)" 2>$null; if ($LASTEXITCODE -eq 0) { return @("py","-3.11") } }
  if (Has python) { & python -c "import sys;exit(0 if sys.version_info >= (3,11) else 1)" 2>$null; if ($LASTEXITCODE -eq 0) { return @("python") } }
  return $null
}
Step "Verificando Python 3.11+"
$python = Python-Command
if (-not $python) {
  Install-Winget "Python.Python.3.11" "Python 3.11"
  $python = Python-Command
  if (-not $python) { throw "Python instalado, mas nao detectado. Feche e abra o terminal e tente novamente." }
}
Step "Verificando Git"
if (-not (Has git)) { Install-Winget "Git.Git" "Git" }
if (-not (Has git)) { throw "Git nao encontrado apos instalacao. Reabra o terminal." }
Step "Verificando Ollama"
if (-not (Has ollama)) { Install-Winget "Ollama.Ollama" "Ollama" }
if (-not (Has ollama)) { throw "Ollama nao encontrado apos instalacao. Reabra o terminal." }
Step "Preparando ambiente Python isolado"
$venv = Join-Path $root ".venv"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
  if ($python.Count -eq 2) { & py -3.11 -m venv $venv } else { & python -m venv $venv }
  if ($LASTEXITCODE -ne 0) { throw "Falha ao criar ambiente Python." }
}
$vp = Join-Path $venv "Scripts\python.exe"
& $vp -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar pip." }
& $vp -m pip install --upgrade aider-chat
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar Aider." }
Step "Preparando configuracoes"
$settings = Join-Path $root "data\settings.json"
$example = Join-Path $root "data\settings.example.json"
if (-not (Test-Path $settings) -and (Test-Path $example)) {
  $json = Get-Content $example -Raw | ConvertFrom-Json
  $json.default_prefix = "seoul_"
  $json.aider_command = (Join-Path $venv "Scripts\aider.exe")
  $json | ConvertTo-Json -Depth 10 | Set-Content $settings -Encoding UTF8
}
Step "Verificando modelo local"
& ollama list
Write-Host "Modelo sugerido: qwen2.5-coder:7b (download de varios GB; requer memoria e espaco livre)."
$choice = Read-Host "Deseja baixar esse modelo agora? [s/N]"
if ($choice -match '^(s|sim|y|yes)$') {
  & ollama pull qwen2.5-coder:7b
  if ($LASTEXITCODE -ne 0) { Write-Warning "Download do modelo falhou. Voce pode repetir depois." }
}
Step "Instalacao concluida"
Write-Host "Use INICIAR_SEOUL.bat para abrir o Seoul IA FiveM."
