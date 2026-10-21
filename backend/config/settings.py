import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/".env")

def env_bool(name,default=False): return os.getenv(name,str(default)).lower() in {"1","true","yes","on"}
def env_list(name,default): return [x.strip() for x in os.getenv(name,default).split(",") if x.strip()]
SECRET_KEY=os.getenv("SECRET_KEY","dev-only-change-this-to-a-64-character-random-secret-key-value")
DEBUG=env_bool("DEBUG",True)
ALLOWED_HOSTS=env_list("ALLOWED_HOSTS","localhost,127.0.0.1,0.0.0.0")
INSTALLED_APPS=["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","corsheaders","rest_framework","rest_framework_simplejwt.token_blacklist","accounts","students","dashboard","coding","assessments","assignments","courses","codeathons","interviews","attendance","gamification","notifications","reports"]
MIDDLEWARE=["corsheaders.middleware.CorsMiddleware","django.middleware.security.SecurityMiddleware",
            "whitenoise.middleware.WhiteNoiseMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="config.wsgi.application"; ASGI_APPLICATION="config.asgi.application"
DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.postgresql")

if DB_ENGINE.endswith("sqlite3"):
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "skelo_db"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "1234"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS=[{"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},{"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE="en-us"; TIME_ZONE="Asia/Kolkata"; USE_I18N=True; USE_TZ=True
STATIC_URL="static/"; STATIC_ROOT=BASE_DIR/"staticfiles"; MEDIA_URL="/media/"; MEDIA_ROOT=BASE_DIR/"media"; DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS=env_list("CORS_ALLOWED_ORIGINS","http://localhost:5173,http://127.0.0.1:5173")
CSRF_TRUSTED_ORIGINS=env_list("CSRF_TRUSTED_ORIGINS","http://localhost:5173,http://127.0.0.1:5173")
REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES":("rest_framework_simplejwt.authentication.JWTAuthentication",),"DEFAULT_PERMISSION_CLASSES":("rest_framework.permissions.IsAuthenticated",)}
SIMPLE_JWT={"ACCESS_TOKEN_LIFETIME":__import__("datetime").timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES","30"))),"REFRESH_TOKEN_LIFETIME":__import__("datetime").timedelta(days=int(os.getenv("REFRESH_TOKEN_DAYS","7"))),"ROTATE_REFRESH_TOKENS":True,"BLACKLIST_AFTER_ROTATION":True,"UPDATE_LAST_LOGIN":True}
AUTH_USER_MODEL="accounts.User"
FRONTEND_URL=os.getenv("FRONTEND_URL","http://localhost:5173")
DEFAULT_FROM_EMAIL=os.getenv("DEFAULT_FROM_EMAIL","noreply@scott.local")
EMAIL_BACKEND=os.getenv("EMAIL_BACKEND","django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST=os.getenv("EMAIL_HOST",""); EMAIL_PORT=int(os.getenv("EMAIL_PORT","587")); EMAIL_HOST_USER=os.getenv("EMAIL_HOST_USER",""); EMAIL_HOST_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD",""); EMAIL_USE_TLS=env_bool("EMAIL_USE_TLS",True); EMAIL_USE_SSL=env_bool("EMAIL_USE_SSL",False)
CODE_EXECUTION_ENABLED=env_bool("CODE_EXECUTION_ENABLED",DEBUG)
MAX_UPLOAD_SIZE=int(os.getenv("MAX_UPLOAD_SIZE","10485760"))
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage"
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG