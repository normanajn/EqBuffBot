@echo off
cd /d "%~dp0"
:: To use a different config file, pass -c or --config:
::   python -m eqbuffbot.main --config mychar_config.yaml
python -m eqbuffbot.main %*
pause
