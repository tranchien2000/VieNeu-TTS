@echo off
setlocal enabledelayedexpansion
if "%~1"=="" (
  for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set "BRANCH=%%b"
) else (
  set "BRANCH=%~1"
)
git checkout "%BRANCH%"
git fetch upstream
git rebase "upstream/%BRANCH%"
git push origin "%BRANCH%" --force-with-lease
echo Sync complete for %BRANCH%
