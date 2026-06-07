import streamlit as st
import email
from email import policy
import json
import base64
from datetime import datetime
import io

st.set_page_config(page_title="EML to JSON Converter", layout="wide")
st.title("📧 EML to JSON Converter")
st.markdown("Upload `.eml` email files and convert them to structured JSON.")

def parse_eml_to_dict(msg):
    """Parse an email.message.Message into a clean dictionary."""
    email_dict = {
        "headers": {},
        "from": "",
        "to": "",
        "cc": "",
        "bcc": "",
        "subject": "",
        "date": "",
        "body": {
            "text": "",
            "html": ""
        },
        "attachments": []
    }

    # Extract headers
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
            # Try to parse email date
            dt = email.utils.parsedate_to_datetime(date_str)
            email_dict["date"] = dt.isoformat()
        except:
            email_dict["date"] = date_str

    # Extract body and attachments
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        email_dict["body"]["text"] += payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    except:
                        email_dict["body"]["text"] += str(payload)

            elif content_type == "text/html" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        email_dict["body"]["html"] += payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    except:
                        email_dict["body"]["html"] += str(payload)

            # Attachments
            elif "attachment" in content_disposition or part.get_filename():
                filename = part.get_filename()
                if filename:
                    payload = part.get_payload(decode=True)
                    if payload:
                        attachment = {
                            "filename": filename,
                            "content_type": content_type,
                            "size_bytes": len(payload),
                            "content_base64": base64.b64encode(payload).decode("utf-8")
                        }
                        email_dict["attachments"].append(attachment)
    else:
        # Not multipart
        payload = msg.get_payload(decode=True)
        content_type = msg.get_content_type()
        if payload:
            try:
                text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
                if content_type == "text/html":
                    email_dict["body"]["html"] = text
                else:
                    email_dict["body"]["text"] = text
            except:
                pass

    return email_dict


# File uploader
uploaded_files = st.file_uploader(
    "Drop your .eml files here",
    type=["eml"],
    accept_multiple_files=True,
    help="You can upload multiple .eml files at once."
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

    if st.button("🚀 Convert to JSON", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing: {uploaded_file.name}")
            
            try:
                # Read file content
                eml_bytes = uploaded_file.getvalue()
                msg = email.message_from_bytes(eml_bytes, policy=policy.default)
                
                # Convert to dict
                email_data = parse_eml_to_dict(msg)
                
                # Convert to JSON
                json_str = json.dumps(email_data, ensure_ascii=False, indent=2)
                json_bytes = json_str.encode("utf-8")
                
                # Create nice filename
                safe_name = uploaded_file.name.replace(".eml", "").replace(" ", "_")
                json_filename = f"{safe_name}.json"
                
                # Show preview (first file only, or collapsible)
                if i == 0:
                    with st.expander("📋 Preview of first converted email (JSON)", expanded=True):
                        st.json(email_data, expanded=False)
                
                # Download button
                st.download_button(
                    label=f"⬇️ Download {json_filename}",
                    data=json_bytes,
                    file_name=json_filename,
                    mime="application/json",
                    key=f"download_{i}"
                )
                
            except Exception as e:
                st.error(f"❌ Failed to process {uploaded_file.name}: {str(e)}")
            
            # Update progress
            progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.text("✅ All files processed!")
        st.balloons()

# Instructions
with st.expander("ℹ️ How it works"):
    st.markdown("""
    1. Drop one or more `.eml` files
    2. Click **Convert to JSON**
    3. Download individual JSON files
    
    **JSON Structure includes:**
    - All email headers
    - Sender, recipients, subject, date
    - Plain text and HTML body
    - Attachments (base64 encoded)
    """)

st.caption("Built with ❤️ using Streamlit + Python email library")
