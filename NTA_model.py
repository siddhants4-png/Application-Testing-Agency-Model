import pandas as pd #This is library to make dataframes and show data properly (Written By Siddhant Shah
import os #This library connects with OS to bring the file and check whaeter exists or not(By Siddhant Shah)
from datetime import datetime #This is for giving the date and time stamp(By Siddhant Shah)
import qrcode #This is for genrating the QR code(By siddhant Shah)
import smtplib #This is for sending email(By siddhant Shah)
from email.message import EmailMessage #This is for structuring the email(By Siddhant Shah)
from PIL import Image # This is for the png image generation of QR code in this code.(By Siddhant Shah)
import requests # This is for requesting to the API(By Siddhant Shah)
import shutil # This is for copying files(By siddhant Shah)
from pathlib import Path #This is for finding the download folder(By Siddhant shah)
import random # This is used to make the random code for the use of OTP(By Siddhant Shah)
import hashlib #This is used to hide the password(By Siddhant Shah)
from dotenv import load_dotenv #This will call env file so that all essential and important things are kept safe.(By siddhant shah)
print(f"Script is running from this folder: {os.getcwd()}")
print(f"Does the .env file exist here? {os.path.exists('.env')}")
load_dotenv()

FILE_NAME = "STA_Model.xlsx"
EXAM_CENTERS = "STA_Center.xlsx"
APPLICATION_NAME = "application Number.txt"
APPLICATION_TRANSACTION = "Application NTA.txt"
ADMIN_PASSWORD = os.getenv("ADMIN_PASS")
print(f"--- DEBUG: Loaded admin password is: '{ADMIN_PASSWORD}' ---")
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns = ["Applicant Name", "State", "Birthdate", "Application Number",
        "Email", "Phone", "Status", "Fees Paid", "Password", "Exam Center", "Exam Date", "Exam slot", "Exam Time", "QR Path", "QR Approved"])
    df = df.astype({
        "Application Number": str,
        "Email": str,
        "Phone": str
    })
    df.to_excel(FILE_NAME, index=False)
if not os.path.exists(EXAM_CENTERS):
    center_df = pd.DataFrame(columns=["Center Name", "State Pin Code", "Capacity", "Assigned Count"])
    center_df = center_df.astype({"State Pin Code": str, "Capacity": int, "Assigned Count": int})
    center_df.to_excel(EXAM_CENTERS, index=False)
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
    api_key = os.getenv("SMS_API_KEY")
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
    df = pd.read_excel(FILE_NAME, dtype={"Application Number": str})
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
        mask = df["Application Number"]== key
    elif choice == "2":
        key = input("Enter Email to remove: ").strip().lower()
        mask = df["Email"].str.lower() == key
    elif choice == "3":
        key = input("Enter Phone Number to remove: ").strip()
        mask = df["Phone"].astype(str) == key
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
        df["Application Number"] = df["Application Number"].astype(str)
        df.to_excel(FILE_NAME, index=False)
        print("Application(s) successfully removed")
    else:
        print("Deletion cancelled.")
        
