# JNCC Annotations API deployment instructions

Below is the deployment procedure for the annotations-api and related services in the JNCC Windows Server. It avoids Docker/WSL and runs everything directly on Windows Server 2022.

The resulting architecture is:

```text
Windows Server 2022
│
├── PostgreSQL 18 :5432
│   ├── worms-cachedb
│   └── annotationsdb + PostGIS
│
├── Taxamatch
│   └── Ruby 2.7 + Puma :8082
│
├── worms-cache
│   └── Python 3.13 + Django :8001
│
├── annotations-api
│   └── Python 3.13 + Django/GeoDjango :8000
│
└── Later:
    Caddy / IIS
    └── HTTPS :443
```

The services communicate internally through `127.0.0.1`.

---

## 1. Prepare Windows Server

Open **PowerShell as Administrator**.

Create a directory for the applications:

```powershell
mkdir C:\Users\nocadmin\paidiver
cd C:\Users\nocadmin\paidiver
```

You already installed Chocolatey. Verify it:

```powershell
choco --version
```

Install Git if needed:

```powershell
choco install git -y
```

Open a new PowerShell and check:

```powershell
git --version
```

---

## 2. Install Python 3.13

Both Python applications use Python 3.13.

With Chocolatey:

```powershell
choco install python313 -y
```

Open a new PowerShell and check:

```powershell
py -3.13 --version
```

You should see:

```text
Python 3.13.x
```

Each application should have its own `.venv`, created with the required Python version.

---

## 3. Install `uv`

Install `uv` using Python:

```powershell
py -3.13 -m pip install uv
```

Test it even if its executable is not yet on `PATH`:

```powershell
py -3.13 -m uv --version
```

If `uv` itself works directly:

```powershell
uv --version
```

you can use `uv` from this point onward.

Otherwise use:

```powershell
py -3.13 -m uv
```

until its Scripts directory is added to PATH.

---

## 4. Clone the projects

Go to:

```powershell
cd C:\Users\nocadmin\paidiver
```

Clone:

```powershell
git clone https://github.com/paidiver/worms-cache.git
git clone https://github.com/paidiver/annotations-api.git
```

Your structure becomes:

```text
C:\Users\nocadmin\paidiver\
│
├── worms-cache\
└── annotations-api\
```

It is important to mention that both packages needed to be updated in order to work in this environment. Because of that, all the steps related to the deployment of the packages should be performed in the `jncc` branch of each repo.

---

## 5. PostgreSQL

You already discovered that the server has:

```text
PostgreSQL 18
C:\Program Files\PostgreSQL\18
Service: postgresql-x64-18
Port: 5432
```

You can connect locally with:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
    -h 127.0.0.1 `
    -p 5432 `
    -U postgres
```

Using `127.0.0.1` is important because your current `pg_hba.conf` has:

```text
host    all    all    127.0.0.1/32    trust
```

while IPv6 uses password authentication.

You have already created the databases, but the intended layout is:

```text
PostgreSQL 18
│
├── worms-cachedb
│   └── worms_user
│
└── annotationsdb
    ├── annotations_user
    └── PostGIS
```

For example:

```sql
CREATE ROLE worms_user
WITH LOGIN PASSWORD 'STRONG_PASSWORD';

CREATE DATABASE "worms-cachedb"
OWNER worms_user;

CREATE ROLE annotations_user
WITH LOGIN PASSWORD 'ANOTHER_STRONG_PASSWORD';

CREATE DATABASE annotationsdb
OWNER annotations_user;
```

For annotations:

```sql
\c annotationsdb

CREATE EXTENSION postgis;
```

Verify:

```sql
SELECT PostGIS_Version();
```


Plese also create the DEV databases with dev users:

```sql
CREATE ROLE worms_user_dev
WITH LOGIN PASSWORD 'STRONG_PASSWORD';

CREATE DATABASE "worms-cachedb-dev"
OWNER worms_user_dev;

CREATE ROLE annotations_user_dev
WITH LOGIN PASSWORD 'STRONG_PASSWORD';

CREATE DATABASE annotationsdb-dev
OWNER annotations_user_dev;

\c annotationsdb

CREATE EXTENSION postgis;

