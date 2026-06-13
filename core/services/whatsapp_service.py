import logging
import json
import urllib.request
import urllib.error
from django.conf import settings

logger = logging.getLogger("core.whatsapp")


def format_whatsapp_number(number):
    """
    Format standard mobile numbers for WhatsApp API (E.164 format).
    Assumes Indian mobile numbers if length is 10 digits.
    """
    if not number:
        return ""
    # Strip non-numeric characters except leading +
    cleaned = "".join(c for c in str(number) if c.isdigit() or c == "+")
    if len(cleaned) == 10 and cleaned.isdigit():
        return "+91" + cleaned
    if not cleaned.startswith("+"):
        return "+" + cleaned
    return cleaned


def get_whatsapp_settings():
    """
    Retrieve WhatsApp configurations, checking the database first, then settings.py
    """
    from core.models import WhatsAppConfig

    try:
        db_config = WhatsAppConfig.get_solo()
    except Exception:
        # Fallback if database is unavailable or migration not run
        db_config = None

    if db_config:
        return {
            "enabled": db_config.is_enabled,
            "provider": db_config.provider,
            "meta_token": db_config.meta_token or getattr(settings, "WHATSAPP_META_TOKEN", ""),
            "meta_phone_id": db_config.meta_phone_id or getattr(settings, "WHATSAPP_META_PHONE_ID", ""),
            "twilio_sid": db_config.twilio_sid or getattr(settings, "WHATSAPP_TWILIO_SID", ""),
            "twilio_auth_token": db_config.twilio_auth_token or getattr(settings, "WHATSAPP_TWILIO_AUTH_TOKEN", ""),
            "twilio_from": db_config.twilio_from or getattr(settings, "WHATSAPP_TWILIO_FROM", ""),
            "custom_url": db_config.custom_url or getattr(settings, "WHATSAPP_CUSTOM_URL", ""),
            "custom_token": db_config.custom_token or getattr(settings, "WHATSAPP_CUSTOM_TOKEN", ""),
            "admission_template": db_config.admission_template or getattr(settings, "WHATSAPP_ADMISSION_TEMPLATE", ""),
            "payment_template": db_config.payment_template or getattr(settings, "WHATSAPP_PAYMENT_TEMPLATE", ""),
            "enquiry_template": db_config.enquiry_template or getattr(settings, "WHATSAPP_ENQUIRY_TEMPLATE", ""),
            "absent_template": db_config.absent_template or getattr(settings, "WHATSAPP_ABSENT_TEMPLATE", ""),
        }

    return {
        "enabled": getattr(settings, "WHATSAPP_ENABLED", False),
        "provider": getattr(settings, "WHATSAPP_PROVIDER", "console").lower(),
        "meta_token": getattr(settings, "WHATSAPP_META_TOKEN", ""),
        "meta_phone_id": getattr(settings, "WHATSAPP_META_PHONE_ID", ""),
        "twilio_sid": getattr(settings, "WHATSAPP_TWILIO_SID", ""),
        "twilio_auth_token": getattr(settings, "WHATSAPP_TWILIO_AUTH_TOKEN", ""),
        "twilio_from": getattr(settings, "WHATSAPP_TWILIO_FROM", ""),
        "custom_url": getattr(settings, "WHATSAPP_CUSTOM_URL", ""),
        "custom_token": getattr(settings, "WHATSAPP_CUSTOM_TOKEN", ""),
        "admission_template": getattr(settings, "WHATSAPP_ADMISSION_TEMPLATE", ""),
        "payment_template": getattr(settings, "WHATSAPP_PAYMENT_TEMPLATE", ""),
        "enquiry_template": getattr(settings, "WHATSAPP_ENQUIRY_TEMPLATE", ""),
        "absent_template": getattr(settings, "WHATSAPP_ABSENT_TEMPLATE", ""),
    }


