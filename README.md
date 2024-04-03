![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/MePhew-GonteQ-Industries/zolza-hairstyles-api/test-deploy.yml?logo=bilibili&style=for-the-badge) ![GitHub last commit](https://img.shields.io/github/last-commit/MePhew-GonteQ-Industries/zolza-hairstyles-api?color=8bd5ca&logo=starship&style=for-the-badge) ![GitHub repo size](https://img.shields.io/github/repo-size/MePhew-GonteQ-Industries/zolza-hairstyles-api?logo=github&style=for-the-badge)

![Endpoint Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMePhew-GonteQ-Industries%2Fzolza-hairstyles-uptime%2Fmaster%2Fapi%2Fapi%2Fuptime.json&style=for-the-badge)
![Endpoint Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMePhew-GonteQ-Industries%2Fzolza-hairstyles-uptime%2Fmaster%2Fapi%2Fapi%2Fresponse-time.json&style=for-the-badge)

# Zołza Hairstyles Hairdressing Salon

## Appointments management system - API repo

## Table of Contents

- 🧩 [Features](#features)
- 🏠 [Local Development](#local-development)
- 🚀 [Production Deployment](#production-deployment)
- 🚀 [Running behind a proxy](#proxy-configuration)
- ⚖️ [License](#license)

## <a name="features">🧩 Features</a>

List of the features that have been implemented so far:

- [x] User accounts
    - [x] Registration
    - [x] Account deletion
    - [x] Account activation via email
    - [x] Logging in
    - [x] Password reset via email
    - [x] Account types with diffrent permissions (users, admins and the owner)
- [X] Booking appointments:
    - [x] Booking through the appointments page by first selecting a service and then followed by selecting a date
    - [X] Quick booking from the home page
- [ ] Administrative features
    - [ ] Business summary and overview
    - [ ] Appointments management
    - [ ] Services management
    - [ ] Users administration
    - [ ] Work hours management
    - [ ] Business statistics
    - [ ] Administrative settings
- [ ] Settings
    - [x] Updating user data (name, surname and gender)
    - [ ] Account security
        - [x] Password change
        - [x] Active sessions management
            - [x] Log out of every session seperately
            - [x] Log out everywhere
            - [x] Show location on a map based on IP address
        - [ ] Two-Factor Authentication
    - [ ] Notification settings
        - [ ] Appointment reminders
        - [ ] New functionality added
    - [X] Themes
    - [x] Internalization
        - [x] Translations
            - [x] Polish
            - [x] English

## <a name="local-development">🏠 Local development</a>

1. First you need to install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2. Set required environment variables

    ```dotenv
    API_VERSION='1.0.0 Stable'
    API_TITLE='<API name>'
    # See https://docs.python.org/3/library/logging.html#logging-levels for available logging levels
    LOG_LEVEL='<DEBUG/INFO...>'

    # Pytz timezone (see https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568 for list of all timezones)
    COMPANY_TIMEZONE: str

    # Used mostly for email messages
    COMPANY_NAME=''
    BASE_URL='/api'
    # Used for account activation and password reset links
    FRONTEND_URL='<frontend URL>'

    DATABASE_USERNAME=''
    DATABASE_PASSWORD=''
    DATABASE_HOSTNAME=''
    DATABASE_PORT=''
    DATABASE_NAME=''

    # See https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/?h=secret#handle-jwt-tokens for more info
    API_SECRET='<cryptographically secure secret key used for generating JWT tokens>'
    ALGORITHM='<e.g. HS256>'
    ACCESS_TOKEN_EXPIRE_MINUTES='<e.g. 60>'

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES='<e.g. 10>'

    MAIL_VERIFICATION_COOLDOWN_MINUTES='<e.g. 5>'
    PASSWORD_RESET_COOLDOWN_MINUTES='<e.g. 15>'

    # Email service configuration used for sending account activation, password reset, appointment reminder and administrative messages
    MAIL_USERNAME=''
    MAIL_PASSWORD=''
    MAIL_FROM='no-reply@example.com'
    MAIL_PORT=587
    MAIL_SERVER=''
    MAIL_STARTTLS=true
    MAIL_SSL_TLS=false
    USE_CREDENTIALS=true
    VALIDATE_CERTS=true
    MAIL_FROM_NAME=''

    # Access token obtained from https://ipinfo.io/ used for displaying info about ip addresses associated with sessions
    IPINFO_ACCESS_TOKEN=''

    # Time for which users won't be asked again to enter their passwords when performing critical operations
    SUDO_MODE_TIME_HOURS='<e.g. 2>'

    # Service durations are a multiple of this number
    # Thus it determines the shortest possible time a service can take
    # Setting it too high would probably mean a lot of wasted time between appointments
    # Setting it too low would make it harder for admins to reserve slots
    APPOINTMENT_SLOT_TIME_MINUTES='<e.g. 30>'

    # Determines the latest possible date users can book their appointments
    MAX_FUTURE_APPOINTMENT_DAYS='<e.g. 30>'

    # Path to JSON credentials file obtained from https://firebase.google.com/
    # Used for sending notifications via FCM (see https://firebase.google.com/docs/cloud-messaging for more info)
    FIREBASE_SERVICE_ACCOUNT_CREDENTIALS_PATH="<path>.json"
    ```

3. Initialize dynamic resources

Working hours are stored in a JSON file in project's directory

Path to the file has to be as follows: `<PROJECT_ROOT>/dynamic_resources/weekplan.json`

File structure:

`weekplan.json`

```json
[
  // Each object represents a single day
  {
    "work_hours": {
      "start_hour": 9,
      "start_minute": 0,
      "end_hour": 17,
      "end_minute": 30
    },
    "breaks": [
      // Each object represents a single break
      {
        "start_hour": 13,
        "start_minute": 30,
        // Time has to be a multiple of APPOINTMENT_SLOT_TIME_MINUTES
        "time_minutes": 30
      }
    ]
  },
  // Workaround to create a day off by setting the end time to the same value as start time
  {
    "work_hours": {
      "start_hour": 9,
      "start_minute": 0,
      "end_hour": 9,
      "end_minute": 0
    },
    "breaks": []
  },
  ...
]
```

4. Create a database and tables

Create tables using the following command (database has to be already created):

```bash
alembic upgrade head
```

5. Run the API using [Uvicorn](https://www.uvicorn.org/) via the provided startup script

```bash
python3 run_uvicorn.py
```

## <a name="production-deployment">🚀 Production Deployment</a>

You can use [Gunicorn](https://gunicorn.org/) as a production server.

If you are using multiple workers you need to configure your server to call the init_app() function on startup.

Example for Gunicorn:

`gunicorn.conf.py`

```py
from init_app import init_app


def on_starting(_server):
    init_app()
```

Otherwise, you can call this function in another file (e.g. `main.py`)

Example startup command for Gunicorn:

```bash
gunicorn --access-logfile ./gunicorn-access.log --error-logfile ./gunicorn-error.log --workers 4 --worker-class uvicorn.workers.UvicornWorker src.main:app
```

If your server is using systemd as a service manager you can also create a custom unit file to make managing the API's
state easier

Example systemd unit file:

```ini
[Unit]
Description = <UNIT_NAME>
After = network.target

[Service]
User = ubuntu
Group = ubuntu
WorkingDirectory = <PROJECT_ROOT>
Environment = "PATH=<PROJECT_ROOT>/venv/bin"
EnvironmentFile = <PROJECT_ROOT>/.env
ExecStart = <PROJECT_ROOT>/venv/bin/gunicorn --access-logfile ./gunicorn-access.log --error-logfile ./gunicorn-error.log --workers 4 --worker-class uvicorn.workers.UvicornWorker src.main:app

[Install]
WantedBy = multi-user.target
```

## <a name="proxy-configuration">🚪 Running behind a proxy</a>

If you want to run the api behind a proxy (e.g. to make managing SSL ceritficates easier
with [Certbot](https://certbot.eff.org/)) you need to make sure original IP addresses are forwarded to the API for
sessions management to work correctly.

Example configuration for [Nginx](https://www.nginx.com/):

```nginx
server {
        server_name <list of server domain names>;

        # make API accessible on <server_root>/api URL
        location /api {
                proxy_pass http://localhost:<local API port number>;

                proxy_http_version 1.1;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection 'upgrade';
                proxy_set_header Host $http_host;
                proxy_set_header X-NginX-Proxy true;
                proxy_redirect off;
        }
}
```

You can use [DigitalOcean's config generation tool](https://www.digitalocean.com/community/tools/nginx) to generate
a secure Nginx config

## <a name="license">⚖️ License</a>

[GPL-3.0](./LICENSE)
