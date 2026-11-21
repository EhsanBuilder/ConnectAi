import streamlit as st
import database
import ai
import api_client
import logger
import streamlit as st
import base64
from google_auth import create_google_flow
from calendar_service import create_calendar_event
import random
import json
import os
import time
import re
from urllib.parse import urlencode
from datetime import date, datetime, timedelta
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageOps
import requests
import finance_queries
from st_keyup import st_keyup













# =========================================================
# CONFIG
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SESSION_FILE = os.path.join(BASE_DIR, "session.json")
GOOGLE_STATE_FILE = os.path.join(BASE_DIR, "google_oauth_state.json")
CSS_FILE = os.path.join(BASE_DIR, "mobile.css")
IRAN_FLAG_FILE = os.path.join(
    BASE_DIR,
    "assets",
    "iran_lion_sun.webp"
)

st.set_page_config(
    page_title="ConnectAI",
    page_icon=None,
    layout="wide"
)
# =========================================================
# LOADING SCREEN
# =========================================================




# =========================================================
# DATABASE
# =========================================================

database.init_db()

try:
    database.init_finance_tables()
except Exception as e:
    logger.log_error(f"Finance init error: {e}")
    st.error(f"Finance database error: {e}")


# =========================================================
# CSS
# =========================================================

if os.path.exists(CSS_FILE):
    try:
        with open(CSS_FILE, "r", encoding="utf-8") as file:
            st.markdown(
                f"<style>{file.read()}</style>",
                unsafe_allow_html=True
            )
    except Exception as e:
        logger.log_error(f"Failed to load CSS: {e}")


# =========================================================
# DATABASE
# =========================================================

database.init_db()


# =========================================================
# SESSION FILE
# =========================================================

def save_session(user):
    try:
        with open(
            SESSION_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                user,
                file,
                ensure_ascii=False,
                indent=4
            )

        return True

    except Exception as e:
        logger.log_error(
            f"Failed to save session: {e}"
        )
        return False