def assign_exam_centers():
    if not os.path.exists(FILE_NAME):
        print("No application data found.")
        return
    if not os.path.exists(EXAM_CENTERS):
        print("No exam center data found.")
        return
    df = pd.read_excel(FILE_NAME, dtype={"Application Number": str})
    centers_df = pd.read_excel(EXAM_CENTERS, dtype={"State Pin Code": str})
    unassigned = df[df["Exam Center"].isna() | (df["Exam Center"] == "")]
    if unassigned.empty:
        print("\n All applicants alredy have assigned exam centers.")
        return
    print("\nUnassigned Applicants: ")
    print(unassigned[["Applicant Name", "Application Number","Email", "Phone", "State"]].to_string(index=False))
    app_no = str(input("\nEnter the Application Number to assign: ").strip())
    if app_no not in df["Application Number"].values:
        print("Application number not found.")
        return
    user = df.loc[df["Application Number"]==app_no].iloc[0]
    user_state_pin = str(user['State'])
    available_centers = centers_df[
        (centers_df['State Pin Code'] == user_state_pin)&
        (centers_df['Assigned Count']< centers_df['Capacity'])
    ]
    if available_centers.empty:
        print(f"\nNo available exam centers found for state pin code {user_state_pin}.")
        return
    print(f"\nAvailable Centers for State Pin {user_state_pin}:")
    print(available_centers[['Center Name', 'Capacity', 'Assigned Count']].to_string(index=False))
    exam_center = input("Enter Exam Center Name from the list above: ").strip()
    chosen_center_mask = available_centers['Center Name'].str.lower() == exam_center.lower()
    if not chosen_center_mask.any():
        print("Invalid Center name")
        return
    exam_date = input("Enter Exam Date (DD-MM-YYYY): ").strip()
    exam_slot = input("Enter Exam slot(Slot1/Slot2): ").strip().capitalize()
    exam_times = {
        "Slot1": "9:00 AM - 12:00 PM",
        "Slot2": "3:00 PM - 6:00 PM"
        }
    exam_time = exam_times.get(exam_slot, "TBD")
    df.loc[df["Application Number"] == app_no, ["Exam Center", "Exam Date", "Exam Slot", "Exam Time"]] = [exam_center, exam_date, exam_slot, exam_time]
    df["Application Number"] = df["Application Number"].astype(str)
    df.to_excel(FILE_NAME, index=False)
    print(f"\n Exam center assigned successfully to {app_no}.")
    center_index = centers_df[
        (centers_df['Center Name'].str.lower() == exam_center.lower())&
        (centers_df['State Pin Code'] == user_state_pin)
    ].index
    centers_df.loc[center_index, 'Assigned Count'] += 1
    centers_df.to_excel(EXAM_CENTERS, index=False)
    new_count = centers_df.loc[center_index, 'Assigned Count'].iloc[0]
    print(f"Updated center capacity: '{exam_center}' now has {new_count} student(s) assigned.")
    user = df.loc[df["Application Number"]== app_no].iloc[0]
    qr_data = (
        f"STA Admit Card\n"
        f"Name: {user['Applicant Name']}\n"
        f"Application: {user['Application Number']}\n"
        f"Center: {user['Exam Center']}\n"
        f"Date: {user['Exam Date']}\n"
        f"Time: {user['Exam Time']}"
    )
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_colour="black", back_colour="white")
    qr_path = f"STA_QR_{user['Application Number']}.png"
    qr_img.save(qr_path)
    df.loc[df["Application Number"]== app_no, ["QR Path", "QR Approved"]] = [qr_path, "No"]
    df["Application Number"] = df["Application Number"].astype(str)
    df.to_excel(FILE_NAME, index = False)
    print("\n TBD Keep checking")