SELECT PostGIS_Version();
```


Once everything is working, I strongly recommend changing the IPv4 rule from:

```text
trust
```

to:

```text
scram-sha-256
```

so your applications actually authenticate using their database passwords.

---

## 6. Install PostGIS

`annotations-api` uses GeoDjango and requires PostGIS.

Install PostGIS for PostgreSQL 18 using **StackBuilder**.

Open:

```text
Start → StackBuilder
```

Select:

```text
PostgreSQL 18 (x64)
```

and install the appropriate PostGIS package under spatial extensions.

Then check from PostgreSQL:

```sql
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name = 'postgis';
```

Inside `annotationsdb`:

```sql
CREATE EXTENSION postgis;
```

---

## 7. Configure `worms-cache`

Enter the project:

```powershell
cd C:\Users\nocadmin\paidiver\worms-cache
```

Install dependencies:

```powershell
uv sync --locked
```

This should create:

```text
worms-cache\.venv\
```

Check:

```powershell
.\.venv\Scripts\python.exe --version
```

It should be Python 3.13.

Create:

```text
C:\Users\nocadmin\paidiver\worms-cache\.env
```

with configuration similar to:

```env
POSTGRES_DB=worms-cachedb
POSTGRES_USER=worms_user
POSTGRES_PASSWORD=YOUR_PASSWORD
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=GENERATE_A_LONG_RANDOM_SECRET
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

WORMS_API_BASE_URL=https://marinespecies.org/rest

TAXAMATCH_URL=http://127.0.0.1:8082

INGEST_API_TOKEN=GENERATE_A_RANDOM_TOKEN
```

### 7.1 Make Django load `.env`

> IMPORTANT: this part is already updated in the `jncc` branch and it is not necessary to run again

If the project doesn't already load `.env`, install:

```powershell
uv add python-dotenv
```

Then near the beginning of `config/settings.py`:

```python
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
```

Then Django can continue using:

```python
os.getenv("POSTGRES_HOST")
```

etc.

Test loading variables:

```powershell
uv run python manage.py shell
```

then:

```python
import os
print(os.getenv("POSTGRES_HOST"))
print(os.getenv("TAXAMATCH_URL"))
```

Exit with:

```python
exit()
```

### 7.2 Run migrations

```powershell
uv run python manage.py migrate
```

Don't start the final service yet because Taxamatch should be available first.

---

## 8. Install Ruby 2.7 + DevKit for Taxamatch

Taxamatch is not Python. It uses Ruby and old dependencies.

You need:

```text
Ruby 2.7 x64
MSYS2 / DevKit
```

Use the archived **RubyInstaller + DevKit 2.7 x64** package (available [here](https://github.com/oneclick/rubyinstaller2/releases/download/RubyInstaller-2.7.3-1/rubyinstaller-devkit-2.7.3-1-x64.exe))

During installation enable:

```text
Add Ruby executables to PATH
MSYS2 / DevKit
```

Then run:

```powershell
ridk install
```

Install the MSYS2 base system and MINGW development toolchain.

Open a new PowerShell and verify:

```powershell
ruby --version
```

You currently obtained approximately:

```text
ruby 2.7.3
```

Check:

```powershell
gem --version
ridk version
```

---

## 9. Install Taxamatch dependencies

Enter:

```powershell
cd C:\Users\nocadmin\paidiver\worms-cache\taxamatch_service
```

Install the required Bundler:

```powershell
gem install bundler -v 2.4.22
```

Check:

```powershell
bundle _2.4.22_ --version
```

Install gems:

```powershell
bundle _2.4.22_ install
```

You already reached:

```text
Bundle complete!
```

which means the legacy native dependencies compiled successfully.

---

## 10. Run Taxamatch on Windows

This is important: **Puma worker mode does not work on Windows** because it relies on Unix process forking.

Because of that, the `puma.rb` file inside `taxamatch_service` was updated in order to disallow workers in windows.

Set:

```powershell
cd C:\Users\nocadmin\paidiver\worms-cache\taxamatch_service