def load_session():
    if not os.path.exists(SESSION_FILE):
        return None

    try:
        with open(
            SESSION_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception as e:
        logger.log_error(
            f"Failed to load session: {e}"
        )
        return None


def clear_session():
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

    except Exception as e:
        logger.log_error(
            f"Failed to clear session: {e}"
        )


# =========================================================
# GOOGLE OAUTH STATE
# =========================================================

def save_google_state(state, code_verifier=None):
    try:
        data = {
            "state": state,
            "code_verifier": code_verifier,
            "created_at": time.time()
        }

        with open(
            GOOGLE_STATE_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        return True

    except Exception as e:
        logger.log_error(
            f"Failed to save Google OAuth state: {e}"
        )
        return False


def load_google_state():
    if not os.path.exists(GOOGLE_STATE_FILE):
        return None

    try:
        with open(
            GOOGLE_STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        created_at = data.get("created_at", 0)

        if time.time() - created_at > 600:
            clear_google_state()
            return None

        return {
            "state": data.get("state"),
            "code_verifier": data.get("code_verifier")
        }

    except Exception as e:
        logger.log_error(
            f"Failed to load Google OAuth state: {e}"
        )
        return None


def clear_google_state():
    try:
        if os.path.exists(GOOGLE_STATE_FILE):
            os.remove(GOOGLE_STATE_FILE)

    except Exception as e:
        logger.log_error(
            f"Failed to clear Google OAuth state: {e}"
        )


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    saved_user = load_session()

    if saved_user:
        st.session_state.logged_in = True
        st.session_state.user = saved_user
    else:
        st.session_state.logged_in = False
        st.session_state.user = None


DEFAULTS = {
    "page": "dashboard",
    "settings_section": "profile",
    "workspace_id": None,
    "language": "🇺🇸 English",
    "ai_results": {},
    "editing_contact_id": None,
    "selected_contact_id": None,
    "mobile_menu_open": False,
    "google_state": None,
    "google_code_verifier": None,
    "calendar_contact_id": None,
    "calendar_form_open": False,
    "contact_selected_message": None,
    "greeting_seed": None
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# LANGUAGE
# =========================================================

def set_language(language_value):
    st.session_state.language = language_value
    st.rerun()


def load_iran_flag():
    if not os.path.exists(IRAN_FLAG_FILE):
        return None

    try:
        return Image.open(IRAN_FLAG_FILE)

    except Exception as e:
        logger.log_error(
            f"Failed to load Iran flag: {e}"
        )
        return None


language = st.session_state.language


# =========================================================
# LANGUAGE SELECTOR
# =========================================================

language_col = st.columns([8, 2])[1]

with language_col:

    if language == "🇮🇷 فارسی":

        flag_col, menu_col = st.columns(
            [1, 5],
            vertical_alignment="center"
        )

        with flag_col:
            iran_flag = load_iran_flag()

            if iran_flag:
                st.image(
                    iran_flag,
                    width=38
                )

        with menu_col:
            with st.popover(
                "فارسی ▾",
                use_container_width=True
            ):

                st.markdown("### 🌐 زبان")
                st.caption("انتخاب زبان")

                if st.button(
                    "🇺🇸 English",
                    use_container_width=True,
                    key="language_en_fa"
                ):
                    set_language("🇺🇸 English")

                if st.button(
                    "🇪🇸 Español",
                    use_container_width=True,
                    key="language_es_fa"
                ):
                    set_language("🇪🇸 Español")

    elif language == "🇺🇸 English":

        with st.popover(
            "🇺🇸 English ▾",
            use_container_width=True
        ):

            st.markdown("### 🌐 Language")
            st.caption("Choose your language")

            if st.button(
                "فارسی",
                use_container_width=True,
                key="language_fa_en"
            ):
                set_language("🇮🇷 فارسی")

            if st.button(
                "🇪🇸 Español",
                use_container_width=True,
                key="language_es_en"
            ):
                set_language("🇪🇸 Español")

    else:

        with st.popover(
            "🇪🇸 Español ▾",
            use_container_width=True
        ):

            st.markdown("### 🌐 Idioma")
            st.caption("Elige tu idioma")

            if st.button(
                "فارسی",
                use_container_width=True,
                key="language_fa_es"
            ):
                set_language("🇮🇷 فارسی")

            if st.button(
                "🇺🇸 English",
                use_container_width=True,
                key="language_en_es"
            ):
                set_language("🇺🇸 English")


if language == "🇮🇷 فارسی":
    current_language = "fa"
elif language == "🇺🇸 English":
    current_language = "en"
else:
    current_language = "es"


# =========================================================
# TEXTS
# =========================================================

texts = {

"title": {
    "fa": "ConnectAI",
    "en": "ConnectAI",
    "es": "ConnectAI"
},
    "total_contacts": {
        "fa": "کل مخاطبین",
        "en": "Total contacts",
        "es": "Total de contactos"
    },

    "business_contacts": {
        "fa": "مخاطبین کاری",
        "en": "Business contacts",
        "es": "Contactos de trabajo"
    },

    "today": {
        "fa": "امروز",
        "en": "Today",
        "es": "Hoy"
    },

    "overdue": {
        "fa": "عقب‌افتاده",
        "en": "Overdue",
        "es": "Atrasados"
    },
"nav_settings": {
    "fa": "تنظیمات",
    "en": "Settings",
    "es": "Configuración"
},
    "subtitle": {
        "fa": "دستیار هوشمند مدیریت مخاطبین",
        "en": "Smart Contact Management Assistant",
        "es": "Asistente inteligente de gestión de contactos"
    },
"settings": {
    "fa": "تنظیمات",
    "en": "Settings",
    "es": "Configuración"
},
    "login": {
        "fa": "🔐 ورود",
        "en": "🔐 Login",
        "es": "🔐 Iniciar sesión"
    },

    "register": {
        "fa": "📝 ثبت نام",
        "en": "📝 Register",
        "es": "📝 Registrarse"
    },

    "name": {
        "fa": "نام",
        "en": "Name",
        "es": "Nombre"
    },

    "email": {
        "fa": "ایمیل",
        "en": "Email",
        "es": "Correo electrónico"
    },

    "password": {
        "fa": "رمز عبور",
        "en": "Password",
        "es": "Contraseña"
    },

    "confirm_password": {
        "fa": "تکرار رمز عبور",
        "en": "Confirm Password",
        "es": "Confirmar contraseña"
    },

    "dashboard": {
        "fa": "📊 داشبورد",
        "en": "📊 Dashboard",
        "es": "📊 Panel"
    },

    "contacts": {
        "fa": "👥 مخاطبین",
        "en": "👥 Contacts",
        "es": "👥 Contactos"
    },

    "add_contact": {
        "fa": "➕ افزودن مخاطب",
        "en": "➕ Add Contact",
        "es": "➕ Añadir contacto"
    },

    "profile": {
        "fa": "👤 پروفایل",
        "en": "👤 Profile",
        "es": "👤 Perfil"
    },

    "activity": {
        "fa": "📜 فعالیت‌ها",
        "en": "📜 Activity",
        "es": "📜 Actividad"
    },

    "finance": {
        "fa": "💰 امور مالی",
        "en": "💰 Finance",
        "es": "💰 Finanzas"
    },

    "phone": {
        "fa": "شماره تلفن",
        "en": "Phone",
        "es": "Teléfono"
    },

    "note": {
        "fa": "یادداشت",
        "en": "Note",
        "es": "Nota"
    },

    "followup": {
        "fa": "تاریخ پیگیری",
        "en": "Follow-up",
        "es": "Seguimiento"
    },

    "budget": {
        "fa": "بودجه",
        "en": "Budget",
        "es": "Presupuesto"
    },

    "vip": {
        "fa": " VIP",
        "en": " VIP",
        "es": " VIP"
    },

    "edit": {
        "fa": "✏️ ویرایش",
        "en": "✏️ Edit",
        "es": "✏️ Editar"
    },

    "delete": {
        "fa": "🗑️ حذف",
        "en": "🗑️ Delete",
        "es": "🗑️ Eliminar"
    },

    "save": {
        "fa": "💾 ذخیره",
        "en": "💾 Save",
        "es": "💾 Guardar"
    },

    "cancel": {
        "fa": "❌ لغو",
        "en": "❌ Cancel",
        "es": "❌ Cancelar"
    },

    "smart_analysis": {
        "fa": "🤖 تحلیل هوشمند",
        "en": "🤖 Smart Analysis",
        "es": "🤖 Análisis inteligente"
    },

    "ai_loading": {
        "fa": "🤖 در حال تحلیل...",
        "en": "🤖 Analyzing...",
        "es": "🤖 Analizando..."
    },

    "ai_result": {
        "fa": "🤖 نتیجه تحلیل",
        "en": "🤖 AI Result",
        "es": "🤖 Resultado de IA"
    },



"logout": {
    "fa": "خروج",
    "en": "Logout",
    "es": "Cerrar sesión"
},

    "login_success": {
        "fa": "ورود موفق بود ✅",
        "en": "Login successful ✅",
        "es": "Inicio de sesión exitoso ✅"
    },

    "login_error": {
        "fa": "ایمیل یا رمز اشتباه است ❌",
        "en": "Wrong email or password ❌",
        "es": "Correo electrónico o contraseña incorrectos ❌"
    },

    "register_success": {
        "fa": "حساب ساخته شد 🎉",
        "en": "Account created 🎉",
        "es": "Cuenta creada 🎉"
    },

    "contact_added": {
        "fa": "مخاطب اضافه شد ✅",
        "en": "Contact added ✅",
        "es": "Contacto añadido ✅"
    },

    "contact_updated": {
        "fa": "مخاطب بروزرسانی شد ✅",
        "en": "Contact updated ✅",
        "es": "Contacto actualizado ✅"
    },

    "google_login": {
        "fa": "🔵 ورود با Google",
        "en": "🔵 Sign in with Google",
        "es": "🔵 Iniciar sesión con Google"
    },

    "continue_google": {
        "fa": "🔵 ادامه با Google",
        "en": "🔵 Continue with Google",
        "es": "🔵 Continuar con Google"
    },

    "terms": {
        "fa": "☑️ قوانین و شرایط استفاده را می‌پذیرم",
        "en": "☑️ I accept the terms and conditions",
        "es": "☑️ Acepto los términos y condiciones"
    },

    "name_required": {
        "fa": "نام را وارد کن.",
        "en": "Please enter your name.",
        "es": "Introduce tu nombre."
    },

    "email_required": {
        "fa": "ایمیل را وارد کن.",
        "en": "Please enter your email.",
        "es": "Introduce tu correo electrónico."
    },

    "password_required": {
        "fa": "رمز عبور را وارد کن.",
        "en": "Please enter your password.",
        "es": "Introduce tu contraseña."
    },

    "passwords_mismatch": {
        "fa": "رمزها یکی نیستند.",
        "en": "Passwords do not match.",
        "es": "Las contraseñas no coinciden."
    },

    "terms_required": {
        "fa": "باید قوانین را قبول کنی.",
        "en": "You must accept the terms.",
        "es": "Debes aceptar los términos."
    },

    "search": {
        "fa": "🔎 جستجو",
        "en": "🔎 Search",
        "es": "🔎 Buscar"
    },

    "today_suggestions": {
        "fa": "🤖 پیشنهادهای امروز",
        "en": "🤖 Today's Suggestions",
        "es": "🤖 Sugerencias de hoy"
    },

    "no_followups": {
        "fa": "✅ امروز پیگیری خاصی وجود ندارد.",
        "en": "✅ No important follow-ups for today.",
        "es": "✅ No hay seguimientos importantes para hoy."
    },

    "contacts_count": {
        "fa": "تعداد نتایج: {count}",
        "en": "Results: {count}",
        "es": "Resultados: {count}"
    },

    "no_contact_found": {
        "fa": "مخاطبی پیدا نشد.",
        "en": "No contacts found.",
        "es": "No se encontraron contactos."
    },









    "latest_contacts": {
        "fa": "آخرین مخاطبین",
        "en": "Latest Contacts",
        "es": "Contactos recientes"
    },

    "no_contacts_yet": {
        "fa": "هنوز مخاطبی وجود ندارد.",
        "en": "No contacts yet.",
        "es": "Aún no hay contactos."
    },

    "view_contact": {
        "fa": "مشاهده مخاطب",
        "en": "View Contact",
        "es": "Ver contacto"
    },

    "contact_type": {
        "fa": "نوع مخاطب",
        "en": "Contact Type",
        "es": "Tipo de contacto"
    },

    "personal": {
        "fa": "شخصی",
        "en": "Personal",
        "es": "Personal"
    },

    "work": {
        "fa": "کاری",
        "en": "Work",
        "es": "Trabajo"
    },

    "ai_analyze": {
        "fa": "🤖 تحلیل",
        "en": "🤖 Analyze",
        "es": "🤖 Analizar"
    },



    "new_meeting": {
        "fa": "📅 جلسه جدید",
        "en": "📅 New Meeting",
        "es": "📅 Nueva reunión"
    },

    "meeting_for": {
        "fa": "📅 ساخت جلسه برای {name}",
        "en": "📅 Create meeting for {name}",
        "es": "📅 Crear reunión para {name}"
    },

    "meeting_title": {
        "fa": "عنوان جلسه",
        "en": "Meeting Title",
        "es": "Título de la reunión"
    },

    "meeting_date": {
        "fa": "تاریخ",
        "en": "Date",
        "es": "Fecha"
    },

    "start_time": {
        "fa": "ساعت شروع",
        "en": "Start Time",
        "es": "Hora de inicio"
    },

    "end_time": {
        "fa": "ساعت پایان",
        "en": "End Time",
        "es": "Hora de finalización"
    },

    "description": {
        "fa": "توضیحات",
        "en": "Description",
        "es": "Descripción"
    },

    "create_meeting": {
        "fa": "📅 ساخت جلسه",
        "en": "📅 Create Meeting",
        "es": "📅 Crear reunión"
    },

    "creating_meeting": {
        "fa": "📅 در حال ساخت جلسه در Google Calendar...",
        "en": "📅 Creating meeting in Google Calendar...",
        "es": "📅 Creando reunión en Google Calendar..."
    },

    "meeting_created": {
        "fa": "✅ جلسه با موفقیت در Google Calendar ساخته شد.",
        "en": "✅ Meeting created successfully in Google Calendar.",
        "es": "✅ Reunión creada correctamente en Google Calendar."
    },

    "open_calendar": {
        "fa": "🔗 باز کردن جلسه در Google Calendar",
        "en": "🔗 Open Meeting in Google Calendar",
        "es": "🔗 Abrir reunión en Google Calendar"
    },

    "meeting_failed": {
        "fa": "❌ ساخت جلسه ناموفق بود.",
        "en": "❌ Failed to create meeting.",
        "es": "❌ No se pudo crear la reunión."
    },

    "end_time_error": {
        "fa": "❌ ساعت پایان باید بعد از ساعت شروع باشد.",
        "en": "❌ End time must be after start time.",
        "es": "❌ La hora de finalización debe ser posterior a la hora de inicio."
    },

    "unknown_error": {
        "fa": "خطای نامشخص",
        "en": "Unknown error",
        "es": "Error desconocido"
    },

    "edit_contact": {
        "fa": "✏️ ویرایش مخاطب: {name}",
        "en": "✏️ Edit Contact: {name}",
        "es": "✏️ Editar contacto: {name}"
    },

    "save_changes": {
        "fa": "💾 ذخیره تغییرات",
        "en": "💾 Save Changes",
        "es": "💾 Guardar cambios"
    },

    "edit_failed": {
        "fa": "ویرایش مخاطب ناموفق بود: {error}",
        "en": "Failed to edit contact: {error}",
        "es": "No se pudo editar el contacto: {error}"
    },

    "add_contact_name_required": {
        "fa": "نام مخاطب را وارد کن.",
        "en": "Please enter the contact name.",
        "es": "Introduce el nombre del contacto."
    },

    "add_contact_failed": {
        "fa": "افزودن مخاطب ناموفق بود: {error}",
        "en": "Failed to add contact: {error}",
        "es": "No se pudo añadir el contacto: {error}"
    },

    "no_activity": {
        "fa": "هنوز فعالیتی ثبت نشده است.",
        "en": "No activity has been recorded yet.",
        "es": "Aún no hay actividad registrada."
    },

    "activity_error": {
        "fa": "خطا در نمایش فعالیت‌ها: {error}",
        "en": "Error displaying activity: {error}",
        "es": "Error al mostrar la actividad: {error}"
    },

    "contact_selected": {
        "fa": "💬 مخاطب «{name}» انتخاب شد.",
        "en": "💬 Contact “{name}” selected.",
        "es": "💬 Contacto «{name}» seleccionado."
    },

    "account_info": {
        "fa": "⚙️ اطلاعات حساب",
        "en": "⚙️ Account Information",
        "es": "⚙️ Información de la cuenta"
    },

    "plan": {
        "fa": "پلن",
        "en": "Plan",
        "es": "Plan"
    },

    "save_name": {
        "fa": "💾 ذخیره نام",
        "en": "💾 Save Name",
        "es": "💾 Guardar nombre"
    },

    "name_updated": {
        "fa": "نام با موفقیت بروزرسانی شد ✅",
        "en": "Name updated successfully ✅",
        "es": "Nombre actualizado correctamente ✅"
    },

    "profile_update_failed": {
        "fa": "بروزرسانی پروفایل ناموفق بود: {error}",
        "en": "Profile update failed: {error}",
        "es": "No se pudo actualizar el perfil: {error}"
    },

    "registration_failed": {
        "fa": "ثبت نام انجام نشد ❌",
        "en": "Registration failed ❌",
        "es": "No se pudo completar el registro ❌"
    },

    "user_info_missing": {
        "fa": "اطلاعات کاربر دریافت نشد ❌",
        "en": "User information was not received ❌",
        "es": "No se recibió la información del usuario ❌"
    },

    "registration_error": {
        "fa": "خطا در ثبت نام: {error}",
        "en": "Registration error: {error}",
        "es": "Error de registro: {error}"
    },

    "login_error_exception": {
        "fa": "خطا در ورود: {error}",
        "en": "Login error: {error}",
        "es": "Error al iniciar sesión: {error}"
    },

    "google_security_failed": {
        "fa": "ساخت اطلاعات امنیتی Google ناموفق بود ❌",
        "en": "Failed to create Google security information ❌",
        "es": "No se pudo crear la información de seguridad de Google ❌"
    },

    "google_security_save_failed": {
        "fa": "ذخیره اطلاعات امنیتی Google ناموفق بود ❌",
        "en": "Failed to save Google security information ❌",
        "es": "No se pudo guardar la información de seguridad de Google ❌"
    },

    "google_state_not_found": {
        "fa": "اطلاعات امنیتی ورود Google پیدا نشد ❌",
        "en": "Google login security information was not found ❌",
        "es": "No se encontró la información de seguridad del inicio de sesión de Google ❌"
    },

    "google_state_mismatch": {
        "fa": "خطای امنیتی در ورود با Google ❌",
        "en": "Google login security error ❌",
        "es": "Error de seguridad al iniciar sesión con Google ❌"
    },

    "google_verifier_missing": {
        "fa": "اطلاعات امنیتی Google کامل نیست ❌",
        "en": "Google security information is incomplete ❌",
        "es": "La información de seguridad de Google está incompleta ❌"
    },

    "google_credentials_failed": {
        "fa": "دریافت اطلاعات Google ناموفق بود ❌",
        "en": "Failed to receive Google credentials ❌",
        "es": "No se pudieron obtener las credenciales de Google ❌"
    },

    "google_token_failed": {
        "fa": "دریافت توکن Google ناموفق بود ❌",
        "en": "Failed to receive Google access token ❌",
        "es": "No se pudo obtener el token de acceso de Google ❌"
    },

    "google_userinfo_failed": {
        "fa": "دریافت اطلاعات Google ناموفق بود ❌",
        "en": "Failed to receive Google user information ❌",
        "es": "No se pudo obtener la información del usuario de Google ❌"
    },

    "google_email_missing": {
        "fa": "ایمیل حساب Google دریافت نشد ❌",
        "en": "Google account email was not received ❌",
        "es": "No se recibió el correo electrónico de la cuenta de Google ❌"
    },

    "google_login_failed": {
        "fa": "ورود با Google انجام نشد ❌",
        "en": "Google login failed ❌",
        "es": "No se pudo iniciar sesión con Google ❌"
    },

    "google_access_save_failed": {
        "fa": "ذخیره دسترسی Google ناموفق بود ❌",
        "en": "Failed to save Google access ❌",
        "es": "No se pudo guardar el acceso de Google ❌"
    },

    "google_login_success": {
        "fa": "ورود با Google با موفقیت انجام شد ✅",
        "en": "Google login successful ✅",
        "es": "Inicio de sesión con Google exitoso ✅"
    },

    "google_connection_error": {
        "fa": "خطا در اتصال Google: {error}",
        "en": "Google connection error: {error}",
        "es": "Error de conexión con Google: {error}"
    },

    "google_login_error": {
        "fa": "خطا در ورود با Google: {error}",
        "en": "Google login error: {error}",
        "es": "Error al iniciar sesión con Google: {error}"
    },

    "vip_update_failed": {
        "fa": "تغییر VIP ناموفق بود: {error}",
        "en": "VIP update failed: {error}",
        "es": "No se pudo actualizar el estado VIP: {error}"
    },

    "ai_analysis_error": {
        "fa": "خطا در تحلیل: {error}",
        "en": "Analysis error: {error}",
        "es": "Error de análisis: {error}"
    },

    "ai_contact_prompt": {
        "fa": """این مشتری را تحلیل کن.

1- وضعیت مشتری چیست؟
2- احتمال خرید یا همکاری چقدر است؟
3- چه کاری پیشنهاد می‌کنی؟
4- نکته مهم اطلاعات او چیست؟

کوتاه و کاربردی جواب بده.""",

        "en": """Analyze this customer.

1- What is the customer's current status?
2- How likely are they to buy or collaborate?
3- What action do you recommend?
4- What is the most important information about them?

Keep the answer short and practical.""",

        "es": """Analiza a este cliente.

1- ¿Cuál es el estado actual del cliente?
2- ¿Qué probabilidad hay de compra o colaboración?
3- ¿Qué acción recomiendas?
4- ¿Cuál es la información más importante sobre él?

Responde de forma breve y práctica."""
    },



    "calendar_error": {
        "fa": "❌ خطا در ساخت جلسه: {error}",
        "en": "❌ Calendar error: {error}",
        "es": "❌ Error al crear la reunión: {error}"
    },

    "meeting_default_title": {
        "fa": "جلسه با {name}",
        "en": "Meeting with {name}",
        "es": "Reunión con {name}"
    },

    "meeting_default_description": {
        "fa": "جلسه با {name}",
        "en": "Meeting with {name}",
        "es": "Reunión con {name}"
    },
    "empty_title": {
        "fa": "هنوز مخاطبی نداری",
        "en": "You don't have any contacts yet",
        "es": "Todavía no tienes contactos"
    },

    "empty_text": {
        "fa": "اولین مخاطبت رو اضافه کن تا پیگیری‌ها و پیشنهادهای امروز شروع بشه.",
        "en": "Add your first contact to start getting follow-ups and daily suggestions.",
        "es": "Añade tu primer contacto para empezar a recibir seguimientos y sugerencias diarias."
    },

    "empty_button": {
        "fa": "➕ اولین مخاطبت رو اضافه کن",
        "en": "➕ Add your first contact",
        "es": "➕ Añade tu primer contacto"
    },
"footer": {
    "fa": "ConnectAI — مدیریت هوشمند مخاطبین",
    "en": "ConnectAI — Smart Contact Management",
    "es": "ConnectAI — Gestión inteligente de contactos"
}
}


# =========================================================
# TRANSLATION
# =========================================================
AVATAR_DIR = os.path.join(
    BASE_DIR,
    "avatars"
)

os.makedirs(
    AVATAR_DIR,
    exist_ok=True
)
def t(key):
    return texts[key][current_language]


def tf(key, **kwargs):
    return t(key).format(**kwargs)



def load_svg_icon(path, size=20):
    with open(path, "r", encoding="utf-8") as file:
        svg = file.read()

    encoded = base64.b64encode(
        svg.encode("utf-8")
    ).decode("utf-8")

    return f"""
        <img
            src="data:image/svg+xml;base64,{encoded}"
            width="{size}"
            height="{size}"
            style="vertical-align: middle;"
        />
    """
# =========================================================
# GREETING
# =========================================================

GREETINGS = {
    "morning": {
        "fa": [
            "صبح بخیر {name} ☀️",
            "سلام {name}، صبح‌ات بخیر! روز خوبی داشته باشی",
            "صبح‌ات بخیر {name}، آماده‌ای برای یک روز پرانرژی؟",
        ],
        "en": [
            "Good morning, {name} ☀️",
            "Good morning, {name}! Have a great day",
            "Morning, {name}! Ready for an energetic day?",
        ],
        "es": [
            "Buenos días, {name} ☀️",
            "¡Buenos días, {name}! Que tengas un gran día",
            "¡Buen día, {name}! ¿Listo para una jornada llena de energía?",
        ],
    },
    "noon": {
        "fa": [
            "ظهر بخیر {name} 🌤️",
            "سلام {name}، ظهرت بخیر! یک استراحت کوتاه یادت نره",
            "ظهر بخیر {name}، امیدوارم روزت تا اینجا خوب بوده باشه",
        ],
        "en": [
            "Good afternoon, {name} 🌤️",
            "Good afternoon, {name}! Don't forget a short break",
            "Hello, {name}! Hope your day is going well so far",
        ],
        "es": [
            "Buenas tardes, {name} 🌤️",
            "¡Buenas tardes, {name}! No olvides un pequeño descanso",
            "¡Hola, {name}! Espero que tu día vaya bien hasta ahora",
        ],
    },
    "evening": {
        "fa": [
            "عصر بخیر {name} 🌇",
            "سلام {name}، عصرت بخیر! خسته نباشی",
            "عصر بخیر {name}، بریم سراغ پیگیری‌های امروز؟",
        ],
        "en": [
            "Good evening, {name} 🌇",
            "Good evening, {name}! Nice work today",
            "Good evening, {name}! Shall we check today's follow-ups?",
        ],
        "es": [
            "Buenas tardes, {name} 🌇",
            "¡Buenas tardes, {name}! Buen trabajo hoy",
            "¡Buenas tardes, {name}! ¿Revisamos los seguimientos de hoy?",
        ],
    },
    "night": {
        "fa": [
            "شب بخیر {name} 🌙",
            "سلام {name}، شبت بخیر! امیدوارم روز خوبی داشته باشی",
            "شب بخیر {name}، یک نگاه آخر به کارهای امروز بنداز",
        ],
        "en": [
            "Good night, {name} 🌙",
            "Good evening, {name}! I hope you had a good day",
            "Good night, {name}! Take a last look at today's tasks",
        ],
        "es": [
            "Buenas noches, {name} 🌙",
            "¡Buenas noches, {name}! Espero que hayas tenido un buen día",
            "Buenas noches, {name}. Echa un último vistazo a las tareas de hoy",
        ],
    },
}


def get_time_period(hour):
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 16:
        return "noon"
    if 16 <= hour < 20:
        return "evening"
    return "night"


def get_greeting(user, lang):
    period = get_time_period(datetime.now().hour)

    # نام کوچک کاربر (اگر نام وجود نداشت یا فقط نام پیش‌فرض گوگل بود، بدون نام)
    name = ""
    if user:
        full_name = (user.get("name") or "").strip()
        if full_name and full_name != "Google User":
            name = full_name.split()[0]

    # یک عدد تصادفی فقط یک‌بار در هر ورود ساخته می‌شود
    # تا با هر کلیک روی برنامه، جمله عوض نشود
    if st.session_state.get("greeting_seed") is None:
        st.session_state.greeting_seed = random.randint(0, 9999)

    templates = GREETINGS[period][lang]
    template = templates[st.session_state.greeting_seed % len(templates)]

    if name:
        return template.format(name=name)

    # حالت بدون نام: جای نام را همراه با ویرگول کنارش حذف می‌کنیم
    for part in ("، {name}", ", {name}", " {name}"):
        template = template.replace(part, "")

    return template.replace("{name}", "")
# =========================================================
# AVATAR
# =========================================================
def save_avatar(user_id, uploaded_file):

    if uploaded_file is None:
        return ""

    try:

        file_extension = uploaded_file.name.split(".")[-1]

        file_path = os.path.join(
            AVATAR_DIR,
            f"user_{user_id}.{file_extension}"
        )

        with open(
            file_path,
            "wb"
        ) as file:

            file.write(
                uploaded_file.getbuffer()
            )

        return file_path


    except Exception as e:

        logger.log_error(
            f"Avatar save error: {e}"
        )

        return ""

def show_avatar(user, size=60):
    import random
    import hashlib

    avatar = user.get("avatar", "") if user else ""

    if avatar and os.path.exists(avatar):
        try:
            image = Image.open(avatar)
            st.image(image, width=size)
            return
        except Exception as e:
            logger.log_error(f"Failed to load avatar: {e}")

    name = (
        user.get("name", "").strip()
        if user else ""
    )
    initial = name[0].upper() if name else "?"

    colors = [
        "#667eea",  # بنفش
        "#e74c3c",  # قرمز
        "#27ae60",  # سبز
        "#f39c12",  # نارنجی
        "#e84393",  # صورتی
    ]

    user_id = str(user.get("id", name)) if user else "guest"
    color_index = int(
        hashlib.md5(user_id.encode()).hexdigest(), 16
    ) % len(colors)
    color = colors[color_index]

    st.markdown(
        f"""
        <div style="
            width:{size}px;
            height:{size}px;
            border-radius:50%;
            background:{color};
            display:flex;
            align-items:center;
            justify-content:center;
            color:white;
            font-size:{size // 2}px;
            font-weight:bold;
        ">
            {initial}
        </div>
        """,
        unsafe_allow_html=True
    )



# =========================================================
# REGISTER
# =========================================================

def register_user(name, email, password):

    try:

        result = api_client.register(
            name,
            email,
            password
        )

        if result.get("status") != "success":
            st.error(
                result.get(
                    "message",
                    t("registration_failed")
                )
            )
            return

        user_data = result.get("user")

        if not user_data:
            st.error(t("user_info_missing"))
            return

        user_id = user_data["id"]

        workspace_id = (
            database.get_or_create_default_workspace(
                user_id
            )
        )

        user = {
            "id": user_id,
            "name": name.strip(),
            "email": email.strip().lower(),
            "plan": "free"
        }

        st.session_state.logged_in = True
        st.session_state.user = user
        st.session_state.workspace_id = workspace_id

        save_session(user)

        st.success(t("register_success"))
        st.rerun()

    except Exception as e:

        logger.log_error(
            f"Registration error: {e}"
        )

        st.error(
            tf(
                "registration_error",
                error=e
            )
        )


# =========================================================
# GOOGLE CALLBACK
# =========================================================

def handle_google_callback():

    if st.session_state.get("logged_in", False):
        return

    code = st.query_params.get("code")
    state = st.query_params.get("state")

    if not code:
        return

    saved_state = st.session_state.get("google_state")
    saved_code_verifier = (
        st.session_state.get("google_code_verifier")
    )

    saved_data = load_google_state()
    print("GOOGLE STATE FILE:")
    print(saved_data)
    if saved_data:

        if not saved_state:
            saved_state = saved_data.get("state")

        if not saved_code_verifier:
            saved_code_verifier = saved_data.get(
                "code_verifier"
            )

    if not saved_state:
        st.error(t("google_state_not_found"))
        clear_google_state()
        st.query_params.clear()
        return

    if state != saved_state:
        st.error(t("google_state_mismatch"))
        clear_google_state()
        st.query_params.clear()
        return

    if not saved_code_verifier:
        st.error(t("google_verifier_missing"))
        clear_google_state()
        st.query_params.clear()
        return

    try:

        flow = create_google_flow()
        flow.code_verifier = saved_code_verifier

        authorization_response = (
            "http://localhost:8501/?"
            + urlencode(
                {
                    "code": code,
                    "state": state
                }
            )
        )

        flow.fetch_token(
            authorization_response=authorization_response
        )

        credentials = flow.credentials

        if not credentials or not credentials.token:
            st.error(t("google_token_failed"))
            clear_google_state()
            st.query_params.clear()
            return

        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={
                "Authorization": f"Bearer {credentials.token}"
            },
            timeout=10
        )

        if response.status_code != 200:
            st.error(t("google_userinfo_failed"))
            clear_google_state()
            st.query_params.clear()
            return

        google_user = response.json()

        google_name = (
            google_user.get("name")
            or google_user.get("given_name")
            or "Google User"
        )

        google_email = google_user.get("email")

        if not google_email:
            st.error(t("google_email_missing"))
            clear_google_state()
            st.query_params.clear()
            return

        result = api_client.google_login(
            google_name,
            google_email
        )

        if result.get("status") != "success":
            st.error(
                result.get(
                    "message",
                    t("google_login_failed")
                )
            )
            clear_google_state()
            st.query_params.clear()
            return

        google_user_data = result.get("user")

        if not google_user_data:
            st.error(t("user_info_missing"))
            clear_google_state()
            st.query_params.clear()
            return

        workspace_id = result.get("workspace_id")

        if not workspace_id:
            workspace_id = (
                database.get_or_create_default_workspace(
                    google_user_data["id"]
                )
            )

        credentials_saved = database.save_google_credentials(
            user_id=google_user_data["id"],
            workspace_id=workspace_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=credentials.scopes or []
        )

        if not credentials_saved:
            st.error(t("google_access_save_failed"))
            clear_google_state()
            st.query_params.clear()
            return

        st.session_state.logged_in = True
        st.session_state.user = google_user_data
        st.session_state.workspace_id = workspace_id

        save_session(google_user_data)

        clear_google_state()

        st.session_state.google_state = None
        st.session_state.google_code_verifier = None

        st.query_params.clear()

        st.success(t("google_login_success"))
        st.rerun()

    except Exception as e:

        logger.log_error(
            f"Google OAuth error: {e}"
        )

        clear_google_state()

        st.error(
            tf(
                "google_connection_error",
                error=e
            )
        )


# =========================================================
# GOOGLE CALLBACK
# =========================================================

handle_google_callback()




# =========================================================
# LOGIN / REGISTER
# =========================================================

if not st.session_state.logged_in:

    tab_login, tab_register = st.tabs(
        [
            t("login").replace("🔐 ", ""),
            t("register").replace("📝 ", "")
        ]
    )


    # LOGIN TAB
    with tab_login:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:2rem; font-weight:700;">
                    {t("login").replace("🔐 ", "")}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )




        login_email = st.text_input(
            t("email"),
            key="login_email"
        )

        login_password = st.text_input(
            t("password"),
            type="password",
            key="login_password"
        )

        if st.button(
            t("login").replace("🔐 ", ""),
            use_container_width=True,
            key="normal_login_button"
        ):

            try:
                result = api_client.login(
                    login_email,
                    login_password
                )

                if result.get("status") == "success":

                    logged_user = result["user"]

                    workspace_id = (
                        database.get_or_create_default_workspace(
                            logged_user["id"]
                        )
                    )

                    st.session_state.logged_in = True
                    st.session_state.user = logged_user
                    st.session_state.workspace_id = workspace_id

                    save_session(logged_user)

                    st.success(t("login_success"))
                    st.rerun()

                else:
                    st.error(
                        result.get("message", t("login_error"))
                    )

            except Exception as e:
                logger.log_error(f"Login error: {e}")
                st.error(tf("login_error_exception", error=e))

        if st.button(
            t("google_login"),
            use_container_width=True,
            key="google_login_button"
        ):

            try:
                flow = create_google_flow()

                authorization_url, state = (
                    flow.authorization_url(
                        access_type="offline",
                        include_granted_scopes="true",
                        prompt="consent"
                    )
                )

                code_verifier = getattr(
                    flow, "code_verifier", None
                )

                if not code_verifier:
                    st.error(t("google_security_failed"))

                else:
                    st.session_state.google_state = state
                    st.session_state.google_code_verifier = code_verifier

                    if save_google_state(state, code_verifier):
                        st.link_button(
                            t("continue_google"),
                            authorization_url,
                            use_container_width=True
                        )
                    else:
                        st.error(t("google_security_save_failed"))

            except Exception as e:
                logger.log_error(
                    f"Google authorization error: {e}"
                )
                st.error(tf("google_login_error", error=e))

    # REGISTER TAB
    with tab_register:

        st.title(t("register"))

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'{load_svg_icon(os.path.join(BASE_DIR, "icons", "user.svg"), 20)}'
            f'<span>{t("name")}</span></div>',
            unsafe_allow_html=True
        )

        reg_name = st.text_input(
            t("name"),
            label_visibility="collapsed",
            key="reg_name"
        )

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span>✉️</span><span>{t("email")}</span></div>',
            unsafe_allow_html=True
        )

        reg_email = st.text_input(
            t("email"),
            label_visibility="collapsed",
            key="reg_email"
        )

        reg_password = st.text_input(
            t("password"),
            type="password",
            key="reg_password"
        )

        reg_confirm = st.text_input(
            t("confirm_password"),
            type="password",
            key="reg_confirm"
        )

        terms = st.checkbox(
            t("terms"),
            key="terms_checkbox"
        )

        if st.button(
            t("register").replace("📝 ", ""),
            use_container_width=True,
            key="register_button"
        ):

            if not reg_name.strip():
                st.warning(t("name_required"))

            elif not reg_email.strip():
                st.warning(t("email_required"))

            elif not reg_password:
                st.warning(t("password_required"))

            elif reg_password != reg_confirm:
                st.error(t("passwords_mismatch"))

            elif not terms:
                st.warning(t("terms_required"))

            else:
                register_user(
                    reg_name,
                    reg_email,
                    reg_password
                )

    st.stop()







    with tab_register:
        st.title(t("register"))

        # Name field
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'{load_svg_icon(os.path.join(BASE_DIR, "icons", "log-in.svg"), 20)}'
            f'<span>{t("name")}</span></div>',
            unsafe_allow_html=True
        )

        reg_name = st.text_input(
            t("name"),
            label_visibility="collapsed",
            key="reg_name"
        )

        # Email field
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span>✉️</span><span>{t("email")}</span></div>',
            unsafe_allow_html=True
        )

        reg_email = st.text_input(
            t("email"),
            label_visibility="collapsed",
            key="reg_email"
        )

        reg_password = st.text_input(
            t("password"),
            type="password",
            key="reg_password"
        )

        reg_confirm = st.text_input(
            t("confirm_password"),
            type="password",
            key="reg_confirm"
        )

        terms = st.checkbox(
            t("terms"),
            key="terms_checkbox"
        )

        if st.button(
            t("register"),
            use_container_width=True,
            key="register_button"
        ):
            if not reg_name.strip():
                st.warning(t("name_required"))
            elif not reg_email.strip():
                st.warning(t("email_required"))
            elif not reg_password:
                st.warning(t("password_required"))
            elif reg_password != reg_confirm:
                st.error(t("passwords_mismatch"))
            elif not terms:
                st.warning(t("terms_required"))
            else:
                register_user(
                    reg_name,
                    reg_email,
                    reg_password
                )

    st.stop()