def get_next_application_number(state_pin_code, birthdate):
    key = f"25{state_pin_code}{birthdate}"
    next_serial = 1  
    if os.path.exists(APPLICATION_NAME):
        with open(APPLICATION_NAME, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            for line in lines:
                if line.startswith(key):
                    try:
                        serial_part = int(line[len(key):])
                        if serial_part >= next_serial:
                            next_serial = serial_part + 1
                    except ValueError:
                        continue
    application_number = f"{key}{next_serial:03d}"
    with open(APPLICATION_NAME, "a") as f:
        f.write(application_number + "\n")
    return application_number    
def send_email(user_email, subject, body, attachment=None):
    MY_EMAIL = os.getenv("GMAIL_EMAIL")
    MY_PASSWORD = os.getenv("GMAIL_PASSWORD")
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = MY_EMAIL
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
            smtp.login(MY_EMAIL, MY_PASSWORD)
            smtp.send_message(msg)
        print(f"Email sent to {user_email}")
    except Exception as e:
       print(f"Failed to send email: {e}")
def complete_registration(name, state, birthdate, email, phone):
    df = pd.read_excel(FILE_NAME, dtype={"Application Number": str})
    application_number = get_next_application_number(state, birthdate)
    print(f"\nPayment Confirmed.")
    print(f"Your Application Number is: {application_number}")
    password = input("Set Your Password: ")
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    new_entry = {
        "Applicant Name": name,
        "State": state,
        "Birthdate": birthdate,
        "Application Number": application_number,
        "Email": email,
        "Phone": phone,
        "Status": "Paid",
        "Fees Paid": "Rs. 1000",
        "Password": hashed_password,
        "Exam Center": "",
        "Exam Date": "",
        "Exam Slot": "",
        "Exam Time": ""
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index = True)
    df["Application Number"] = df["Application Number"].astype(str)
    df.to_excel(FILE_NAME, index=False)
    log_transaction(application_number, "Fees Paid", 1000)
    body = (
        f"Dear {name},\n\n"
        f"You have been Successfully registered.\n"
        f"Your Application Number: {application_number}\n"
        f"Keep checking periodically for the updates using user login.\n\n"
        f"Best Of Luck,\nSTA Testing Agency"
    )
    send_email(email, "Application Confirmation", body)
    sms_message = (
    f"Dear {name}, your STA Application ({application_number}) has been successfully registered. "
    f"You can now login in using your application number and password."
    )
    
    send_sms(phone, sms_message)
    
def user_login():
    if not os.path.exists(FILE_NAME):
        print("No registered user found.")
        return
    df = pd.read_excel(FILE_NAME, dtype={"Application Number": str})
    if df.empty:
        print("No registered users found.")
        return
    print("\n==========User Login==========")
    application_number = input("Enter Your Application Number(type 'F' to reset password): ").strip()
    if application_number.upper() == 'F':
        forgot_password()
        return
    password = input("Enter Your Password: ")
    user = df.loc[df["Application Number"] == application_number]
    hashed_input = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if user.empty:
        print("Invalid Application Number.")
        return
    stored_hash = str(user.iloc[0]["Password"]).strip()
    if stored_hash != hashed_input:
        print("Incorrect Password.")
        return
    print(f"\n Welcome, {user.iloc[0]['Applicant Name']}!\n")
    if pd.isna(user.iloc[0]['Exam Center']) or user.iloc[0]['Exam Center'] == "":
        print("Your exam center has not been assigned yet.Please check back later.")
    else:
        display_df = user[[
            "Application Number",
            "Applicant Name",
            "Exam Center",
            "Exam Date",
            "Exam Slot",
            "Exam Time"
        ]]
        print("Your Examination Details:\n")
        print(display_df.to_string(index=False))
        qr_path = user.iloc[0].get("QR Path", None)
        qr_approved = user.iloc[0].get("QR Approved", "No")
        if qr_approved == "Yes" and pd.notna(qr_path) and os.path.exists(qr_path):
            print(" Your Admit Card QR is ready. Opening QR Code...")
            img = Image.open(qr_path)
            img.show()
            print("\n-----Download Admit Card-----")
            download_choice = input("Download Admit Card.(Press Y to download): ").strip().lower()
            if download_choice == 'y':
                try:
                    download_folder = str(Path.home()/"Downloads")
                    file_name = os.path.basename(qr_path)
                    destination_path = os.path.join(download_folder, file_name)
                    shutil.copy(qr_path, destination_path)
                    print(f"\nSuccessfully saved! Your admit card is in:")
                    print(destination_path)
                except Exception as e:
                    print(f"\nAn error occured while Saving: {e}")
                    print(f"You can find your admit card file in the script's folder:{os.path.abspath(qr_path)}")
            else:
                print("\nYour Admit Card QR is not yet approved. Please check again or contact STA Helpline")
            
    print("\nYou have been logged out automatically for security.\n")
def forgot_password():
    print("\n----Password Reset----")
    if not os.path.exists(FILE_NAME):
        print("No registered user data found.")
        return
    df = pd.read_excel(FILE_NAME, dtype={"Application Number": str, "Email": str, "Phone": str})
    app_no = input("Enter your Application Number for Verification: ").strip()
    user_mask = df["Application Number"] == app_no
    if not user_mask.any():
        print("Application Number not found. Please try again.")
        return
    user_data = df.loc[user_mask].iloc[0]
    user_email= user_data['Email']
    otp = str(random.randint(100000, 999999))
    print(f"Sending OTP to your registered email: {user_email}...")
    email_subject = "STA - Password Reset OTP"
    email_body = (
        f"Dear {user_data['Applicant Name']},\n\n"
        f"Your One-Time Password(OTP) for resetting your password is: \n\n"
        f"**{otp}**\n\n"
        f"This OTP is valid for 5 minutes.\n\n"
        f"Regards,\nSTA Agency"
    )
    send_email(user_email, email_subject, email_body)
    print("OTP sent successfully")
    entered_otp = input("Enter the 6-digit OTP: ").strip()
    if entered_otp == otp:
        print("OTP Verified Successfully.")
        new_password = input("Enter new password: ").strip()
        confirm_password = input("Confirm your new password: ").strip()
        if new_password == confirm_password:
            hashed_password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            df.loc[user_mask, "Password"] = hashed_password
            df.to_excel(FILE_NAME, index=False)
            print("\nPassword has been reset successfully.")
            print("You can now log in with your new password.")
        else:
            print("Passwords do not match. Password reset failed.")
    else:
        print("Incorrect OTP. Password reset failed.")
def user_registration():
    name, state, birthdate, email, phone = collect_user_data()
    df = pd.read_excel(FILE_NAME, dtype={"Phone": str, "Email": str})
    clean_phone = str(phone).strip()
    clean_email = str(email).strip().lower()
    phone_exists = df['Phone'].astype(str) == clean_phone
    if phone_exists.any():
        print(f"\n--- REGISTRATION FAILED ---")
        print(f"The phone number '{phone}' is already registered in our system.")
        print("You cannot register a new application with this phone number.")
        print("Please try logging in or contact support if you believe this is an error.")
        return
    email_exists = df['Email'].str.lower() == clean_email
    if email_exists.any():
        print(f"\n--- REGISTRATION FAILED ---")
        print(f"The email address '{email}' is already registered in our system.")
        print("You cannot register a new application with this email address.")
        print("Please try logging in or contact support if you believe this is an error.")
        return
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
        print("3. Back to main menu")
        print("4. Remove Repeated Application")
        print("5. Assign Exam Centers")
        print("6. Approve Admit Cards")
        print("7.View all Exam Centers")
        choice = input("Enter Your choice: ")
        if choice == "1":
            if os.path.exists(FILE_NAME):
                df = pd.read_excel(FILE_NAME, dtype={"Application Number": str})
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
        elif choice == "5":
            assign_exam_centers()
        elif choice == "6":
            df = pd.read_excel(FILE_NAME, dtype={"Application Number": str})
            pending = df[df["QR Approved"].isna()|(df["QR Approved"]=="No")]
            if pending.empty:
                print("No pending QR codes for approval.")
            else:
                print("\n Pending Admit Cards for approval: ")
                print(pending[["Applicant Name", "Application Number", "Email", "Exam Center"]].to_string(index=False))
                approve_app_no = input("\nEnter Application Number To Approve: ").strip()
                if approve_app_no in df["Application Number"].values:
                    user = df.loc[df["Application Number"]==approve_app_no].iloc[0]
                    qr_path = user.get("QR Path","")
                    if not qr_path or not os.path.exists(qr_path):
                        print("QR Path not found, regenerating...")
                        qr_data = (
                            f"STA Admit Card\n"
                            f"Name: {user['Applicant Name']}\n"
                            f"Application: {user['Application Number']}\n"
                            f"Center: {user['Exam Center']}\n"
                            f"Date: {user['Exam Date']}\n"
                            f"Time: {user['Exam Time']}"
                        )
                        qr = qrcode.QRCode(
                            version=1,
                            error_correction=qrcode.constants.ERROR_CORRECT_H,
                            box_size=10,
                            border=4
                        )
                        qr.add_data(qr_data)
                        qr.make(fit=True)
                        qr_img = qr.make_image(fill_color="black", back_color="white")
                        qr_path = f"STA_QR_{user['Application Number']}.png"
                        qr_img.save(qr_path)
                        df.loc[df["Application Number"] == approve_app_no, "QR Path"] = qr_path
                    df.loc[df["Application Number"] == approve_app_no, "QR Approved"] = "Yes"   
                    df["Application Number"] = df["Application Number"].astype(str)   
                    df.to_excel(FILE_NAME, index=False)
                    print(f"\nQR code approved for application number{approve_app_no}")
                    print(f"Sending notification to {user['Applicant Name']}...")
                    email_subject=f"Your STA Admit Card is Released(Application: {approve_app_no})"
                    email_body = (
                        f"Dear {user['Applicant Name']},\n\n"
                        f"Your admit card for the STA exam (Application Number: {user['Application Number']}) has been approved and is now available.\n\n"
                        f"Your admit card's QR code is attached to this email. You will need to show this at the exam center.\n"
                        f"Please keep this secure and do not share it.\n\n"
                        f"WIshing You All the Best!!,\nSTA Agency"
                    )
                    send_email(user['Email'], email_subject, email_body, qr_path)
                    sms_message = (
                        f"Dear {user['Applicant Name']}, Your STA Admit Card is released and sent to your registered email-id.Please do check it and login to download."
                    )
                    send_sms(user['Phone'], sms_message)
                    print("Notification sent successfully.")
                    img = Image.open(qr_path)
                    img.show()
                else:
                    print("Invalid application number.")
        elif choice == "7":
            if os.path.exists(EXAM_CENTERS):
                centers_df = pd.read_excel(EXAM_CENTERS, dtype={"State Pin Code": str})
                print("\n Registered Exam Centers: ")
                print(centers_df.to_string(index=False))
        else:
            print("Invalid Choice.")
def center_registration():
    print("\n==========Exam Center Registration==========")
    center_name = input("Enter Center Name: ").strip()
    state_pin_code = input("Enter State Pin Code: ").strip()
    try:
        capacity = int(input("Enter Total Capacity: ").strip())
    except ValueError:
        print("Invalid capacity. Please enter a number.")
        return
    df = pd.read_excel(EXAM_CENTERS, dtype={"State Pin Code": str})
    expected_cols = ["Center Name","State Pin Code","Capacity","Assigned Count"]
    if list(df.columns)!= expected_cols:
        print("Center file appears empty or has incorrect headers.")
        df = pd.DataFrame(columns=expected_cols)
    mask = (df['Center Name'].str.lower() == center_name.lower()) & (df['State Pin Code'] == state_pin_code)
    if mask.any():
        print(f"\nError: A center with the name '{center_name}' is alredy registered")
        return
    new_center = {
        "Center Name": center_name,
        "State Pin Code": state_pin_code,
        "Capacity": capacity,
        "Assigned Count": 0
    }
    df = pd.concat([df, pd.DataFrame([new_center])], ignore_index=True)
    df["State Pin Code"] = df["State Pin Code"].astype(str)
    df["Capacity"] = df["Capacity"].astype(int)
    df["Assigned Count"] = df["Assigned Count"].astype(int)
    df.to_excel(EXAM_CENTERS, index=False)
    print(f"\n Center '{center_name}' has been registered with a capacity of '{capacity}' is registered Successfully.")
    
def show_duplicates():
    if not os.path.exists(FILE_NAME):
        print("No data found")
        return
    df = pd.read_excel(FILE_NAME, dtype={"Application Number": str})
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
        print("3. User Login")
        print("4. Center Registration")
        print("5. Exit")
        choice = input("Enter Your choice: ")
        if choice == "1":
            user_registration()
        elif choice == "2":
            admin_login()
        elif choice =="3":
            user_login()
        elif choice == "4":
            center_registration()
        elif choice == "5":
            print("Exiting the Program.....")
            print("Thank You, Have a nice Day")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
                        
