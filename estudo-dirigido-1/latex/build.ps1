$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

$tex = "main.tex"
if (-not (Test-Path $tex)) { throw "Arquivo nao encontrado: $tex" }

function Get-TeXBinDirs {
    $dirs = [System.Collections.Generic.List[string]]::new()

    # MiKTeX (instalacao por usuario ou por maquina)
    foreach ($root in @(
            "$env:ProgramFiles\MiKTeX\miktex\bin\x64",
            "$env:ProgramFiles\MiKTeX\miktex\bin",
            "${env:ProgramFiles(x86)}\MiKTeX\miktex\bin\x64",
            "${env:ProgramFiles(x86)}\MiKTeX\miktex\bin",
            "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64",
            "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin"
        )) {
        if ($root) { [void]$dirs.Add($root) }
    }

    # TeX Live (ano da pasta varia)
    $texliveRoot = "C:\texlive"
    if (Test-Path $texliveRoot) {
        Get-ChildItem -Path $texliveRoot -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            ForEach-Object {
                $win32 = Join-Path $_.FullName "bin\win32"
                if (Test-Path $win32) { [void]$dirs.Add($win32) }
            }
    }

    return $dirs
}

function Find-PdfLatexPath {
    $cmd = Get-Command pdflatex -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }

    foreach ($dir in Get-TeXBinDirs) {
        $candidate = Join-Path $dir "pdflatex.exe"
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Find-BibtexPath {
    $cmd = Get-Command bibtex -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }

    foreach ($dir in Get-TeXBinDirs) {
        $candidate = Join-Path $dir "bibtex.exe"
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

$pdflatexPath = Find-PdfLatexPath
if (-not $pdflatexPath) {
    $msg = @"
pdflatex nao foi encontrado no PATH nem nos caminhos comuns (MiKTeX / TeX Live).

O que fazer no Windows:
1) Instale uma distribuicao LaTeX (escolha uma):
   - MiKTeX: https://miktex.org/download
   - TeX Live: https://www.tug.org/texlive/windows.html
2) Durante/apos a instalacao, marque a opcao de atualizar o PATH (variavel de ambiente),
   OU adicione manualmente a pasta ...\miktex\bin\x64 (ou texlive\...\bin\win32) ao PATH do usuario.
3) Feche e reabra o terminal (e o Cursor), depois rode de novo:
   powershell -ExecutionPolicy Bypass -File .\build.ps1

Dica: no PowerShell, teste:  Get-Command pdflatex
"@
    throw $msg
}

$bibtexPath = Find-BibtexPath

function Invoke-PdfLatex([string]$job) {
    & $pdflatexPath -interaction=nonstopmode -halt-on-error $job | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "pdflatex falhou ($LASTEXITCODE)." }
}

Write-Host "Usando: $pdflatexPath"
Invoke-PdfLatex $tex
if ($bibtexPath) {
    Write-Host "Usando: $bibtexPath"
    Push-Location $here
    try {
        $jobname = [System.IO.Path]::GetFileNameWithoutExtension($tex)
        & $bibtexPath $jobname | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "bibtex falhou ($LASTEXITCODE)." }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "AVISO: bibtex nao encontrado; referencias podem ficar incompletas."
}
Invoke-PdfLatex $tex
Invoke-PdfLatex $tex

$out = Join-Path $here "main.pdf"
$dest = Join-Path (Split-Path $here -Parent) "relatorio.pdf"
if (Test-Path $out) {
    Copy-Item -Force $out $dest
    Write-Host "OK: copiado para $dest"
}
else {
    throw "PDF nao gerado: $out"
}
