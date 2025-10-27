import pandas as pd
import os
from datetime import datetime
import qrcode
import smtplib
from email.message import EmailMessage
from PIL import Image
import requests

FILE_NAME = r"C:\Users\Home\Documents\STA_Model.xlsx"
APPLICATION_NAME = r"C:\Users\Home\Desktop\application Number.txt"
APPLICATION_TRANSACTION = r"C:\Users\Home\Desktop\Application NTA.txt"
ADMIN_PASSWORD = "admin123"

if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns = ["Applicant Name", "State", "Birthdate", "Application Number",
        "Email", "Phone", "Status", "Fees Paid", "Password"])
    df.to_excel(FILE_NAME, index=False)
def collect_user_data():
    print("\n=== User Registration ===")
    name = input("Full Name: ")
    state = input("State Pin Code: ")
    birthdate = input("Birthdate (DDMMYYYY): ")
    email = input("Email Address: ")
    phone = input("Phone Number: ")
    return name, state, birthdate, email, phone
def generate_qr(application_data, amount = 1000):
    data_string = (
        f"Application: {application_data['name']}\n"
        f"Email: {application_data['email']}\n"
        f"Amount: Rs.{amount}\nStatus: Paid"
    )
    img = qrcode.make(data_string)
    qr_path = f"qr_{application_data['email'].replace('@','_')}.png"
    img.save(qr_path)
    print(f"\n QR Code saved as: {qr_path}")
    print("Please Scan the QR to simulate payment.")
    img.show()
    return qr_path
def send_sms(phone_number, message_body):
    api_key = "m7Za59TitR3hULKWDj2AoF8pxeJGNz60IwBuMqryOg4YdbVcHELfdDkbT8KV36OUxQ4nv1hzjB2ACrIw"
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": api_key,
        "counter-type": "application/x-www-form-urlencoded"
    }
    payload = {
        "sender_id": "TXTIND",
        "message": message_body,
        "language": "english",
        "route":"q",
        "numbers": (phone_number if phone_number.startswith('+91') else f'91{phone_number} ')
    }
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            print(f"SMS sent successfully to {phone_number}")
        else:
            print(f"Failed to send SMS: {response.text}")
    except Exception as e:
        print(f"Error sending SMS: {e}")
        
def log_transaction(application_number, transaction_type, amount):
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    entry = f"[{timestamp}] Application Number: {application_number} | {transaction_type} | Amount: ₹{amount}"
    with open(APPLICATION_TRANSACTION, "a", encoding="utf-8") as f:
        f.write(entry + "\n")
def remove_application():
    if not os.path.exists(FILE_NAME):
        print("No application data found.")
        return
    df = pd.read_excel(FILE_NAME)
    if df.empty:
        print("No applicants to remove.")
        return

    print("\nCurrnet Registered Applicants: ")
    print(df[["Applicant Name", "Application Number", "Email", "Phone"]].to_string(index=False))
    print("\nRemove by:")
    print("1.Application Number")
    print("2. Email")
    print("3. Phone Number")
    choice = input("Enter Your Choice: ")
    if choice == "1":
        key = input("Enter Application Number to remove: ").strip()
        mask = df["Application Number"].astype(str) == key
    elif choice == "2":
        key = input("Enter Email to remove: ").strip().lower()
        mask = df["Email"].str.lower() == key
    elif choice == "3":
        key = input("Enter Phone Number to remove: ").strip()
        mask = df["phone"].astype(str) == key
    else:
        print("Invalid choice")
        return
    if not mask.any():
        print("No matching application found.")
        return
    print("\nMatched Records: ")
    print(df[mask].to_string(index=False))
    confirm = input("Are You sure you want to delete these records?(y/n):").lower()
    if confirm == "y":
        df = df[~mask]
        df.to_excel(FILE_NAME, index=False)
        print("Application(s) successfully removed")
    else:
        print("Deletion cancelled.")
    
def get_next_application_number(state_pin_code, birthdate):
    key = f"25{state_pin_code}{birthdate}"
    serial = 1
    if os.path.exists(APPLICATION_NAME):
        with open(APPLICATION_NAME, "r") as f:
            for line in f:
                if line.strip().startswith(key):
                    serial += 1
    application_number = f"{key}{serial:03d}"
    with open(APPLICATION_NAME, "a") as f:
        f.write(application_number + "\n")
    return application_number
