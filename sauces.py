import uiautomator2 as u2  
import requests
import time
import random
import string
import re
import threading
import os

# Connect to the device
device = u2.connect()

# Define global flags
task_completed = False
otp_extracted = False

# Function to close any open settings or windows
def close_open_windows():
    print("Closing any open windows...")
    for _ in range(5):
        if device.press("back"):
            time.sleep(0.1)
        else:
            break
    print("All open windows closed.\n")

# Function to close the app
def close_app():
    print("Closing the app...")
    device.app_stop("io.doctorx.app")
    time.sleep(0.1)
    print("App closed.\n")

# Function to sanitize filenames
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Updated function to wait for an element with frequent checks for fast response
def wait_for_element(selector, timeout=5, interval=0.05, retry_until_found=False):
    start_time = time.time()
    while True:
        try:
            element = device(**selector)
            if element.exists:
                return element  
        except Exception as e:
            print(f"Encountered an error while waiting for element: {str(e)}")
        if not retry_until_found and time.time() - start_time > timeout:
            file_name = f"error_{sanitize_filename(selector.get('text', 'unknown'))}.png"
            device.screenshot(file_name)
            raise Exception(f"Element with selector {selector} not found within {timeout} seconds.")
        time.sleep(interval)

# Function to clear app data using UI automation
def clear_app_data_ui(retries=3):
    print("Clearing app data using UI automation...")
    for attempt in range(retries):
        try:
            close_app()

            # Long press on the "Sauces" app icon on the home screen
            app_icon = wait_for_element({'text': 'DoctorX'}, retry_until_found=True)
            app_icon.long_click(duration=0.5)

            # Wait and click on the "App info" option
            app_info = wait_for_element({'text': 'App info'}, retry_until_found=True)
            app_info.click()

            # Click on "Storage usage"
            storage_usage = wait_for_element({'text': 'Storage usage'}, retry_until_found=True)
            storage_usage.click()

            # Wait until "Clear data" button appears
            clear_data_button = wait_for_element({'text': 'Clear data'}, timeout=3, retry_until_found=True)

            # Check if data is already cleared (0B)
            if device(text="0B").exists:
                print("Data is already cleared (0B). Skipping to next step.\n")
                return

            # Click on "Clear data" if enabled
            if clear_data_button.info['enabled']:
                clear_data_button.click()

                # Confirm "Delete" if needed
                delete_button = wait_for_element({'text': 'Delete'}, retry_until_found=True)
                delete_button.click()
                print("App data cleared successfully.\n")
                return
            else:
                print("Clear data button is not clickable. Skipping to next step.\n")
                return

        except Exception as e:
            print(f"Error clearing app data: {str(e)}. Attempt {attempt + 1}/{retries} failed.\n")
            if attempt < retries - 1:
                print("Retrying to clear app data...\n")
                time.sleep(0.5)
            else:
                print("Failed to clear app data after multiple attempts.\n")
                raise

# Function to generate a random 9-character nickname (letters and digits)
def generate_random_nickname(length=9):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# Function to get a temporary email address
def get_temp_email():
    response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
    if response.status_code == 200:
        email_address = response.json()[0]
        print(f"Generated temporary email: {email_address}\n")
        return email_address
    else:
        raise Exception("Failed to retrieve temporary email.")

# Function to extract the OTP from temp email
def get_otp(email):
    global otp_extracted
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
                        otp_extracted = True
                        print(f"Extracted OTP: {otp}\n")
                        return otp
        time.sleep(retry_interval)

    raise Exception("Failed to retrieve OTP within timeout period.")

# Function to reliably set text in a field and verify it
def set_text_reliably(field, text, field_name="field"):
    for attempt in range(2):
        field.set_text(text)
        time.sleep(0.1)
        try:
            entered_text = field.get_text()
            if entered_text == text:
                print(f"Successfully entered text '{text}' into {field_name}.\n")
                return True
        except Exception as e:
            print(f"Error verifying text in {field_name}: {str(e)}")
        print(f"Retrying text entry '{text}' into {field_name} (Attempt {attempt + 2}/2)...")
    raise Exception(f"Failed to reliably enter text '{text}' into {field_name} after multiple attempts.")

# Function to detect specific error messages and handle them
def handle_possible_errors():
    try:
        if device(text="The code has been expired, please ask for new code").exists:
            print("Detected expired OTP. Restarting the process.")
            close_app()
            clear_app_data_ui()
            automate_referral()

        elif device(text="Try again later").exists or device(text="Cannot create account").exists:
            print("Account creation limit reached or temporary block. Retrying...")
            return False

        return True
    except Exception as e:
        print(f"Error while checking for possible errors: {str(e)}")
        return False

# Updated function to click a button and verify
def click_button_and_verify(text, expected_text=None):
    try:
        button = wait_for_element({'text': text}, retry_until_found=True)
        button.click()
        time.sleep(0.5)

        if expected_text:
            if device(text=expected_text).exists:
                print(f"Successfully clicked '{text}' and transitioned to the next screen.\n")
            else:
                print(f"'{text}' click might not have registered. Retrying...")
                button.click()
                time.sleep(0.5)
                if not device(text=expected_text).exists:
                    print(f"Button '{text}' click failed again. Taking screenshot and moving on.")
                    device.screenshot(f"error_{sanitize_filename(text)}_button.png")
        else:
            if not button.exists:
                print(f"Successfully clicked '{text}' and moved to the next screen.\n")
            else:
                print(f"'{text}' click might not have registered. Retrying...")
                button.click()
                time.sleep(0.5)
                if button.exists:
                    print(f"Button '{text}' click failed again. Taking screenshot and moving on.")
                    device.screenshot(f"error_{sanitize_filename(text)}_button.png")
    except Exception as e:
        device.screenshot(f"error_click_{sanitize_filename(text)}.png")
        print(f"Error clicking '{text}': {str(e)}")

