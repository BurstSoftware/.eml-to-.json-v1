import streamlit as st
import email
from email import policy
import json
import base64
from datetime import datetime
import io

st.set_page_config(page_title="EML to JSON Converter", layout="wide")
st.title("📧 EML to JSON Converter")
st.markdown("Upload `.eml` files and convert them to structured JSON.")

# Initialize session state
if "converted_emails" not in st.session_state:
    st.session_state.converted_emails = []  # list of dicts with filename and data

def parse_eml_to_dict(msg):
    """Parse email.message.Message into a clean dictionary."""
    email_dict = {
        "headers": {},
        "from": "",
        "to": "",
        "cc": "",
        "bcc": "",
        "subject": "",
        "date": "",
        "body": {"text": "", "html": ""},
        "attachments": []
    }

    # Headers
    for header in msg.keys():
        email_dict["headers"][header] = msg.get(header)

    # Common fields
    email_dict["from"] = msg.get("From", "")
    email_dict["to"] = msg.get("To", "")
    email_dict["cc"] = msg.get("Cc", "")
    email_dict["bcc"] = msg.get("Bcc", "")
    email_dict["subject"] = msg.get("Subject", "")

    # Date
    date_str = msg.get("Date")
    if date_str:
        try:
            dt = email.utils.parsedate_to_datetime(date_str)
            email_dict["date"] = dt.isoformat()
        except:
            email_dict["date"] = date_str

    # Body & Attachments
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", "")).lower()

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            charset = part.get_content_charset() or "utf-8"

            if content_type == "text/plain" and "attachment" not in disposition:
                try:
                    email_dict["body"]["text"] += payload.decode(charset, errors="replace")
                except:
                    email_dict["body"]["text"] += str(payload)

            elif content_type == "text/html" and "attachment" not in disposition:
                try:
                    email_dict["body"]["html"] += payload.decode(charset, errors="replace")
                except:
                    email_dict["body"]["html"] += str(payload)

            # Attachment
            elif "attachment" in disposition or part.get_filename():
                filename = part.get_filename() or "attachment.bin"
                attachment = {
                    "filename": filename,
                    "content_type": content_type,
                    "size_bytes": len(payload),
                    "content_base64": base64.b64encode(payload).decode("utf-8")
                }
                email_dict["attachments"].append(attachment)
    else:
        # Single part email
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    email_dict["body"]["html"] = text
                else:
                    email_dict["body"]["text"] = text
            except:
                pass

    return email_dict


# ====================== FILE UPLOADER ======================
uploaded_files = st.file_uploader(
    "Drop your .eml files here",
    type=["eml"],
    accept_multiple_files=True,
    help="You can upload multiple .eml files at once."
)

# ====================== CONVERT BUTTON ======================
if uploaded_files and st.button("🚀 Convert to JSON", type="primary"):
    st.session_state.converted_emails = []  # Reset previous results
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing: {uploaded_file.name}")
        try:
            msg = email.message_from_bytes(uploaded_file.getvalue(), policy=policy.default)
            email_data = parse_eml_to_dict(msg)

            st.session_state.converted_emails.append({
                "original_filename": uploaded_file.name,
                "json_filename": uploaded_file.name.replace(".eml", ".json").replace(" ", "_"),
                "data": email_data
            })
        except Exception as e:
            st.error(f"Failed to process {uploaded_file.name}: {e}")

        progress_bar.progress((i + 1) / len(uploaded_files))

    status_text.text("✅ Conversion complete!")
    st.success(f"✅ Successfully converted {len(st.session_state.converted_emails)} email(s)")
    st.balloons()

# ====================== DISPLAY CONVERTED FILES ======================
if st.session_state.converted_emails:
    st.subheader("📄 Converted JSON Files")

    for idx, item in enumerate(st.session_state.converted_emails):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{item['json_filename']}**")
        with col2:
            json_bytes = json.dumps(item["data"], ensure_ascii=False, indent=2).encode("utf-8")
            
            st.download_button(
                label="⬇️ Download JSON",
                data=json_bytes,
                file_name=item["json_filename"],
                mime="application/json",
                key=f"download_{idx}"
            )

        # Preview
        with st.expander(f"👁️ Preview — {item['json_filename']}", expanded=idx == 0):
            st.json(item["data"], expanded=False)

    st.divider()

# Instructions
with st.expander("ℹ️ How it works"):
    st.markdown("""
    1. Drop one or more `.eml` files  
    2. Click **Convert to JSON**  
    3. All JSON files appear below with **Download** buttons and previews  
    4. You can download any file anytime without converting again
    """)

st.caption("Built with Streamlit • Persistent results using session state")
