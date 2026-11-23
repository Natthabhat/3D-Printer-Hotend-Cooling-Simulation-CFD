# Start a visible Fluent 3D double-precision solver (4 cores) that PyFluent scripts can attach to via server_info.txt
$cfd = Split-Path -Parent $MyInvocation.MyCommand.Path
$fluent = "C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe"
$si = Join-Path $cfd "server_info.txt"
Remove-Item $si -ErrorAction SilentlyContinue
Start-Process -FilePath $fluent -ArgumentList @("3ddp", "-t4", "-sifile=`"$si`"") -WorkingDirectory $cfd
$deadline = (Get-Date).AddMinutes(4)
while (-not (Test-Path $si) -and (Get-Date) -lt $deadline) { Start-Sleep 3 }
if (Test-Path $si) { "Fluent ready: $si" } else { "Fluent did not write $si"; exit 1 }