# =========================================================
# CURRENT USER
# =========================================================

# =========================================================
# SESSION / CURRENT USER
# Replace the corresponding section in app.py with this block.
# =========================================================

user = st.session_state.user

if not user:
    st.session_state.logged_in = False
    st.rerun()


# =========================================================
# INTERNAL WORKSPACE
# =========================================================

if not st.session_state.workspace_id and user:
    print("CURRENT USER:", user)
    print("USER ID:", user["id"])

    st.session_state.workspace_id = database.get_or_create_default_workspace(
        user["id"]
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    show_avatar(user, 65)
    st.write(f"**{user.get('name', '')}**")
    st.caption(user.get("email", ""))
    st.divider()

    current_page = st.session_state.get("page", "dashboard")

    menu_items = [
        ("dashboard", "nav_dashboard", ":material/dashboard:"),
        ("contacts", "nav_contacts", ":material/business_center:"),
        ("add_contact", "nav_add_contact", ":material/person_add:"),
        ("activity", "nav_activity", ":material/calendar_month:"),
        ("finance", "nav_finance", ":material/account_balance_wallet:"),
        ("settings", "nav_settings", ":material/settings:"),

    ]

    for page_name, button_key, icon_name in menu_items:
        label = t(page_name)
        label = re.sub(r"^[^\w\s]+\s*", "", label)

        if st.button(
            label,
            icon=icon_name,
            use_container_width=True,
            key=button_key,
            type="primary" if current_page == page_name else "secondary",
        ):
            st.session_state.page = page_name
            st.session_state.editing_contact_id = None
            st.rerun()

    st.divider()

    if st.button(
        t("logout"),
        icon=":material/logout:",
        use_container_width=True,
        key="logout_button",
    ):
        clear_session()
        clear_google_state()
        st.session_state.greeting_seed = None
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.workspace_id = None
        st.session_state.google_state = None
        st.session_state.google_code_verifier = None
        st.session_state.calendar_contact_id = None
        st.session_state.calendar_form_open = False
        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.title(t("title"))
st.caption(t("subtitle"))


# =========================================================
# DASHBOARD
# =========================================================

if st.session_state.page == "dashboard":
    with st.container(border=True):
        st.subheader(get_greeting(user, current_language))

    stats = database.get_dashboard_stats(
        user["id"],
        st.session_state.workspace_id,
    )
    contacts = database.get_contacts(
        user["id"],
        st.session_state.workspace_id,
    )

    if not contacts:
        st.markdown(f"### {t('empty_title')}")
        st.write(t("empty_text"))

        if st.button(
            t("empty_button"),
            type="primary",
            use_container_width=True,
            key="empty_add_contact",
        ):
            st.session_state.page = "add_contact"
            st.rerun()

        st.divider()

    # Dashboard statistics
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            f":material/groups: {t('total_contacts')}",
            stats["total"],
        )

    with c2:
        st.metric(
            f":material/star: {t('vip')}",
            stats["vip"],
        )

    with c3:
        st.metric(
            f":material/business_center: {t('business_contacts')}",
            stats["work"],
        )

    with c4:
        st.metric(
            f":material/calendar_month: {t('today')}",
            stats["today"],
        )

    with c5:
        st.metric(
            f":material/warning: {t('overdue')}",
            stats["late"],
        )

    st.divider()
    st.subheader(t("today_suggestions"))

    contacts = database.get_contacts(
        user["id"],
        st.session_state.workspace_id,
    )
    today = date.today()
    followups = []

    for contact in contacts:
        followup = contact["followup"]

        if not followup:
            continue

        try:
            followup_date = date.fromisoformat(followup)
        except (ValueError, TypeError):
            continue

        if followup_date <= today:
            followups.append(contact)

    if not followups:
        st.success(t("no_followups"))
    else:
        for contact in followups[:5]:
            with st.container(border=True):
                st.write(f"👤 **{contact['name']}**")
                st.caption(
                    f"📅 {t('followup')}: {contact['followup']}"
                )

                if st.button(
                    t("view_contact"),
                    key=f"dash_{contact['id']}",
                ):
                    st.session_state.selected_contact_id = contact["id"]
                    st.session_state.contact_selected_message = contact["name"]
                    st.session_state.page = "contacts"
                    st.rerun()

    st.divider()
    st.subheader(t("latest_contacts"))

    if not contacts:
        st.info(t("no_contacts_yet"))
    else:
        for contact in contacts[:10]:
            col1, col2, col3 = st.columns([4, 3, 1])

            with col1:
                vip = "⭐" if contact["vip"] else ""
                st.write(f"**{contact['name']}** {vip}")

            with col2:
                st.caption(contact["phone"])

            with col3:
                if st.button("👁️", key=f"view_{contact['id']}"):
                    st.session_state.selected_contact_id = contact["id"]
                    st.session_state.contact_selected_message = contact["name"]
                    st.session_state.page = "contacts"
                    st.rerun()