$env:RACK_ENV="production"
$env:BIND="127.0.0.1"
$env:PORT="8082"
$env:PUMA_THREADS="8"
$env:MAX_NAMES="50"
$env:MAX_CANDIDATES_PER_NAME="300"
```

Them run:

```powershell
bundle exec puma -C puma.rb config.ru
```

You want to eventually see:

```text
Puma starting in single mode...
...
* Listening on tcp://127.0.0.1:8082
```

In another PowerShell check:

```powershell
Get-NetTCPConnection -LocalPort 8082 -State Listen
```

and:

```powershell
curl.exe http://127.0.0.1:8082/
```

You should see something like

```output
{"ok":true,"version":"1.1.2"}
```

---

## 11. Run `worms-cache`

Once Taxamatch is listening on `8082`, return to:

```powershell
cd C:\Users\nocadmin\paidiver\worms-cache
```

Make sure `.env` contains:

```env
TAXAMATCH_URL=http://127.0.0.1:8082
```

Run migrations if not already done:

```powershell
uv run python manage.py migrate
```

For initial testing:

```powershell
uv run python manage.py runserver 127.0.0.1:8001
```

Check:

```powershell
curl.exe http://127.0.0.1:8001/api/health/
```

The intended internal path is now:

```text
worms-cache :8001
      │
      ├── PostgreSQL → 127.0.0.1:5432
      │
      └── Taxamatch → 127.0.0.1:8082
```

---

## 12. Install GDAL for `annotations-api`

This is required because `annotations-api` uses GeoDjango.

Without it, you got:

```text
django.core.exceptions.ImproperlyConfigured:
Could not find the GDAL library
```

Install **OSGeo4W** (https://download.osgeo.org/osgeo4w/v2/osgeo4w-setup.exe) and include:

```text
GDAL
GEOS
PROJ
```

A typical installation location is:

```text
C:\OSGeo4W
```

If you install it only for an specific user, the installation location could be different, like the one below:

```text
C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W
```

Check:

```powershell
Get-ChildItem C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin\gdal*.dll
```

Then configure the current shell:

```powershell
$env:PATH = "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin;$env:PATH"
$env:GDAL_DATA = "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\gdal"
$env:PROJ_LIB = "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\proj"
```

Test:

```powershell
gdalinfo --version
```

Find your actual GDAL DLL:

```powershell
Get-ChildItem C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin\gdal*.dll |
    Select-Object FullName
```

For example:

```text
C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin\gdal311.dll
```

Because your Django version searches older DLL names such as:

```text
gdal306
gdal305
...
```

you may need to specify the DLL explicitly in Django setting file (it is already added to the settings in the `jncc` branch:

```python
GDAL_LIBRARY_PATH = r"C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin\gdal311.dll"
GEOS_LIBRARY_PATH = r"C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin\geos_c.dll"
```

Use the actual filenames present on your server.

For permanent machine-level variables:

```powershell
[Environment]::SetEnvironmentVariable(
    "GDAL_DATA",
    "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\gdal",
    "Machine"
)

[Environment]::SetEnvironmentVariable(
    "PROJ_LIB",
    "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\proj",
    "Machine"
)
```

Also eventually put:

```text
C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin
```

on the machine PATH.

---

## 13. Configure `annotations-api`

Enter:

```powershell
cd C:\Users\nocadmin\paidiver\annotations-api
```

Install the environment:

```powershell
uv sync --locked
```

Create:

```text
C:\Users\nocadmin\paidiver\annotations-api\.env
```

For example:

```env
POSTGRES_DB=annotationsdb
POSTGRES_USER=annotations_user
POSTGRES_PASSWORD=YOUR_PASSWORD
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=GENERATE_ANOTHER_LONG_SECRET
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

WORMS_API_BASE_URL=https://marinespecies.org/rest

CACHED_WORMS_API_BASE_URL=http://127.0.0.1:8001/api
CACHED_WORMS_API_TOKEN=SAME_TOKEN_USED_BY_WORMS_CACHE
```


### 13.1 Make Django load `.env`

> IMPORTANT: this part is already updated in the `jncc` branch and it is not necessary to run again

If the project doesn't already load `.env`, install:

```powershell
uv add python-dotenv
```

Then near the beginning of `config/settings.py`:

```python
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
```

Then Django can continue using:

```python
os.getenv("POSTGRES_HOST")
```

etc.

Test loading variables:

```powershell
uv run python manage.py shell
```

then:

```python
import os
print(os.getenv("POSTGRES_HOST"))
print(os.getenv("TAXAMATCH_URL"))
```

Exit with:

```python
exit()
```

---

## 14. Run annotations migrations

Make sure the GDAL environment is available in this PowerShell:

```powershell
$env:PATH = "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin;$env:PATH"
$env:GDAL_DATA = "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\gdal"
$env:PROJ_LIB = "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\proj"
```

Then:

```powershell
cd C:\Users\nocadmin\paidiver\annotations-api