def send_whatsapp_message(to_number, message_body):
    """
    Sends a WhatsApp message to the specified number using the configured provider.
    """
    config = get_whatsapp_settings()

    if not config["enabled"]:
        logger.info("WhatsApp bot is disabled. Message to %s not sent.", to_number)
        return False

    formatted_to = format_whatsapp_number(to_number)
    if not formatted_to:
        logger.error("Invalid WhatsApp number provided: %s", to_number)
        return False

    provider = config["provider"].lower()
    logger.info("Sending WhatsApp message to %s using provider: %s", formatted_to, provider)

    if provider == "console":
        logger.info("\n--- WHATSAPP CONSOLE MESSAGE ---\nTo: %s\nMessage: %s\n--------------------------------", formatted_to, message_body)
        print(f"\n--- WHATSAPP CONSOLE MESSAGE ---\nTo: {formatted_to}\nMessage: {message_body}\n--------------------------------")
        return True

    elif provider == "twilio":
        try:
            from twilio.rest import Client
        except ImportError:
            logger.error("The 'twilio' library is required to use the Twilio WhatsApp provider. Install it using 'pip install twilio'.")
            return False

        account_sid = config["twilio_sid"]
        auth_token = config["twilio_auth_token"]
        from_number = config["twilio_from"]

        if not account_sid or not auth_token or not from_number:
            logger.error("Twilio credentials (SID, Token, or From number) are missing in settings.")
            return False

        try:
            client = Client(account_sid, auth_token)
            from_wa = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
            to_wa = f"whatsapp:{formatted_to}"

            message = client.messages.create(
                body=message_body,
                from_=from_wa,
                to=to_wa
            )
            logger.info("Twilio WhatsApp message sent successfully. SID: %s", message.sid)
            return True
        except Exception as e:
            logger.exception("Error sending WhatsApp message via Twilio: %s", e)
            return False

    elif provider == "meta":
        token = config["meta_token"]
        phone_id = config["meta_phone_id"]

        if not token or not phone_id:
            logger.error("Meta WhatsApp Cloud API credentials (Token or Phone ID) are missing in settings.")
            return False

        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        recipient = formatted_to.replace("+", "")
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "body": message_body
            }
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                logger.info("Meta WhatsApp Cloud API message sent successfully: %s", resp_data)
                return True
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error("Meta WhatsApp Cloud API HTTP Error: %s - Response: %s", e, error_body)
            return False
        except Exception as e:
            logger.exception("Error sending WhatsApp message via Meta Cloud API: %s", e)
            return False

    elif provider == "custom":
        custom_url = config["custom_url"]
        token = config["custom_token"]
        if not custom_url:
            logger.error("Custom Gateway URL is missing in settings.")
            return False

        headers = {
            "Content-Type": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {
            "to": formatted_to,
            "message": message_body,
            "msg": message_body,
            "body": message_body,
            "token": token
        }
        try:
            req = urllib.request.Request(
                custom_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_data = response.read().decode("utf-8")
                logger.info("Custom WhatsApp Gateway message sent successfully. Response: %s", resp_data)
                return True
        except Exception as e:
            logger.exception("Error sending WhatsApp message via Custom Gateway: %s", e)
            return False

    else:
        logger.error("Unsupported WhatsApp provider configured: %s", provider)
        return False


def send_admission_notification(student):
    """
    Format and send WhatsApp message to a student upon successful admission.
    """
    phone = student.mobile_own or student.parent_mobile
    if not phone:
        logger.warning("No mobile number available for admitted student ID %s", student.id)
        return False

    config = get_whatsapp_settings()
    template = config["admission_template"]

    course_name = student.course
    if student.course == "Other" and student.custom_course:
        course_name = student.custom_course

    message = template.format(
        student_name=student.full_name,
        course_name=course_name,
        student_id=student.student_id
    )
    return send_whatsapp_message(phone, message)


def send_payment_notification(payment):
    """
    Format and send WhatsApp receipt message to a student upon recording fee payment.
    """
    student = payment.student
    phone = student.mobile_own or student.parent_mobile
    if not phone:
        logger.warning("No mobile number available for student ID %s associated with payment %s", student.id, payment.receipt_no)
        return False

    config = get_whatsapp_settings()
    template = config["payment_template"]

    course_name = student.course
    if student.course == "Other" and student.custom_course:
        course_name = student.custom_course

    message = template.format(
        student_name=student.full_name,
        course_name=course_name,
        amount=payment.amount,
        receipt_no=payment.receipt_no,
        remaining_fees=payment.remaining_after_this
    )
    return send_whatsapp_message(phone, message)


def send_enquiry_notification(enquiry):
    """
    Format and send WhatsApp message to a user after submitting an enquiry.
    """
    phone = enquiry.mobile
    if not phone:
        logger.warning("No mobile number available for enquiry ID %s", enquiry.id)
        return False

    config = get_whatsapp_settings()
    template = config["enquiry_template"]

    course_name = enquiry.get_display_course()
    institute_name = getattr(settings, "INSTITUTE_NAME", "Shri Samarth Computer Education")
    contact_number = getattr(settings, "INSTITUTE_CONTACT", "9876543210")

    try:
        message = template.format(
            student_name=enquiry.name,
            course_name=course_name,
            institute_name=institute_name,
            contact_number=contact_number
        )
    except KeyError as e:
        logger.error("Template formatting key error for enquiry: %s", e)
        message = template
    return send_whatsapp_message(phone, message)


def send_absent_notification(student, date_obj, batch_time, batch_type):
    """
    Format and send WhatsApp message to a student marked absent today.
    """
    phone = student.mobile_own or student.parent_mobile
    if not phone:
        logger.warning("No mobile number available for absent student %s", student.full_name)
        return False

    config = get_whatsapp_settings()
    template = config["absent_template"]

    date_str = date_obj.strftime("%d-%m-%Y") if hasattr(date_obj, "strftime") else str(date_obj)

    try:
        message = template.format(
            student_name=student.full_name,
            date=date_str,
            batch_time=batch_time or "N/A",
            batch_type=batch_type or "Regular"
        )
    except KeyError as e:
        logger.error("Template formatting key error for absent student: %s", e)
        message = template
    return send_whatsapp_message(phone, message)