def send_email(user_email, subject, body, attachment=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'siddhantmilinds@gmail.com'
    msg['To'] = user_email
    msg.set_content(body)
    if attachment:
        with open(attachment, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(attachment)
            msg.add_attachment(file_data, maintype = 'image', subtype = 'png', filename = file_name)
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login('siddhantmilinds@gmail.com', 'zsye viya esfd djuk')
            smtp.send_message(msg)
        print(f"Email sent to {user_email}")
    except Exception as e:
       print(f"Failed to send email: {e}")
def complete_registration(name, state, birthdate, email, phone):
    df = pd.read_excel(FILE_NAME)
    application_number = get_next_application_number(state, birthdate)
    print(f"\nPayment Confirmed.")
    print(f"Your Application Number is: {application_number}")
    password = input("Set Your Password: ")
    new_entry = {
        "Applicant Name": name,
        "State": state,
        "Birthdate": birthdate,
        "Application Number": application_number,
        "Email": email,
        "Phone": phone,
        "Status": "Paid",
        "Fees Paid": "Rs. 1000",
        "Password": password
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index = True)
    df.to_excel(FILE_NAME, index=False)
    log_transaction(application_number, "Fees Paid", 1000)
    body = (
        f"Dear {name},\n\n"
        f"You have been Successfully registered.\n"
        f"Your Application Number: {application_number}\n"
        f"Password: {password}\n\n"
        f"Best Of Luck,\nSTA Testing Agency"
    )
    send_email(email, "Application Confirmation", body)
    sms_message = (
    f"Dear {name}, your STA Application ({application_number}) has been successfully registered. "
    f"Password: {password}."
    )
    
    send_sms(phone, sms_message)

    
def user_registration():
    name, state, birthdate, email, phone = collect_user_data()
    qr_path = generate_qr({"name": name, "email": email})
    input("\n After Scanning and paying,press ENTER to continue....")
    complete_registration(name, state, birthdate, email, phone)

def admin_login():
    print("\n==========Admin Login==========")
    pwd = input("Enter admin password: ")
    if pwd != ADMIN_PASSWORD:
        print("Incorrect Password.")
        return
    while True:
        print("\n----------Admin Panel----------")
        print("1. View all Applicants")
        print("2. View Transaction History")
        print("3. Back to main menue")
        print("4. Remove Repeated Application")
        choice = input("Enter Your choice: ")
        if choice == "1":
            if os.path.exists(FILE_NAME):
                df = pd.read_excel(FILE_NAME)
                print("\n Registered Applicants: ")
                print(df.to_string(index=False))
            else:
                print("No data found.")
        elif choice == "2":
            if os.path.exists(APPLICATION_TRANSACTION):
                print("\n Transaction History: ")
                with open(APPLICATION_TRANSACTION, "r", encoding="utf-8") as f:
                    entries = f.readlines()
                    if entries:
                        for entry in entries:
                            print(entry.strip())
                    else:
                        print("No transaction history found.")
            else:
                print("No transaction history file found.")
        elif choice == "3":
            print("Exiting the System....")
            break
        elif choice == "4":
            remove_application()
        else:
            print("Invalid Choice.")
def show_duplicates():
    if not os.path.exists(FILE_NAME):
        print("No data found")
        return
    df = pd.read_excel(FILE_NAME)
    duplicates = df[df.duplicated(subset=["Email", "Phone"], keep=False)]
    if duplicates.empty:
        print("No duplicate application found.")
    else:
        print("\nDuplicate Applications Found:")
        print(duplicates.to_string(index=False))

def main():
    while True:
        print("\n==========Siddhant Testing Agency(STA)==========")
        print("1. User Registration")
        print("2. Admin Login")
        print("3. Exit")
        choice = input("Enter Your choice: ")
        if choice == "1":
            user_registration()
        elif choice == "2":
            admin_login()
        elif choice == "3":
            print("Exiting the Program.....")
            print("Thank You, Have a nice Day")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
                        