uv run python manage.py migrate
```

If this completes, you have confirmed:

```text
Python ✓
Django ✓
PostgreSQL ✓
PostGIS ✓
GDAL ✓
GEOS ✓
PROJ ✓
```

Now test the application:

```powershell
uv run python manage.py runserver 127.0.0.1:8000
```

From another PowerShell:

```powershell
curl.exe http://127.0.0.1:8000/api/health/
```

---

## 15. Create the annotations user

In order to create the user, please run the command below:

```powershell
uv run python manage.py create_user_with_token <username> <password>
```

Please get the token and save it, as you will need it in the ingest endpoints.


## 16. Final internal connectivity

When everything is running, the server should look like:

```text
                       PostgreSQL :5432
                      /               \
                     /                 \
          worms-cachedb              annotationsdb
                                      + PostGIS

                 Taxamatch :8082
                        ▲
                        │
                        │
               worms-cache :8001
                        ▲
                        │
                        │ Cached WoRMS
                        │
              annotations-api :8000
```

The important addresses are:

```text
PostgreSQL:
127.0.0.1:5432

Taxamatch:
http://127.0.0.1:8082

worms-cache:
http://127.0.0.1:8001

annotations-api:
http://127.0.0.1:8000
```

---

## 17. Don't use Django `runserver` in production

The commands:

```powershell
python manage.py runserver
```

are useful for confirming that everything works, but they should not be your final deployment.

For Django on Windows, use **Waitress**.

For `worms-cache`:

```powershell
cd C:\Users\nocadmin\paidiver\worms-cache

uv pip install waitress
```

Then:

```powershell
uv run waitress-serve `
    --listen=127.0.0.1:8001 `
    config.wsgi:application
```

For `annotations-api`:

```powershell
cd C:\Users\nocadmin\paidiver\annotations-api

uv pip install waitress
```

Then:

```powershell
uv run waitress-serve `
    --listen=127.0.0.1:8000 `
    config.wsgi:application
```

---

## 18. Create Windows services

You don't want to RDP into the server after every reboot and manually run:

```text
Taxamatch
worms-cache
annotations-api
```

The final deployment should make them Windows services.

A convenient tool for this is **NSSM**.


The basic pattern will be:

```text
Windows Service
   ↓
NSSM
   ↓
your executable + arguments
```

For example:

```text
paidiver-worms-cache
   ↓
C:\...\worms-cache\.venv\Scripts\waitress-serve.exe
   ↓
--listen=127.0.0.1:8001 config.wsgi:application
```

and similarly for `annotations-api` and `taxamatch`.

### 18.1 Install NSSM

In Administrator PowerShell:

```powershell
choco install nssm -y
```

Then verify:

```powershell
nssm version
```

If `nssm` is not immediately found, close PowerShell and open a new Administrator PowerShell.


## 19. Create `worms-cache` service

It is cleaner to point NSSM directly at the executable inside the virtual environment.

Considering that the project is:

```text
C:\Users\nocadmin\paidiver\worms-cache
```

the executable should be:

```text
C:\Users\nocadmin\paidiver\worms-cache\.venv\Scripts\waitress-serve.exe
```

First verify it exists:

```powershell
Test-Path "C:\Users\nocadmin\paidiver\worms-cache\.venv\Scripts\waitress-serve.exe"
```

Then create the service:

```powershell
nssm install paidiver-worms-cache
```

A GUI will open.

Set:

```text
Path:
C:\Users\nocadmin\paidiver\worms-cache\.venv\Scripts\waitress-serve.exe

Startup directory:
C:\Users\nocadmin\paidiver\worms-cache

Arguments:
--listen=127.0.0.1:8001 config.wsgi:application
```

Then click **Install service**.

You can also do the same entirely from PowerShell:

```powershell
nssm install paidiver-worms-cache `
  "C:\Users\nocadmin\paidiver\worms-cache\.venv\Scripts\waitress-serve.exe" `
  "--listen=127.0.0.1:8001 config.wsgi:application"
