# Online Text-Based Browser RPG

RPG online de texto baseado em jogos como Gladiatus, BitFight, Travian e outros clássicos dos anos 2000.

## Requisitos
- Python 3.10 (conforme [Pipfile](Pipfile))
- Pipenv (ou equivalente) para instalar dependências listadas em [Pipfile](Pipfile)
- Postgres configurado via variável de ambiente `DATABASE_URL` 

## Configuração rápida (desenvolvimento)
1. Instale dependências:
```bash
pipenv install
```
2. Copie o template de variáveis de ambiente e ajuste:
- [app/.env.template](app/.env.template) → crie [app/.env](app/.env)

3. Execute migrações e crie superusuário:
```bash
# a partir da pasta app/
python manage.py migrate
python manage.py createsuperuser
```
(`app/manage.py` — [app/manage.py](app/manage.py))

4. Rode o servidor de desenvolvimento:

```bash
python manage.py runserver
```