# =========================================================
# CONTACTS
# =========================================================

elif st.session_state.page == "contacts":
    st.header(t("contacts"))
    st.caption("مخاطبین خود را جستجو و مدیریت کنید.")

    search = st_keyup(
        "🔎 جستجوی مخاطب",
        placeholder="نام، شماره یا ایمیل...",
        debounce=300,
        key="contact_search",
    )

    contacts = database.get_contacts(
        user_id=user["id"],
        workspace_id=st.session_state.workspace_id,
        search=search.strip(),
    )

    st.caption(f"تعداد مخاطبین: {len(contacts)}")
    st.divider()

    if not contacts:
        st.info("هنوز مخاطبی پیدا نشد.")
    else:
        for contact in contacts:
            with st.container(border=True):
                col1, col2 = st.columns([3, 2])

                with col1:
                    vip = " ⭐" if contact["vip"] else ""
                    st.subheader(f"{contact['name']}{vip}")

                    if contact["phone"]:
                        st.write(f"📞 {contact['phone']}")

                    if contact["email"]:
                        st.write(f"📧 {contact['email']}")

                with col2:
                    if contact["contact_type"] == "work":
                        st.caption("💼 کاری")
                    else:
                        st.caption("👤 شخصی")

                    budget = contact["budget"]
                    if budget:
                        try:
                            budget = f"{int(budget):,}"
                        except (ValueError, TypeError):
                            pass
                        st.write(f"💰 بودجه: {budget}")

                    if contact["followup"]:
                        st.write(f"📅 پیگیری: {contact['followup']}")

                    if contact["note"]:
                        st.write(f"📝 {contact['note']}")

                btn1, btn2 = st.columns(2)

                with btn1:
                    if st.button(
                        t("edit"),
                        use_container_width=True,
                        key=f"edit_{contact['id']}",
                    ):
                        st.session_state.editing_contact_id = contact["id"]
                        st.session_state.calendar_form_open = False
                        st.rerun()

                with btn2:
                    if st.button(
                        t("new_meeting"),
                        use_container_width=True,
                        key=f"meeting_{contact['id']}",
                    ):
                        st.session_state.calendar_contact_id = contact["id"]
                        st.session_state.calendar_form_open = True
                        st.session_state.editing_contact_id = None
                        st.rerun()


