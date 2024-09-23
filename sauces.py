import uiautomator2 as u2
import requests
import time
import random
import string
import re
import threading
from rich.console import Console
from rich.panel import Panel
from retrying import retry
from threading import Lock

# Initialize rich console and a lock for thread-safe outputs
console = Console()
console_lock = Lock()

# Connect to the device using uiautomator2
device = u2.connect()

# Global flags for tracking task status
task_completed = False
otp_extracted = False

# Retry decorator for automatic retries on failure
@retry(stop_max_attempt_number=3, wait_fixed=500)
def retry_on_failure(func, *args, **kwargs):
    return func(*args, **kwargs)

# Function to display rich panels with custom messages (thread-safe output)
def show_panel(title, content, style="bold green"):
    with console_lock:
        console.print(Panel(content, title=title, style=style))

# Function to close any open settings or windows
def close_open_windows():
    show_panel("Closing Windows", "Closing any open windows...")
    for _ in range(5):
        if device.press("back"):
            time.sleep(0.1)
        else:
            break
    console.log("[green]All open windows closed.\n")

# Function to stop the app
def close_app():
    show_panel("Closing App", "Stopping the app...")
    device.app_stop("io.sauces.app")
    time.sleep(0.1)
    console.log("[green]App closed.\n")

# Function to wait for an element and return it
def wait_for_element(selector, timeout=5, interval=0.05, retry_until_found=False):
    start_time = time.time()
    while True:
        element = device(**selector)
        if element.exists:
            return element
        if not retry_until_found and time.time() - start_time > timeout:
            raise Exception(f"Element {selector} not found within {timeout} seconds.")
        time.sleep(interval)

# Function to clear app data via UI automation
def clear_app_data_ui():
    show_panel("Clearing Data", "Clearing app data using UI automation...")
    close_app()

    # Long press on app icon and navigate to app info
    app_icon = retry_on_failure(wait_for_element, {'text': 'Sauces'}, retry_until_found=True)
    app_icon.long_click(duration=0.5)

    app_info = retry_on_failure(wait_for_element, {'text': 'App info'}, retry_until_found=True)
    app_info.click()

    # Navigate to Storage usage and clear data
    storage_usage = retry_on_failure(wait_for_element, {'text': 'Storage usage'}, retry_until_found=True)
    storage_usage.click()

    clear_data_button = retry_on_failure(wait_for_element, {'text': 'Clear data'}, retry_until_found=True)

    if clear_data_button.info['enabled']:
        clear_data_button.click()
        delete_button = retry_on_failure(wait_for_element, {'text': 'Delete'}, retry_until_found=True)
        delete_button.click()
    else:
        show_panel("Skipping", "Data already cleared.", style="bold yellow")

    console.log("[green]App data cleared successfully.\n")

# Function to generate a random nickname of letters and digits
def generate_random_nickname(length=9):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# Function to retrieve a temporary email address
def get_temp_email():
    response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
    if response.status_code == 200:
        email_address = response.json()[0]
        show_panel("Temporary Email", f"Generated temporary email: {email_address}")
        return email_address
    else:
        raise Exception("Failed to retrieve temporary email.")

# Function to extract OTP from the temporary email
def get_otp(email):
    global otp_extracted
    domain = email.split('@')[1]
    username = email.split('@')[0]

    show_panel("OTP Retrieval", f"Waiting for OTP at {username}@{domain}...")

    retry_interval = 2
    max_retries = 20

    for attempt in range(max_retries):
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
                        otp_extracted = True
                        show_panel("OTP Extracted", f"Extracted OTP: {otp}")
                        return otp
        time.sleep(retry_interval)

    raise Exception("Failed to retrieve OTP within the timeout period.")

# Function to set text in a field and verify
def set_text_reliably(field, text, field_name="field"):
    for attempt in range(2):
        field.set_text(text)
        time.sleep(0.1)
        if field.get_text() == text:
            show_panel("Text Input", f"Entered text '{text}' into {field_name}.")
            return True
    raise Exception(f"Failed to enter text '{text}' into {field_name}.")

# Function to click buttons and verify screen transition
def click_button_and_verify(text, expected_text=None):
    button = retry_on_failure(wait_for_element, {'text': text}, retry_until_found=True)
    button.click()
    time.sleep(0.5)

    if expected_text:
        if not device(text=expected_text).exists:
            show_panel("Warning", f"'{text}' click might not have registered. Retrying...", style="bold yellow")
            button.click()
            time.sleep(0.5)
            if not device(text=expected_text).exists:
                raise Exception(f"Failed to transition after clicking '{text}'.")

# Function to handle any possible errors on the screen
def handle_possible_errors():
    if device(text="The code has been expired").exists:
        show_panel("Expired OTP", "OTP expired. Restarting the process...", style="bold red")
        close_app()
        clear_app_data_ui()
        automate_referral()
    elif device(text="Try again later").exists:
        show_panel("Limit Reached", "Account creation limit reached. Retrying...", style="bold red")
        return False
    return True

# Main automation function
def automate_referral():
    temp_email = get_temp_email()

    # Start the app
    device.app_start("io.sauces.app")

    # Enter the temporary email
    email_field = retry_on_failure(wait_for_element, {'className': "android.widget.EditText"}, retry_until_found=True)
    set_text_reliably(email_field, temp_email, "email field")

    # Log in
    click_button_and_verify("Log in / Sign up")

    # Wait for OTP and enter it
    otp_code = get_otp(temp_email)
    if otp_extracted:
        otp_fields = retry_on_failure(wait_for_element, {'className': "android.widget.EditText"}, retry_until_found=True)
        set_text_reliably(otp_fields, otp_code, "OTP field")

    if not handle_possible_errors():
        return

    # Click "Next Step" four times, then click "Not Now"
    for _ in range(4):
        click_button_and_verify("Next Step", expected_text="Next Step")
    click_button_and_verify("Not now")

    # Enter random nickname
    random_nickname = generate_random_nickname()
    nickname_field = retry_on_failure(wait_for_element, {'className': "android.widget.EditText"}, retry_until_found=True)
    set_text_reliably(nickname_field, random_nickname, "nickname field")
    click_button_and_verify("Next Step")

    # Enter referral code and click "Complete"
    referral_code = "iemtejas"
    referral_field = retry_on_failure(wait_for_element, {'className': "android.widget.EditText"}, retry_until_found=True)
    set_text_reliably(referral_field, referral_code, "referral field")
    click_button_and_verify("Complete")

    show_panel("Process Complete", "Referral process completed successfully!", style="bold green")

# Loop the automation for specified iterations
def run_in_loop(iterations=100):
    for i in range(iterations):
        show_panel(f"Iteration {i+1}", f"Starting iteration {i+1}/{iterations}.")
        try:
            clear_app_data_ui()
            automate_referral()
        except Exception as e:
            show_panel("Error", f"Error during iteration {i+1}: {str(e)}", style="bold red")
        finally:
            close_app()
            close_open_windows()

# Start the automation loop for 100 iterations
run_in_loop(iterations=100)