```

Then set the working directory:

```powershell
nssm set paidiver-worms-cache AppDirectory `
  "C:\Users\nocadmin\paidiver\worms-cache"
```


### 19.1 Configure environment variables for `worms-cache`

A Windows Service will not necessarily inherit the same environment you have in your interactive PowerShell session.

If your Django code loads `.env` itself with `python-dotenv`, then keeping:

```text
C:\Users\nocadmin\paidiver\worms-cache\.env
```

is enough.

If not, configure the service environment explicitly.

For example:

```powershell
nssm set paidiver-worms-cache AppEnvironmentExtra `
  "POSTGRES_HOST=127.0.0.1" `
  "POSTGRES_PORT=5432" `
  "POSTGRES_DB=worms-cachedb" `
  "POSTGRES_USER=worms_user" `
  "POSTGRES_PASSWORD=YOUR_PASSWORD" `
  "TAXAMATCH_URL=http://127.0.0.1:8082"
```


### 19.2 Configure logs for `worms-cache`

Create a logs folder:

```powershell
mkdir C:\Users\nocadmin\paidiver\logs
```

Then:

```powershell
nssm set paidiver-worms-cache AppStdout `
  C:\Users\nocadmin\paidiver\logs\worms-cache.log
```

and:

```powershell
nssm set paidiver-worms-cache AppStderr `
  C:\Users\nocadmin\paidiver\logs\worms-cache-error.log
```

Enable log rotation:

```powershell
nssm set paidiver-worms-cache AppRotateFiles 1
nssm set paidiver-worms-cache AppRotateOnline 1
nssm set paidiver-worms-cache AppRotateBytes 10485760
```

That rotates around 10 MB.


### 19.3 Start `worms-cache`

Run:

```powershell
Start-Service paidiver-worms-cache
```

Check:

```powershell
Get-Service paidiver-worms-cache
```

You want:

```text
Status   Name
------   ----
Running  paidiver-worms-cache
```

Then:

```powershell
Get-NetTCPConnection -LocalPort 8001 -State Listen
```

and:

```powershell
curl.exe http://127.0.0.1:8001/api/health/
```

If it fails, inspect:

```powershell
Get-Content C:\Users\nocadmin\paidiver\logs\worms-cache-error.log -Tail 100
```

## 20. Create the `annotations-api` service


Assuming:

```text
C:\Users\nocadmin\paidiver\annotations-api
```

verify:

```powershell
Test-Path "C:\Users\nocadmin\paidiver\annotations-api\.venv\Scripts\waitress-serve.exe"
```

Then:

```powershell
nssm install paidiver-annotations-api `
  "C:\Users\nocadmin\paidiver\annotations-api\.venv\Scripts\waitress-serve.exe" `
  "--listen=127.0.0.1:8000 config.wsgi:application"
```

Set working directory:

```powershell
nssm set paidiver-annotations-api AppDirectory `
  "C:\Users\nocadmin\paidiver\annotations-api"
```

Logs:

```powershell
nssm set paidiver-annotations-api AppStdout `
  C:\Users\nocadmin\paidiver\logs\annotations-api.log

nssm set paidiver-annotations-api AppStderr `
  C:\Users\nocadmin\paidiver\logs\annotations-api-error.log

nssm set paidiver-annotations-api AppRotateFiles 1
nssm set paidiver-annotations-api AppRotateOnline 1
nssm set paidiver-annotations-api AppRotateBytes 10485760
```


### 20.1 GDAL variables for `annotations-api`

As `annotations-api` uses GeoDjango, it is necessary to have theOSGeo/GDAL environment.

If your OSGeo4W installation is:

```text
C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W
```

the service must know about:

```text
C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin
GDAL_DATA
PROJ_LIB
```

You can set these machine-wide:

```powershell
[Environment]::SetEnvironmentVariable(
    "GDAL_DATA",
    "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\gdal",
    "Machine"
)

[Environment]::SetEnvironmentVariable(
    "PROJ_LIB",
    "C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\proj",
    "Machine"
)
```

Add OSGeo4W to machine PATH:

```powershell
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")