# =========================================================
# CREATE MEETING FORM
# =========================================================

if st.session_state.get("calendar_form_open", False):

    meeting_contact_id = st.session_state.get("calendar_contact_id")

    if meeting_contact_id:
        meeting_contact = database.get_contact(
            meeting_contact_id,
            user["id"],
            st.session_state.workspace_id,
        )

        if meeting_contact:
            st.divider()
            st.subheader(
                tf("meeting_for", name=meeting_contact["name"])
            )

            with st.form("create_meeting_form"):

                meeting_title = st.text_input(
                    t("meeting_title"),
                    value=tf(
                        "meeting_default_title",
                        name=meeting_contact["name"]
                    ),
                )

                meeting_date = st.date_input(
                    t("meeting_date"),
                    value=date.today() + timedelta(days=1),
                )

                col1, col2 = st.columns(2)

                with col1:
                    start_time = st.time_input(
                        t("start_time"),
                        value=datetime.now().replace(
                            hour=10, minute=0, second=0
                        ).time(),
                    )

                with col2:
                    end_time = st.time_input(
                        t("end_time"),
                        value=datetime.now().replace(
                            hour=11, minute=0, second=0
                        ).time(),
                    )

                meeting_description = st.text_area(
                    t("description"),
                    value=tf(
                        "meeting_default_description",
                        name=meeting_contact["name"]
                    ),
                )

                submitted = st.form_submit_button(
                    t("create_meeting"),
                    use_container_width=True,
                )

            if submitted:

                if end_time <= start_time:
                    st.error(t("end_time_error"))

                else:
                    start_datetime = datetime.combine(
                        meeting_date,
                        start_time
                    ).isoformat()

                    end_datetime = datetime.combine(
                        meeting_date,
                        end_time
                    ).isoformat()

                    result = create_calendar_event(
                        user_id=user["id"],
                        workspace_id=st.session_state.workspace_id,
                        title=meeting_title,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        description=meeting_description
                    )

                    if result["success"]:
                        st.success("جلسه با موفقیت ساخته شد!")

                        if result.get("event_link"):
                            st.markdown(
                                f"[مشاهده جلسه در Google Calendar]({result['event_link']})"
                            )

                        st.session_state.calendar_form_open = False
                        st.session_state.calendar_contact_id = None

                        st.rerun()

                    else:
                        st.error(result["message"])

