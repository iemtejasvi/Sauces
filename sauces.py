import uiautomator2 as u2
import time
import requests
import re
import random
import string

# Connect to the device
print("Connecting to device...")
device = u2.connect()
print("✅ Connected successfully.")

# Utility Functions
def get_temp_email():
    response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
    if response.status_code == 200:
        email_address = response.json()[0]
        print(f"Generated temporary email: {email_address}\n")
        return email_address
    else:
        raise Exception("Failed to retrieve temporary email.")

def get_otp(email):
    domain = email.split('@')[1]
    username = email.split('@')[0]
    print(f"Waiting for OTP email at {username}@{domain}...")
    retry_interval = 2
    max_retries = 20

    for _ in range(max_retries):
        response = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}")
        if response.status_code == 200:
            messages = response.json()
            if messages:
                msg_id = messages[0]['id']
                response = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={msg_id}")
                if response.status_code == 200:
                    message_body = response.json().get('textBody', '') or response.json().get('htmlBody', '')
                    otp_match = re.search(r'\b\d{3}\b', message_body)
                    if otp_match:
                        otp = otp_match.group(0)
                        print(f"Extracted OTP: {otp}\n")
                        return otp
        time.sleep(retry_interval)

    raise Exception("Failed to retrieve OTP within timeout period.")

def wait_for_element(selector, retry_until_found=False, timeout=20):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if device(**selector).exists:
            return device(**selector)
        time.sleep(1)
    if retry_until_found:
        raise Exception(f"Element {selector} not found within timeout.")
    return None

def set_text_reliably(element, text, label):
    try:
        element.clear_text()
        time.sleep(0.5)
        element.set_text(text)
        time.sleep(1)  # Ensure input stabilizes
        if element.get_text() == text:
            print(f"✅ Entered text in {label}.")
        else:
            print(f"❌ Text in {label} is incorrect: {element.get_text()}")
    except Exception as e:
        print(f"❌ Failed to set text in {label}: {e}")

def click_button_and_verify(button_text, timeout=20):
    """
    Wait for the button to load and click it, ensuring it exists before clicking.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        button = device(text=button_text)
        if button.exists:
            button.click()
            time.sleep(0.5)  # Faster UI transition allowance
            print(f"✅ Clicked on button: {button_text}")
            return
        time.sleep(0.5)  # Check again quickly
    raise Exception(f"❌ Button '{button_text}' not found within timeout.")

def generate_random_nickname(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# Steps
def clear_app_data(app_name):
    device.press("home")
    print("🔄 Returning to home screen...")
    time.sleep(1)

    device(text=app_name).long_click()
    time.sleep(1)

    device(text="App info").click()
    time.sleep(1)

    device(text="Storage usage").click()
    time.sleep(1)

    if device(textContains="0 B").exists:
        print("✅ Data is already cleared (0B).")
        device.press("home")
        return

    clear_data_button = device(text="Clear data")
    if clear_data_button.exists:
        clear_data_button.click()
        time.sleep(1)
        if device(text="Delete").exists:
            device(text="Delete").click()
            print("✅ Data cleared successfully.")
        else:
            print("❌ 'Delete' button not found.")
    else:
        print("❌ 'Clear data' button not clickable.")

    device.press("home")

def handle_next_steps():
    """
    Handles the sequence of clicking "Next Step" 4 times and "Not now" once.
    Optimized for faster subsequent clicks after the first.
    """
    try:
        # Click "Next Step" button four times
        for i in range(4):
            retry_timeout = 20 if i == 0 else 5  # Full timeout for the first click, faster retries for the rest
            print(f"🔄 Waiting for 'Next Step' button... (Step {i+1}/4)")
            click_button_and_verify("Next Step", timeout=retry_timeout)
            print(f"✅ Completed 'Next Step' {i+1}/4.")

        # Click "Not now" button
        print("🔄 Waiting for 'Not now' button...")
        click_button_and_verify("Not now", timeout=5)  # Faster retry for "Not now"
        print("✅ Completed 'Not now' action.")
    except Exception as e:
        print(f"❌ Error during 'Next Step' or 'Not now': {e}")

def enter_nickname_and_next():
    random_nickname = generate_random_nickname()
    print(f"Generated nickname: {random_nickname}")
    nickname_field = wait_for_element({'className': "android.widget.EditText"}, retry_until_found=True)
    set_text_reliably(nickname_field, random_nickname, "nickname field")

    click_button_and_verify("Next Step")
    time.sleep(2)  # Ensure referral window loads properly

def enter_referral_and_complete():
    referral_code = "naveen012"
    referral_field = wait_for_element({'className': "android.widget.EditText"}, retry_until_found=True)
    set_text_reliably(referral_field, referral_code, "referral field")

    click_button_and_verify("Complete")
    print("✅ Completed referral entry.")

# Main Script
def automate_registration(app_name, iterations=10000, timeout_per_iteration=50):
    for iteration in range(iterations):
        start_time = time.time()
        try:
            print(f"🚀 Starting iteration {iteration + 1}/{iterations}...")
            clear_app_data(app_name)

            print(f"🚀 Launching app: {app_name}...")
            device(text=app_name).click()
            time.sleep(5)

            temp_email = get_temp_email()
            email_field = wait_for_element({'className': "android.widget.EditText"}, retry_until_found=True)
            set_text_reliably(email_field, temp_email, "email field")
            click_button_and_verify("Log in / Sign up")

            otp_code = get_otp(temp_email)
            otp_fields = wait_for_element({'className': "android.widget.EditText"}, retry_until_found=True)
            set_text_reliably(otp_fields, otp_code, "OTP field")
            print("Entered OTP successfully.")

            handle_next_steps()
            enter_nickname_and_next()
            enter_referral_and_complete()

            elapsed_time = time.time() - start_time
            print(f"✅ Iteration {iteration + 1}/{iterations} completed in {elapsed_time:.2f} seconds.")

            # Check if iteration exceeded timeout
            if elapsed_time > timeout_per_iteration:
                print(f"⚠️ Iteration {iteration + 1} exceeded {timeout_per_iteration} seconds. Moving to next.")
        except Exception as e:
            print(f"❌ Error in iteration {iteration + 1}: {e}")
        finally:
            device.press("home")
            time.sleep(1)  # Ensure stabilization before next iteration

# Run the script
automate_registration("Sunwaves")