# Function to enter the nickname and click "Next Step"
def enter_nickname_and_next():
    random_nickname = generate_random_nickname()
    nickname_field = wait_for_element({'className': "android.widget.EditText"}, retry_until_found=True)
    set_text_reliably(nickname_field, random_nickname, "nickname field")

    click_button_and_verify("Next Step")

# Function to enter referral code and click "Complete"
def enter_referral_and_complete():
    referral_code = "iemtejas"
    referral_field = wait_for_element({'className': "android.widget.EditText"}, retry_until_found=True)
    set_text_reliably(referral_field, referral_code, "referral field")

    # Click "Complete" and ensure transition to the next screen
    click_button_and_verify("Complete", expected_text=None)

    # Add a check to verify that the script has moved past the screen where the "Complete" button appears
    if device(text="Complete").exists:
        print("No need to click 'Complete' again. Proceeding to the next step.\n")
    else:
        print("Successfully completed the referral code step.\n")

# Ensure app is fully loaded before proceeding
def ensure_app_loaded():
    print("Waiting for app to load...")
    time.sleep(4)  # Add a delay of 4 seconds to allow the app to initialize
    try:
        home_screen_element = wait_for_element({'text': 'Email address'}, timeout=5, retry_until_found=True)
        if home_screen_element.exists:
            print("App is fully loaded and ready.\n")
    except Exception as e:
        print(f"Error ensuring app is loaded: {str(e)}")
        device.screenshot("error_app_not_loaded.png")
        close_app()
        raise

# Updated function to automate the referral process
def automate_referral():
    try:
        temp_email = get_temp_email()

        # Open the app and ensure it is ready
        device.app_start("io.doctorx.app")
        ensure_app_loaded()

        # Enter the temp email
        email_field = wait_for_element({'className': "android.widget.EditText"}, retry_until_found=True)
        set_text_reliably(email_field, temp_email, "email field")

        # Click "Log in / Sign up"
        click_button_and_verify("Log in / Sign up")

        # Wait for OTP input page to load
        otp_code = get_otp(temp_email)
        if otp_extracted:
            print(f"Retrieved OTP: {otp_code}\n")

            # Enter OTP into the app
            otp_fields = wait_for_element({'className': "android.widget.EditText"}, retry_until_found=True)
            set_text_reliably(otp_fields, otp_code, "OTP field")
            print("Entered OTP successfully.\n")

            # Check for any possible errors
            if not handle_possible_errors():
                print("An error occurred, restarting the process...\n")
                close_app()
                clear_app_data_ui()
                automate_referral()

            # Click "Next Step" button four times and "Not Now" once
            for _ in range(4):
                click_button_and_verify("Next Step", expected_text="Next Step")
            click_button_and_verify("Not now")

            # Enter random nickname and click "Next Step"
            enter_nickname_and_next()

            # Enter referral code and complete the process
            enter_referral_and_complete()
        else:
            print("OTP extraction failed or timeout occurred, skipping to the next iteration.\n")

    except Exception as e:
        device.screenshot("error_automate_referral.png")
        print(f"Error during automation: {str(e)}")
        close_app()
        raise

# Function to automate referral process with timeout
def automate_referral_with_timeout():
    global task_completed, otp_extracted
    task_completed = False
    otp_extracted = False
    try:
        automate_referral()
        task_completed = True
    except Exception as e:
        print(f"Error during automation: {str(e)}")
        close_app()

# Function to run the automation process with a timeout
def run_automation_with_timeout():
    global task_completed, otp_extracted
    task_thread = threading.Thread(target=automate_referral_with_timeout)
    task_thread.start()
    task_thread.join(timeout=50)

    if task_thread.is_alive():
        print("Timeout reached. Moving to the next iteration.")
        otp_extracted = False
        close_app()
        task_thread.join(timeout=1)
        if task_thread.is_alive():
            print("Task thread did not terminate. Force stopping thread.\n")

    if not task_completed:
        print("Task did not complete within the time limit.\n")

# Loop to repeat the process, clearing data and restarting after each run
def run_in_loop(iterations=999):
    print(f"Running the loop for {iterations} iterations...")
    error_count = 0

    for i in range(iterations):
        try:
            print(f"Starting iteration {i+1}/{iterations}...\n")
            clear_app_data_ui()
            run_automation_with_timeout()
            error_count = 0

        except Exception as e:
            print(f"Error occurred in iteration {i+1}: {str(e)}\n")
            error_count += 1
            if error_count >= 3:
                print("Too many consecutive errors. Stopping script.")
                break

        finally:
            close_app()
            close_open_windows()
            print(f"Iteration {i+1} completed.\n")


# Run the loop for a specified number of iterations
run_in_loop(iterations=999)