# =========================================================
# ADD CONTACT
# =========================================================

elif st.session_state.page == "add_contact":
    st.header(t("add_contact"))
    if st.session_state.pop("contact_added_ok", False):
        st.success("کاربر با موفقیت اضافه شد!")

    new_name = st.text_input(t("name"), key="new_contact_name")
    new_email = st.text_input(t("email"), key="new_contact_email")
    new_phone = st.text_input(t("phone"), key="new_contact_phone")
    new_note = st.text_area(t("note"), key="new_contact_note")
    new_budget = st.text_input(t("budget"), key="new_contact_budget")
    new_followup = st.date_input(
        t("followup"),
        value=date.today() + timedelta(days=1),
        key="new_contact_followup",
    )
    new_type = st.selectbox(
        t("contact_type"),
        [t("personal"), t("work")],
        key="new_contact_type",
    )

    database_new_type = "work" if new_type == t("work") else "personal"
    new_vip = st.checkbox(t("vip"), key="new_contact_vip")

    if st.button(
        t("add_contact"),
        use_container_width=True,
        key="add_contact_button",
    ):
        if not new_name.strip():
            st.warning(t("add_contact_name_required"))
        else:
            try:
                database.add_contact(
                    user_id=user["id"],
                    name=new_name.strip(),
                    email=new_email.strip(),
                    phone=new_phone.strip(),
                    note=new_note.strip(),
                    followup=new_followup.isoformat(),
                    budget=new_budget.strip(),
                    contact_type=database_new_type,
                    vip=1 if new_vip else 0,
                    workspace_id=st.session_state.workspace_id,
                )
                database.log_activity(
                    user["id"],
                    st.session_state.workspace_id,
                    "مخاطب اضافه شد",
                    new_name.strip(),
                )
                st.session_state.contact_added_ok = True
                st.rerun()
            except Exception as e:
                logger.log_error(f"Add contact error: {e}")
                st.error(tf("add_contact_failed", error=e))


