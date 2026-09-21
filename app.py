import streamlit as st
import database
import ai
import api_client
import logger

from google_auth import create_google_flow
from calendar_service import create_calendar_event

import json
import os
import time

from urllib.parse import urlencode
from datetime import date, datetime

from PIL import Image
import requests
try:

    database.init_finance_tables()

except Exception as e:

    logger.log_error(
        f"Finance init error: {e}"
    )

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
    page_icon="🚀",
    layout="wide"
)

logger.log_info("ConnectAI started")


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
    "workspace_id": None,
    "language": "🇮🇷 فارسی",
    "ai_results": {},
    "editing_contact_id": None,
    "selected_contact_id": None,
    "mobile_menu_open": False,
    "google_state": None,
    "google_code_verifier": None,
    "calendar_contact_id": None,
    "calendar_form_open": False,
    "contact_selected_message": None
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
        "fa": "🚀 ConnectAI",
        "en": "🚀 ConnectAI",
        "es": "🚀 ConnectAI"
    },

    "subtitle": {
        "fa": "دستیار هوشمند مدیریت مخاطبین",
        "en": "Smart Contact Management Assistant",
        "es": "Asistente inteligente de gestión de contactos"
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
        "fa": "⭐ VIP",
        "en": "⭐ VIP",
        "es": "⭐ VIP"
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
        "fa": "🚪 خروج",
        "en": "🚪 Logout",
        "es": "🚪 Cerrar sesión"
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

    "total_contacts": {
        "fa": "👥 مخاطبین",
        "en": "👥 Contacts",
        "es": "👥 Contactos"
    },

    "business_contacts": {
        "fa": "💼 کاری",
        "en": "💼 Business",
        "es": "💼 Negocios"
    },

    "today": {
        "fa": "📅 امروز",
        "en": "📅 Today",
        "es": "📅 Hoy"
    },

    "overdue": {
        "fa": "⚠️ عقب افتاده",
        "en": "⚠️ Overdue",
        "es": "⚠️ Vencidos"
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

    "change_vip": {
        "fa": "⭐ تغییر VIP",
        "en": "⭐ Change VIP",
        "es": "⭐ Cambiar VIP"
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

    "footer": {
        "fa": "🚀 ConnectAI — مدیریت هوشمند مخاطبین",
        "en": "🚀 ConnectAI — Smart Contact Management",
        "es": "🚀 ConnectAI — Gestión inteligente de contactos"
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

    avatar = user.get("avatar", "") if user else ""

    if avatar and os.path.exists(avatar):
        try:
            image = Image.open(avatar)
            st.image(image, width=size)
            return

        except Exception as e:
            logger.log_error(
                f"Failed to load avatar: {e}"
            )

    st.markdown(
        f"""
        <div style="
            width:{size}px;
            height:{size}px;
            border-radius:50%;
            background:linear-gradient(135deg,#667eea,#764ba2);
            display:flex;
            align-items:center;
            justify-content:center;
            color:white;
            font-size:{size // 2}px;
        ">
            👤
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
            t("login"),
            t("register")
        ]
    )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    with tab_login:

        st.title(t("login"))

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
            t("login"),
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
                        result.get(
                            "message",
                            t("login_error")
                        )
                    )

            except Exception as e:

                logger.log_error(
                    f"Login error: {e}"
                )

                st.error(
                    tf(
                        "login_error_exception",
                        error=e
                    )
                )

        st.divider()

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
                    flow,
                    "code_verifier",
                    None
                )

                if not code_verifier:

                    st.error(
                        t("google_security_failed")
                    )

                else:

                    st.session_state.google_state = state
                    st.session_state.google_code_verifier = (
                        code_verifier
                    )

                    if save_google_state(
                        state,
                        code_verifier
                    ):

                        st.link_button(
                            t("continue_google"),
                            authorization_url,
                            use_container_width=True
                        )

                    else:

                        st.error(
                            t("google_security_save_failed")
                        )

            except Exception as e:

                logger.log_error(
                    f"Google authorization error: {e}"
                )

                st.error(
                    tf(
                        "google_login_error",
                        error=e
                    )
                )

    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    with tab_register:

        st.title(t("register"))

        reg_name = st.text_input(
            t("name"),
            key="reg_name"
        )

        reg_email = st.text_input(
            t("email"),
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

user = st.session_state.user

if not user:

    st.session_state.logged_in = False
    st.rerun()


# =========================================================
# INTERNAL WORKSPACE
# =========================================================

# Workspace is now hidden from the UI.
# It remains internally because the current database
# uses workspace_id for data isolation.

if not st.session_state.workspace_id:

    st.session_state.workspace_id = (
     database.get_or_create_default_workspace(
            user["id"]
        )
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title(t("title"))

    st.divider()

    show_avatar(user, 65)

    st.write(
        f"**{user.get('name', '')}**"
    )

    st.caption(
        user.get("email", "")
    )

    st.divider()

    if st.button(
        t("dashboard"),
        use_container_width=True,
        key="nav_dashboard"
    ):
        st.session_state.page = "dashboard"
        st.session_state.editing_contact_id = None
        st.rerun()

    if st.button(
        t("contacts"),
        use_container_width=True,
        key="nav_contacts"
    ):
        st.session_state.page = "contacts"
        st.session_state.editing_contact_id = None
        st.rerun()

    if st.button(
        t("add_contact"),
        use_container_width=True,
        key="nav_add_contact"
    ):
        st.session_state.page = "add_contact"
        st.session_state.editing_contact_id = None
        st.rerun()

    if st.button(
        t("activity"),
        use_container_width=True,
        key="nav_activity"
    ):
        st.session_state.page = "activity"
        st.session_state.editing_contact_id = None
        st.rerun()

    if st.button(
        t("finance"),
        use_container_width=True,
        key="nav_finance"
    ):
        st.session_state.page = "finance"
        st.session_state.editing_contact_id = None
        st.rerun()

    if st.button(
        t("profile"),
        use_container_width=True,
        key="nav_profile"
    ):
        st.session_state.page = "profile"
        st.session_state.editing_contact_id = None
        st.rerun()

    st.divider()

    if st.button(
        t("logout"),
        use_container_width=True,
        key="logout_button"
    ):

        clear_session()
        clear_google_state()

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

header_col1, header_col2 = st.columns([5, 1])

with header_col1:

    st.title(t("title"))
    st.caption(t("subtitle"))

with header_col2:

    show_avatar(user, 55)


# =========================================================
# DASHBOARD
# =========================================================

if st.session_state.page == "dashboard":

    st.markdown(
        """
        <div style="
            position:relative;
            overflow:hidden;
            min-height:220px;
            padding:34px 38px;
            margin:8px 0 28px 0;
            border-radius:28px;

            background:linear-gradient(
                135deg,
                rgba(255,255,255,0.88),
                rgba(245,248,255,0.70)
            );

            border:1px solid rgba(255,255,255,0.80);

            box-shadow:
                0 20px 55px rgba(31,41,55,0.10),
                inset 0 1px 0 rgba(255,255,255,0.95);

            backdrop-filter:blur(22px);
            -webkit-backdrop-filter:blur(22px);
        ">

            <div style="
                position:absolute;
                width:280px;
                height:280px;
                right:-90px;
                top:-110px;
                border-radius:50%;

                background:radial-gradient(
                    circle,
                    rgba(99,102,241,0.20) 0%,
                    rgba(99,102,241,0.07) 45%,
                    transparent 72%
                );
            "></div>

            <div style="
                position:absolute;
                width:220px;
                height:220px;
                left:-100px;
                bottom:-130px;
                border-radius:50%;

                background:radial-gradient(
                    circle,
                    rgba(56,189,248,0.16) 0%,
                    transparent 70%
                );
            "></div>

            <div style="
                position:relative;
                z-index:2;
                max-width:75%;
            ">

                <div style="
                    display:inline-flex;
                    align-items:center;
                    gap:8px;

                    padding:7px 13px;
                    margin-bottom:14px;

                    border-radius:999px;

                    background:rgba(255,255,255,0.72);
                    border:1px solid rgba(255,255,255,0.90);

                    box-shadow:
                        0 8px 22px rgba(31,41,55,0.07);

                    color:#4f46e5;
                    font-size:13px;
                    font-weight:700;
                ">
                    ✨ ConnectAI
                </div>

            </div>

            <div style="
                position:absolute;
                z-index:2;
                right:34px;
                bottom:28px;

                width:92px;
                height:92px;

                display:flex;
                align-items:center;
                justify-content:center;

                border-radius:30px;

                background:linear-gradient(
                    145deg,
                    rgba(255,255,255,0.94),
                    rgba(238,242,255,0.74)
                );

                border:1px solid rgba(255,255,255,0.95);

                box-shadow:
                    0 18px 35px rgba(79,70,229,0.15);

                font-size:44px;

                transform:rotate(4deg);
            ">
                🤖
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    stats = database.get_dashboard_stats(
        user["id"],
        st.session_state.workspace_id
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            t("total_contacts"),
            stats["total"]
        )

    with c2:
        st.metric(
            t("vip"),
            stats["vip"]
        )

    with c3:
        st.metric(
            t("business_contacts"),
            stats["work"]
        )

    with c4:
        st.metric(
            t("today"),
            stats["today"]
        )

    with c5:
        st.metric(
            t("overdue"),
            stats["late"]
        )

    st.divider()

    st.subheader(t("today_suggestions"))

    contacts = database.get_contacts(
        user["id"],
        st.session_state.workspace_id
    )

    today = date.today()
    followups = []

    for contact in contacts:

        followup = contact.get("followup")

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

                st.write(
                    f"👤 **{contact['name']}**"
                )

                st.caption(
                    f"📅 {t('followup')}: "
                    f"{contact['followup']}"
                )

                if st.button(
                    t("view_contact"),
                    key=f"dash_{contact['id']}"
                ):

                    st.session_state.selected_contact_id = (
                        contact["id"]
                    )

                    st.session_state.contact_selected_message = (
                        contact["name"]
                    )

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

                vip = "⭐" if contact.get("vip") else ""

                st.write(
                    f"**{contact['name']}** {vip}"
                )

            with col2:

                st.caption(
                    contact.get("phone", "")
                )

            with col3:

                if st.button(
                    "👁️",
                    key=f"view_{contact['id']}"
                ):

                    st.session_state.selected_contact_id = (
                        contact["id"]
                    )

                    st.session_state.contact_selected_message = (
                        contact["name"]
                    )

                    st.session_state.page = "contacts"
                    st.rerun()


# =========================================================
# CONTACTS
# =========================================================

elif st.session_state.page == "contacts":

    st.header(t("contacts"))

    if st.session_state.get(
        "contact_selected_message"
    ):

        selected_name = (
            st.session_state.contact_selected_message
        )

        st.toast(
            tf(
                "contact_selected",
                name=selected_name
            ),
            icon="💬"
        )

        st.session_state.contact_selected_message = None

    search = st.text_input(
        t("search"),
        key="contact_search"
    )

    if search.strip():

        contacts = database.search_contacts(
            user["id"],
            search,
            st.session_state.workspace_id
        )

    else:

        contacts = database.get_contacts(
            user["id"],
            st.session_state.workspace_id
        )

    st.caption(
        tf(
            "contacts_count",
            count=len(contacts)
        )
    )

    if not contacts:

        st.info(t("no_contact_found"))

    else:

        for contact in contacts:

            with st.container(border=True):

                col1, col2, col3 = st.columns([5, 4, 2])

                with col1:

                    vip = "⭐" if contact.get("vip") else ""

                    st.subheader(
                        f"{contact['name']} {vip}"
                    )

                    if contact.get("phone"):
                        st.write(
                            f"📞 {contact['phone']}"
                        )

                    if contact.get("email"):
                        st.write(
                            f"📧 {contact['email']}"
                        )

                with col2:

                    if contact.get("note"):
                        st.write(
                            f"📝 {contact['note']}"
                        )

                    if contact.get("followup"):
                        st.write(
                            f"📅 {contact['followup']}"
                        )

                    if contact.get("budget"):
                        st.write(
                            f"💰 {contact['budget']}"
                        )

                    if contact.get("contact_type"):

                        type_text = (
                            t("work")
                            if contact["contact_type"] == "work"
                            else t("personal")
                        )

                        st.caption(
                            f"{t('contact_type')}: "
                            f"{type_text}"
                        )

                with col3:

                    if st.button(
                        t("ai_analyze"),
                        key=f"ai_{contact['id']}"
                    ):

                        question = t("ai_contact_prompt")

                        with st.spinner(
                            t("ai_loading")
                        ):

                            try:

                                result = ai.ask_contact_ai(
                                    contact,
                                    question
                                )

                            except Exception as e:

                                logger.log_error(
                                    f"AI analysis error: {e}"
                                )

                                result = tf(
                                    "ai_analysis_error",
                                    error=e
                                )

                        st.session_state.ai_results[
                            contact["id"]
                        ] = result

                        st.rerun()

                    if contact["id"] in st.session_state.ai_results:

                        with st.expander(
                            t("ai_result")
                        ):

                            st.write(
                                st.session_state.ai_results[
                                    contact["id"]
                                ]
                            )

                    if st.button(
                        t("change_vip"),
                        key=f"vip_{contact['id']}"
                    ):

                        try:

                            database.toggle_vip(
                                contact["id"],
                                user["id"],
                                contact.get("vip", 0),
                                st.session_state.workspace_id
                            )

                            st.rerun()

                        except Exception as e:

                            logger.log_error(
                                f"VIP toggle error: {e}"
                            )

                            st.error(
                                tf(
                                    "vip_update_failed",
                                    error=e
                                )
                            )

                    if st.button(
                        t("new_meeting"),
                        key=f"calendar_{contact['id']}"
                    ):

                        st.session_state.calendar_contact_id = (
                            contact["id"]
                        )

                        st.session_state.calendar_form_open = True

                        st.rerun()

                    if st.button(
                        t("edit"),
                        key=f"edit_{contact['id']}"
                    ):

                        st.session_state.editing_contact_id = (
                            contact["id"]
                        )

                        st.rerun()


# =========================================================
# ADD CONTACT
# =========================================================

elif st.session_state.page == "add_contact":

    st.header(t("add_contact"))

    new_name = st.text_input(
        t("name"),
        key="new_contact_name"
    )

    new_email = st.text_input(
        t("email"),
        key="new_contact_email"
    )

    new_phone = st.text_input(
        t("phone"),
        key="new_contact_phone"
    )

    new_note = st.text_area(
        t("note"),
        key="new_contact_note"
    )

    new_budget = st.text_input(
        t("budget"),
        key="new_contact_budget"
    )

    new_followup = st.date_input(
        t("followup"),
        value=date.today(),
        key="new_contact_followup"
    )

    new_type = st.selectbox(
        t("contact_type"),
        [
            t("personal"),
            t("work")
        ],
        key="new_contact_type"
    )

    database_new_type = (
        "work"
        if new_type == t("work")
        else "personal"
    )

    new_vip = st.checkbox(
        t("vip"),
        key="new_contact_vip"
    )

    if st.button(
        t("add_contact"),
        use_container_width=True,
        key="add_contact_button"
    ):

        if not new_name.strip():

            st.warning(
                t("add_contact_name_required")
            )

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
                    workspace_id=st.session_state.workspace_id
                )

                st.success(t("contact_added"))
                st.rerun()

            except Exception as e:

                logger.log_error(
                    f"Add contact error: {e}"
                )

                st.error(
                    tf(
                        "add_contact_failed",
                        error=e
                    )
                )


# =========================================================
# ACTIVITY
# =========================================================

elif st.session_state.page == "activity":

    st.header(t("activity"))

    try:

        activities = database.get_activity_logs(
            user["id"],
            st.session_state.workspace_id
        )

        if not activities:

            st.info(t("no_activity"))

        else:

            for activity in activities:

                with st.container(border=True):

                    st.write(
                        f"📌 {activity.get('action', '')}"
                    )

                    if activity.get("details"):
                        st.caption(
                            activity["details"]
                        )

                    if activity.get("created_at"):
                        st.caption(
                            f"🕒 {activity['created_at']}"
                        )

    except Exception as e:

        logger.log_error(
            f"Activity page error: {e}"
        )

        st.error(
            tf(
                "activity_error",
                error=e
            )
        )


# =========================================================
# FINANCE SYSTEM V2
# Professional Business Finance Module
# =========================================================
#
# Features:
# - Income / Expense management
# - Customer financial history
# - Debt tracking
# - Budget management
# - Custom categories
#
# Data isolation:
# user_id + workspace_id
#
# =========================================================



# =========================================================
# FINANCE
# =========================================================

elif st.session_state.page == "finance":

    st.header(t("finance"))

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "➕ ثبت درآمد",
            use_container_width=True
        ):
            st.session_state.finance_action = "income"

    with col2:
        if st.button(
            "➖ ثبت هزینه",
            use_container_width=True
        ):
            st.session_state.finance_action = "expense"

    with col3:
        if st.button(
            "📊 گزارش مالی",
            use_container_width=True
        ):
            st.session_state.finance_action = "report"





# =========================================================
# PROFILE
# =========================================================

elif st.session_state.page == "profile":

    st.header(t("profile"))

    col1, col2 = st.columns([1, 3])

    with col1:

        show_avatar(
            user,
            100
        )

        uploaded_avatar = st.file_uploader(
            "📷 تغییر عکس پروفایل",
            type=[
                "png",
                "jpg",
                "jpeg"
            ],
            key="avatar_upload"
        )
if uploaded_avatar:

    avatar_dir = os.path.join(
        BASE_DIR,
        "avatars"
    )

    os.makedirs(
        avatar_dir,
        exist_ok=True
    )

    avatar_path = os.path.join(
        avatar_dir,
        f"user_{user['id']}.png"
    )

    image = Image.open(uploaded_avatar)

    image.save(
        avatar_path
    )

    database.update_user_avatar(
        user["id"],
        avatar_path
    )

    user["avatar"] = avatar_path

    st.session_state.user = user

    save_session(user)

    st.success("عکس پروفایل ذخیره شد ✅")

    st.rerun()

    with col2:

        st.subheader(
            user.get("name", "")
        )

        st.write(
            f"📧 {user.get('email', '')}"
        )

        st.write(
            f"💎 {t('plan')}: "
            f"{user.get('plan', 'free')}"
        )

    st.divider()

    st.subheader(
        t("account_info")
    )

    profile_name = st.text_input(
        t("name"),
        value=user.get("name", ""),
        key="profile_name"
    )

    if st.button(
        t("save_name"),
        key="save_profile_name"
    ):

        try:

            database.update_user_name(
                user["id"],
                profile_name.strip()
            )

            user["name"] = profile_name.strip()

            st.session_state.user = user

            save_session(user)

            st.success(t("name_updated"))

            st.rerun()

        except Exception as e:

            logger.log_error(
                f"Profile update error: {e}"
            )

            st.error(
                tf(
                    "profile_update_failed",
                    error=e
                )
            )


# =========================================================
# GOOGLE CALENDAR FORM
# =========================================================

if (
    st.session_state.page == "contacts"
    and st.session_state.calendar_form_open
    and st.session_state.calendar_contact_id
):

    calendar_contact = database.get_contact(
        st.session_state.calendar_contact_id,
        user["id"],
        st.session_state.workspace_id
    )

    if calendar_contact:

        st.divider()

        st.subheader(
            tf(
                "meeting_for",
                name=calendar_contact["name"]
            )
        )

        event_title = st.text_input(
            t("meeting_title"),
            value=tf(
                "meeting_default_title",
                name=calendar_contact["name"]
            ),
            key="calendar_event_title"
        )

        event_date = st.date_input(
            t("meeting_date"),
            value=date.today(),
            key="calendar_event_date"
        )

        col1, col2 = st.columns(2)

        with col1:

            start_time = st.time_input(
                t("start_time"),
                value=datetime.strptime(
                    "10:00",
                    "%H:%M"
                ).time(),
                key="calendar_start_time"
            )

        with col2:

            end_time = st.time_input(
                t("end_time"),
                value=datetime.strptime(
                    "11:00",
                    "%H:%M"
                ).time(),
                key="calendar_end_time"
            )

        event_description = st.text_area(
            t("description"),
            value=tf(
                "meeting_default_description",
                name=calendar_contact["name"]
            ),
            key="calendar_event_description"
        )

        col1, col2 = st.columns(2)

        with col1:

            create_event = st.button(
                t("create_meeting"),
                use_container_width=True,
                key="create_calendar_event"
            )

        with col2:

            cancel_event = st.button(
                t("cancel"),
                use_container_width=True,
                key="cancel_calendar_event"
            )

        if cancel_event:

            st.session_state.calendar_contact_id = None
            st.session_state.calendar_form_open = False
            st.rerun()

        if create_event:

            if end_time <= start_time:

                st.error(
                    t("end_time_error")
                )

            else:

                try:

                    start_datetime = datetime.combine(
                        event_date,
                        start_time
                    ).isoformat()

                    end_datetime = datetime.combine(
                        event_date,
                        end_time
                    ).isoformat()

                    with st.spinner(
                        t("creating_meeting")
                    ):

                        result = create_calendar_event(
                            user_id=user["id"],
                            workspace_id=st.session_state.workspace_id,
                            title=event_title,
                            start_datetime=start_datetime,
                            end_datetime=end_datetime,
                            description=event_description
                        )

                    if result.get("success"):

                        st.success(
                            t("meeting_created")
                        )

                        event_link = result.get(
                            "event_link"
                        )

                        if event_link:

                            st.link_button(
                                t("open_calendar"),
                                event_link,
                                use_container_width=True
                            )

                        st.session_state.calendar_contact_id = None
                        st.session_state.calendar_form_open = False

                    else:

                        st.error(
                            t("meeting_failed")
                        )

                        st.error(
                            result.get(
                                "message",
                                t("unknown_error")
                            )
                        )

                except Exception as e:

                    logger.log_error(
                        f"Google Calendar event creation error: {e}"
                    )

                    st.error(
                        tf(
                            "calendar_error",
                            error=e
                        )
                    )


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
        st.session_state.workspace_id
    )

    if contact:

        st.divider()

        st.subheader(
            tf(
                "edit_contact",
                name=contact["name"]
            )
        )

        edit_name = st.text_input(
            t("name"),
            value=contact.get("name", ""),
            key="edit_name"
        )

        edit_email = st.text_input(
            t("email"),
            value=contact.get("email", ""),
            key="edit_email"
        )

        edit_phone = st.text_input(
            t("phone"),
            value=contact.get("phone", ""),
            key="edit_phone"
        )

        edit_note = st.text_area(
            t("note"),
            value=contact.get("note", ""),
            key="edit_note"
        )

        edit_budget = st.text_input(
            t("budget"),
            value=contact.get("budget", ""),
            key="edit_budget"
        )

        edit_followup = st.date_input(
            t("followup"),
            value=(
                date.fromisoformat(
                    contact["followup"]
                )
                if contact.get("followup")
                else date.today()
            ),
            key="edit_followup"
        )

        edit_type = st.selectbox(
            t("contact_type"),
            [
                t("personal"),
                t("work")
            ],
            index=(
                1
                if contact.get("contact_type") == "work"
                else 0
            ),
            key="edit_contact_type"
        )

        database_type = (
            "work"
            if edit_type == t("work")
            else "personal"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                t("save_changes"),
                use_container_width=True,
                key="save_edit_contact"
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
                        workspace_id=st.session_state.workspace_id
                    )

                    st.success(
                        t("contact_updated")
                    )

                    st.session_state.editing_contact_id = None

                    st.rerun()

                except Exception as e:

                    logger.log_error(
                        f"Update contact error: {e}"
                    )

                    st.error(
                        tf(
                            "edit_failed",
                            error=e
                        )
                    )

        with col2:

            if st.button(
                t("cancel"),
                use_container_width=True,
                key="cancel_edit_contact"
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

st.caption(
    t("footer")
)