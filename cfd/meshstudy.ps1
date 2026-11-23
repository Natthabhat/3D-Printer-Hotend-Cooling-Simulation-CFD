# Images for the reconciled cases, then the D2 mesh study (coarse + fine). Fluent Student allows one session,
# so the solver window is closed for meshing and reopened for solving.
$ErrorActionPreference = "Continue"
$cfd = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $cfd
$env:PYTHONIOENCODING = "utf-8"

function Close-Fluent {
    python -c "from fl import connect; s=connect(); s.exit()" 2>$null | Out-Null
    Get-Process fl_mpi2610, cx2610, fluent -ErrorAction SilentlyContinue | Stop-Process -Force -Confirm:$false
    Start-Sleep 20      # a mesher started right after the solver closed hung waiting for the license
}

if ($args -contains "-images") {
    "=== images"; python images_cases.py stock_45C_pl design1_45C_pl design2_45C_pl *> images_pl_log.txt; "images exit $LASTEXITCODE"
}
Close-Fluent

foreach ($lvl in @("coarse", "fine")) {
    Remove-Item "hotend_d2_$lvl.msh.h5" -ErrorAction SilentlyContinue        # never keep a surface-only mesh
    for ($try = 1; $try -le 3; $try++) {                                     # launch can fail right after a session closes
        "=== mesh $lvl (try $try)"
        python mesh_wtm.py hotend_cfd_domain_d2.step "hotend_d2_$lvl.msh.h5" $lvl *> "mesh_${lvl}_log.txt"
        $ok = Select-String -Path "mesh_${lvl}_log.txt" -Pattern 'cells were created' -Quiet
        "$lvl exit $LASTEXITCODE volume mesh $ok"
        if ($ok) { break }
        Remove-Item "hotend_d2_$lvl.msh.h5" -ErrorAction SilentlyContinue
        if (Select-String -Path "mesh_${lvl}_log.txt" -Pattern 'Fix the overlaps|cannot be completed' -Quiet) { break }   # geometry problem: retry won't help
        Get-Process fl_mpi2610, cx2610, fluent -ErrorAction SilentlyContinue | Stop-Process -Force -Confirm:$false
        Start-Sleep 30
    }
}
Select-String -Path mesh_coarse_log.txt, mesh_fine_log.txt -Pattern 'cells were created|Orthogonal Quality of|license' | ForEach-Object { $_.Line }

& (Join-Path $cfd "start_fluent.ps1")
foreach ($lvl in @("coarse", "fine")) {
    $mesh = "hotend_d2_$lvl.msh.h5"
    if (-not (Test-Path $mesh)) { "skip $lvl (no mesh)"; continue }
    "=== solve $lvl"
    python setup_case.py $mesh 45 ti *> "setup_${lvl}_log.txt"; "setup $lvl exit $LASTEXITCODE"
    python step11_meshstudy.py "design2_45C_pl_$lvl" *> "solve_${lvl}_log.txt"; "solve $lvl exit $LASTEXITCODE"
    Select-String -Path "solve_${lvl}_log.txt" -Pattern 'CONVERGENCE|^  t_stub|^  t_heatsink_max|BALANCE|done' | ForEach-Object { $_.Line }
}
"=== all done"