if ($machinePath -notlike "*C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin*") {
    [Environment]::SetEnvironmentVariable(
        "Path",
        "$machinePath;C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\bin",
        "Machine"
    )
}
```

Then restart the service after setting them.

Alternatively you can add them specifically to NSSM:

```powershell
nssm set paidiver-annotations-api AppEnvironmentExtra `
  "GDAL_DATA=C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\gdal" `
  "PROJ_LIB=C:\Users\nocadmin\AppData\Local\Programs\OSGeo4W\share\proj"
```

You also need to explicitly set `GDAL_LIBRARY_PATH` in Django settings. This part is already updated in the `jncc` branch.

---

### 20.2 Start `annotations-api`

```powershell
Start-Service paidiver-annotations-api
```

Check:

```powershell
Get-Service paidiver-annotations-api
```

Then:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

and:

```powershell
curl.exe http://127.0.0.1:8000/api/health/
```

If it fails:

```powershell
Get-Content `
  C:\Users\nocadmin\paidiver\logs\annotations-api-error.log `
  -Tail 100
```


## 21. Create the Taxamatch service

This one is slightly different because it is Ruby/Puma.

You first need the command working manually.

Assuming:

```text
C:\Users\nocadmin\paidiver\worms-cache\taxamatch_service
```

and Ruby is:

```text
C:\Ruby27-x64\bin\ruby.exe
```

and bundle is:

```text
C:\Ruby27-x64\bin\bundle
```

Create the service:


```powershell
nssm install paidiver-taxamatch `
  "C:\Ruby27-x64\bin\ruby.exe" `
  "C:\Ruby27-x64\bin\bundle exec puma -C puma.rb config.ru"
```

Set the working directory:

```powershell
nssm set paidiver-taxamatch AppDirectory `
  "C:\Users\nocadmin\paidiver\worms-cache\taxamatch_service"
```

Set environment variables:

```powershell
nssm set paidiver-taxamatch AppEnvironmentExtra `
  "RACK_ENV=production" `
  "BIND=127.0.0.1" `
  "PORT=8082" `
  "PUMA_THREADS=8" `
  "MAX_NAMES=50" `
  "MAX_CANDIDATES_PER_NAME=300"
```

Logs:

```powershell
nssm set paidiver-taxamatch AppStdout `
  C:\Users\nocadmin\paidiver\logs\taxamatch.log

nssm set paidiver-taxamatch AppStderr `
  C:\Users\nocadmin\paidiver\logs\taxamatch-error.log

nssm set paidiver-taxamatch AppRotateFiles 1
nssm set paidiver-taxamatch AppRotateOnline 1
nssm set paidiver-taxamatch AppRotateBytes 10485760
```

Before starting the service, edit the account related to the service. Open the NSSM configuration:

```powershell
nssm edit paidiver-taxamatch

```
Go to the Log on tab. Select `This account` and use `.\nocadmin`. And add the windows password.

Then:

```powershell
Start-Service paidiver-taxamatch
```

Check:

```powershell
Get-NetTCPConnection -LocalPort 8082 -State Listen
```

It may take a couple of minutes until Taxamatch reaches the `Listening` state. Please check the logs:

```powershell
Get-Content `
  "C:\Users\nocadmin\paidiver\logs\taxamatch.log" `
  -Tail 100
```

## 22. Make them start automatically

NSSM services normally install with automatic startup, but verify:

```powershell
Get-Service `
  paidiver-taxamatch, `
  paidiver-worms-cache, `
  paidiver-annotations-api |
Select-Object Name, Status, StartType
```

You want:

```text
StartType
---------
Automatic
```

If necessary:

```powershell
Set-Service paidiver-taxamatch -StartupType Automatic
Set-Service paidiver-worms-cache -StartupType Automatic
Set-Service paidiver-annotations-api -StartupType Automatic
```

---

## 23. Configure service dependencies

This is useful because your logical order is:

```text
PostgreSQL
   ↓
Taxamatch
   ↓
worms-cache
   ↓
annotations-api
```

At minimum, make the Django services depend on PostgreSQL.

Your PostgreSQL service is:

```text
postgresql-x64-18
```

For example:

```powershell
sc.exe config paidiver-worms-cache depend= postgresql-x64-18
```

For annotations:

```powershell
sc.exe config paidiver-annotations-api depend= postgresql-x64-18
```

---

## 24. Public access

In order to expose the public APIs to the internet, use `Caddy` for this task:

```text
Internet
   │
   ▼
