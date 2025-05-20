@echo off
setlocal enabledelayedexpansion

if "%1"=="" (
    echo Mapped pip command to poetry:
    echo For installing packages use: poetry add package-name
    echo For removing packages use: poetry remove package-name
    echo For installing all dependencies use: poetry install
    echo For updating packages use: poetry update
    goto :eof
)

if "%1"=="install" (
    if "%2"=="-e" (
        poetry add --editable %3
    ) else if "%2"=="-r" (
        poetry install
    ) else (
        poetry add %2 %3 %4 %5 %6 %7 %8 %9
    )
    goto :eof
)

if "%1"=="uninstall" (
    poetry remove %2 %3 %4 %5 %6 %7 %8 %9
    goto :eof
)

if "%1"=="freeze" (
    poetry show --tree
    goto :eof
)

if "%1"=="list" (
    poetry show
    goto :eof
)

rem For dev dependencies
if "%1"=="install-dev" (
    poetry add --group dev %2 %3 %4 %5 %6 %7 %8 %9
    goto :eof
)

rem For installing all dependencies
if "%1"=="sync" (
    poetry install
    goto :eof
)

echo Unknown command. Available commands:
echo pip install [package]    - Install a package
echo pip uninstall [package] - Remove a package
echo pip list               - Show installed packages
echo pip freeze            - Show dependency tree
echo pip install-dev       - Install dev dependencies
echo pip sync             - Install all dependencies from pyproject.toml 