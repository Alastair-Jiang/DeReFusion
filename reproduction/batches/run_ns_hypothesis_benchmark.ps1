param(
    [Parameter(Mandatory = $true)]
    [string]$Manifest,
    [switch]$Execute
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$python = ".venv\Scripts\python.exe"
$arguments = @("reproduction/analysis/run_ns_hypothesis_benchmark.py", "--manifest", $Manifest)
if ($Execute) {
    $arguments += "--execute"
}

& $python @arguments
exit $LASTEXITCODE