HTTPS :443
   │
   ▼
Caddy
   │
   ├── annotations.example.org
   │       → 127.0.0.1:8000
   │
   └── worms.example.org
           → 127.0.0.1:8001
```


### 24.1 Get domain names

For example:

```text
annotations.example.org
worms.example.org
```

Both DNS `A` records should point to your server's public IP.

You can use the same public IP for many applications because the proxy distinguishes them by hostname:

```text
annotations.example.org → same IP
worms.example.org       → same IP
```

### 24.2 Open ports 80 and 443 in Windows Firewall

Run Administrator PowerShell:

```powershell
New-NetFirewallRule `
  -DisplayName "HTTP 80" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 80 `
  -Action Allow
```

and:

```powershell
New-NetFirewallRule `
  -DisplayName "HTTPS 443" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 443 `
  -Action Allow
```

Check:

```powershell
Get-NetFirewallRule -DisplayName "HTTP 80","HTTPS 443"
```



### 24.3 Azure also needs ports 80/443

Because this is an Azure VM, Windows Firewall is only one layer.

The Azure Network Security Group also needs inbound rules approximately like:

```text
TCP 80
Source: Internet
Destination: VM
Action: Allow

TCP 443
Source: Internet
Destination: VM
Action: Allow
```

Keep RDP:

```text
3389
```

restricted to your trusted IP address(es).

Ask the server administrator to allow inbound `TCP/80` and `TCP/443`.


### 24.4 Caddy configuration

Install it with Chocolatey:

```powershell
choco install caddy -y
```

Then check:

```powershell
caddy version
```

Create Caddyfile:

```text
C:\caddy\Caddyfile
```

Then populate the file with the domain and the port of the annotations-api and worms-cache services:

```powershell
@"
annotations-api-jncc.atlantis-viz.online {
    reverse_proxy 127.0.0.1:8000
}

worms-cache-jncc.atlantis-viz.online {
    reverse_proxy 127.0.0.1:8001
}

"@ | Set-Content C:\caddy\Caddyfile
```

Caddy will automatically:

```text
listen on 80
redirect HTTP → HTTPS
obtain an SSL certificate
listen on 443
renew the SSL certificate
proxy requests to Django
```

provided that:

- DNS already points to this server;
- ports 80 and 443 are reachable from the internet.


### 24.5 Test Caddy manually first

Run:

```powershell
cd C:\caddy
caddy run --config Caddyfile
```

You should see it start and attempt to obtain the certificates.

Then externally you should be able to reach:

```text
https://annotations.example.org/api/health/
```

while on the server:

```powershell
curl.exe http://127.0.0.1:8000/api/health/
```

still talks directly to Waitress.

### 24.6 Run Caddy as a Windows service

Once the configuration works, use NSSM just as you did for the APIs.

For example:

```powershell
nssm install paidiver-caddy `
  "C:\ProgramData\chocolatey\bin\caddy.exe" `
  "run --config C:\caddy\Caddyfile"
```

Then:

```powershell
nssm set paidiver-caddy AppDirectory C:\caddy
```

Logs:

```powershell
nssm set paidiver-caddy AppStdout `
  C:\Users\nocadmin\paidiver\logs\caddy.log

nssm set paidiver-caddy AppStderr `
  C:\Users\nocadmin\paidiver\logs\caddy-error.log
```

Set automatic startup:

```powershell
Set-Service paidiver-caddy -StartupType Automatic
```

and start:

```powershell
Start-Service paidiver-caddy
```

Check:

```powershell
Get-Service paidiver-caddy
```

and:

```powershell
Get-NetTCPConnection -LocalPort 80,443 -State Listen
```

### 24.7 Update Django settings

For `annotations-api` and `worms-cache`, you'll also need the external hostname in `ALLOWED_HOSTS`.

For example:

```env
DJANGO_ALLOWED_HOSTS=annotations.example.org,localhost,127.0.0.1
# for worms-cache, uses the worms-cache domain
```

If a browser frontend calls this API from another domain, you'll also need the correct CORS origin, for example:

```text
https://your-frontend.example.org
```

rather than setting CORS to allow everything.
