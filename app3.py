import requests

# SMTP2Go API parameters
API_URL = "https://api.smtp2go.com/v3/email/send"
API_KEY = "api-43E83469CC704967918416A4701A050C"  # Replace with your actual API key
SENDER_EMAIL = "jorge.prado@royalexpressinc.com"
RECIPIENT_EMAIL = "revigor5@gmail.com"

print("Testing")

def send_email():
    # Email content
    email_data = {
        "api_key": API_KEY,
        "to": [RECIPIENT_EMAIL],
        "sender": SENDER_EMAIL,
        "subject": "Visitor Notification",
        "text_body": "A visitor has signed in and selected a department.",
        "html_body": "<p>A visitor has signed in and selected a department.</p>",
    }

    # Send request
    response = requests.post(API_URL, json=email_data)
    if response.status_code == 200:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email: {response.status_code}, {response.text}")

if __name__ == "__main__":
    send_email()