# =========================================================
# ACTIVITY
# =========================================================

elif st.session_state.page == "activity":
    st.header(t("activity"))

    try:
        activities = database.get_activity_logs(
            user["id"],
            st.session_state.workspace_id,
        )

        if not activities:
            st.info(t("no_activity"))
        else:
            for activity in activities:
                with st.container(border=True):
                    st.write(f"📌 {activity.get('action', '')}")

                    if activity.get("details"):
                        st.caption(activity["details"])

                    if activity.get("created_at"):
                        st.caption(f"🕒 {activity['created_at']}")

    except Exception as e:
        logger.log_error(f"Activity page error: {e}")
        st.error(tf("activity_error", error=e))


# =========================================================
# FINANCE
# =========================================================

elif st.session_state.page == "finance":
    st.header(t("finance"))

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("ثبت درآمد", use_container_width=True):
            st.session_state.finance_action = "income"

    with col2:
        if st.button("ثبت هزینه", use_container_width=True):
            st.session_state.finance_action = "expense"

    with col3:
        if st.button("گزارش مالی", use_container_width=True):
            st.session_state.finance_action = "report"

    action = st.session_state.get("finance_action", "report")

    # ---------- فرم ثبت درآمد / هزینه ----------
    if action in ("income", "expense"):
        is_income = action == "income"
        label = "درآمد" if is_income else "هزینه"

        st.subheader(f"ثبت {label}")

        with st.form(f"{action}_form"):
            amount = st.number_input(f"مبلغ {label}", min_value=0, step=1000)
            title = st.text_input(f"عنوان {label}")
            category = st.text_input("دسته‌بندی")
            transaction_date = st.date_input("تاریخ")
            description = st.text_area("توضیحات (اختیاری)")
            submit = st.form_submit_button(f"ثبت {label}")

        if submit:
            if not title.strip():
                st.warning("عنوان را وارد کن.")
            elif not category.strip():
                st.warning("دسته‌بندی را وارد کن.")
            elif amount <= 0:
                st.warning("مبلغ باید بیشتر از صفر باشد.")
            else:
                try:
                    category_id = finance_queries.get_or_create_finance_category(
                        st.session_state.workspace_id,
                        category.strip(),
                        action,
                    )

                    database.add_finance_transaction(
                        user_id=user["id"],
                        workspace_id=st.session_state.workspace_id,
                        transaction_type=action,
                        amount=int(amount),
                        title=title.strip(),
                        category_id=category_id,
                        description=description,
                        transaction_date=str(transaction_date),
                    )

                    st.success(f"{label} با موفقیت ثبت شد")

                except Exception as e:
                    logger.log_error(f"Finance save error: {e}")
                    st.error(f"ثبت ناموفق بود: {e}")

    # ---------- گزارش مالی ----------
    elif action == "report":
        st.subheader("گزارش مالی")

        summary = finance_queries.get_finance_summary(
            user["id"], st.session_state.workspace_id
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("جمع درآمد", f"{summary['income']:,}")
        c2.metric("جمع هزینه", f"{summary['expense']:,}")
        c3.metric("سود", f"{summary['profit']:,}")




def get_or_create_finance_category(workspace_id, name, category_type="income"):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id FROM finance_categories
            WHERE workspace_id = ?
            AND name = ?
            AND category_type = ?
            """,
            (workspace_id, name.strip(), category_type)
        )

        category = cursor.fetchone()

        if category:
            return category["id"]

        cursor.execute(
            """
            INSERT INTO finance_categories
            (workspace_id, name, category_type, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (workspace_id, name.strip(), category_type, now())
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()

# =========================================================
# SETTINGS
# =========================================================

if st.session_state.page == "settings":
    st.header(t("profile"))

    col1, col2 = st.columns([1, 3])

    with col1:
        show_avatar(user, 100)

        uploaded_avatar = st.file_uploader(
            "تغییر تصویر پروفایل",
            type=["png", "jpg", "jpeg"],
        )

        if uploaded_avatar:
            avatar_id = f"{uploaded_avatar.name}-{uploaded_avatar.size}"

            if st.session_state.get("last_avatar") != avatar_id:
                avatar_dir = os.path.join(BASE_DIR, "avatars")
                os.makedirs(avatar_dir, exist_ok=True)
                avatar_path = os.path.join(avatar_dir, f"user_{user['id']}.png")

                image = Image.open(uploaded_avatar)
                image = ImageOps.exif_transpose(image).convert("RGBA")
                image = ImageOps.fit(image, (256, 256))

                mask = Image.new("L", (256, 256), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, 256, 256), fill=255)
                image.putalpha(mask)

                image.save(avatar_path)

                database.update_user_avatar(user["id"], avatar_path)
                user["avatar"] = avatar_path
                st.session_state.user = user
                save_session(user)

                st.session_state.last_avatar = avatar_id
                st.rerun()

    with col2:
        st.subheader(t("account_info"))
        st.write(f"**{t('name')}:** {user.get('name', '')}")
        st.write(f"**{t('email')}:** {user.get('email', '')}")
        st.write(f"**{t('plan')}:** {user.get('plan', 'free')}")


    with col2:
        st.subheader(t("account_info"))
        st.write(f"**{t('name')}:** {user.get('name', '')}")
        st.write(f"**{t('email')}:** {user.get('email', '')}")
        st.write(f"**{t('plan')}:** {user.get('plan', 'free')}")
# =========================================================
# EDIT CONTACT
# =========================================================

if (
    st.session_state.page == "contacts"
    and st.session_state.editing_contact_id
):
    contact = database.get_contact(
        st.session_state.editing_contact_id,
        user["id"],
        st.session_state.workspace_id,
    )

    if contact:
        contact = dict(contact)  # تغییر ۱

        st.divider()
        st.subheader(tf("edit_contact", name=contact["name"]))

        edit_name = st.text_input(
            t("name"),
            value=contact.get("name", ""),
            key="edit_name",
        )
        edit_email = st.text_input(
            t("email"),
            value=contact.get("email", ""),
            key="edit_email",
        )
        edit_phone = st.text_input(
            t("phone"),
            value=contact.get("phone", ""),
            key="edit_phone",
        )
        edit_note = st.text_area(
            t("note"),
            value=contact.get("note", ""),
            key="edit_note",
        )
        edit_budget = st.text_input(
            t("budget"),
            value=str(contact.get("budget") or ""),  # تغییر ۲
            key="edit_budget",
        )
        edit_followup = st.date_input(
            t("followup"),
            value=(
                date.fromisoformat(contact["followup"])
                if contact.get("followup")
                else date.today()
            ),
            key="edit_followup",
        )
        edit_type = st.selectbox(
            t("contact_type"),
            [t("personal"), t("work")],
            index=1 if contact.get("contact_type") == "work" else 0,
            key="edit_contact_type",
        )
        database_type = "work" if edit_type == t("work") else "personal"

        edit_vip = st.checkbox(  # تغییر ۳
            t("vip"),
            value=bool(contact.get("vip")),
            key="edit_vip",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                t("save_changes"),
                use_container_width=True,
                key="save_edit_contact",
            ):
                try:
                    database.update_contact(
                        contact_id=contact["id"],
                        user_id=user["id"],
                        name=edit_name,
                        email=edit_email,
                        phone=edit_phone,
                        note=edit_note,
                        followup=edit_followup.isoformat(),
                        budget=edit_budget,
                        contact_type=database_type,
                        vip=1 if edit_vip else 0,  # تغییر ۳
                        workspace_id=st.session_state.workspace_id,
                    )
                    st.success(t("contact_updated"))
                    st.session_state.editing_contact_id = None
                    st.rerun()
                except Exception as e:
                    logger.log_error(f"Update contact error: {e}")
                    st.error(tf("edit_failed", error=e))

        with col2:
            if st.button(
                t("cancel"),
                use_container_width=True,
                key="cancel_edit_contact",
            ):
                st.session_state.editing_contact_id = None
                st.rerun()


# =========================================================
# APP VERSION
# =========================================================

APP_VERSION = "0.1.1"


# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption(t("footer"))
def get_finance_transactions(user_id, workspace_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                t.id,
                t.transaction_type,
                t.amount,
                t.title,
                c.name AS category,
                t.description,
                t.transaction_date
            FROM finance_transactions t
            LEFT JOIN finance_categories c ON c.id = t.category_id
            WHERE t.user_id = ?
            AND t.workspace_id = ?
            ORDER BY t.transaction_date DESC, t.id DESC
            """,
            (user_id, workspace_id)
        )

        return cursor.fetchall()

    finally:
        conn.close()


def get_finance_summary(user_id, workspace_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT transaction_type, COALESCE(SUM(amount), 0) AS total
            FROM finance_transactions
            WHERE user_id = ?
            AND workspace_id = ?
            GROUP BY transaction_type
            """,
            (user_id, workspace_id)
        )

        totals = {row["transaction_type"]: row["total"] for row in cursor.fetchall()}

        income = totals.get("income", 0)
        expense = totals.get("expense", 0)

        return {
            "income": income,
            "expense": expense,
            "profit": income - expense
        }

    finally:
        conn.close()