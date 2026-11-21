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
function Test-Python($exe, $argsPrefix) {
  if (-not $exe) { return $false }
  try {
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & $exe @argsPrefix -c "import sys; print('SEOUL_PY_OK' if sys.version_info >= (3,11) else 'SEOUL_PY_OLD')" 2>$null
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $oldPreference
    return ($exitCode -eq 0 -and ($output -join "") -match 'SEOUL_PY_OK')
  } catch {
    $ErrorActionPreference = "Stop"
    return $false
  }
}
function Python-Command {
  if (Has py) {
    if (Test-Python "py" @("-3.11")) { return ,@("py","-3.11") }
    if (Test-Python "py" @("-3")) { return ,@("py","-3") }
  }
  if (Has python) {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command.Source -notlike '*WindowsApps*' -and (Test-Python "python" @())) {
      return ,@("python")
    }
  }
  $locations = @(
    (Join-Path $env:LOCALAPPDATA "Programs\\Python\\Python311\\python.exe"),
    (Join-Path $env:ProgramFiles "Python311\\python.exe")
  )
  foreach ($location in $locations) {
    if ((Test-Path $location) -and (Test-Python $location @())) { return ,@($location) }
  }
  return $null
}
Step "Verificando Python 3.11+"
$python = Python-Command
if (-not $python) {
  Install-Winget "Python.Python.3.11" "Python 3.11"
  $python = Python-Command
  if (-not $python) { throw "Python instalado, mas nao detectado nesta sessao. Feche o terminal e execute o instalador novamente. Se necessario, desative os aliases python.exe/python3.exe da Microsoft Store em Configuracoes > Aplicativos > Aliases de execucao do aplicativo." }
}
Step "Verificando Git"
if (-not (Has git)) { Install-Winget "Git.Git" "Git" }
if (-not (Has git)) { throw "Git nao encontrado apos instalacao. Reabra o terminal." }
Step "Ollama opcional para modo local"
if (-not (Has ollama)) {
  $localChoice = Read-Host "Instalar Ollama para IA local? [s/N]"
  if ($localChoice -match '^(s|sim|y|yes)$') { Install-Winget "Ollama.Ollama" "Ollama" }
}
Step "Preparando ambiente Python isolado"
$venv = Join-Path $root ".venv"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
  if ($python.Count -eq 2) { & $python[0] $python[1] -m venv $venv } else { & $python[0] -m venv $venv }
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
  $jsonText = $json | ConvertTo-Json -Depth 10
  [System.IO.File]::WriteAllText($settings, $jsonText, (New-Object System.Text.UTF8Encoding($false)))
}
if (Has ollama) {
  Step "Verificando modelo local"
  & ollama list
  Write-Host "Modelo sugerido: qwen2.5-coder:7b (download de varios GB)."
  $choice = Read-Host "Deseja baixar esse modelo agora? [s/N]"
  if ($choice -match '^(s|sim|y|yes)$') {
    & ollama pull qwen2.5-coder:7b
    if ($LASTEXITCODE -ne 0) { Write-Warning "Download do modelo falhou. Voce pode repetir depois." }
  }
}
Step "Instalacao concluida"
Write-Host "Use ABRIR_PAINEL_SEOUL.bat para o painel web ou INICIAR_SEOUL.bat para o menu original."
