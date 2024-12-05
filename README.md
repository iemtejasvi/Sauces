

# **Automation Script for nearly all Ice network projects (DoctorX, Sauces, Crypto Mayors etc. - README**

## **Overview**

This guide provides step-by-step instructions on how to set up and run the Sauces Automation Script. The script automates the referral process for the Sauces app, but please be aware that it may occasionally fail due to mobile device limitations. You need to monitor its execution, as increasing timeouts might help with certain issues.

---

## **Prerequisites**

### **1. Install Python**

- **Download Python**: Go to [python.org/downloads](https://www.python.org/downloads/) and download the latest version of Python.
- **Install Python**:
  - **Windows**: Run the downloaded executable, ensure "Add Python to PATH" is checked, and follow the installation prompts.
  - **macOS** and **Linux**: Follow the instructions on the Python website to install Python.

### **2. Install Required Python Packages**

Open Command Prompt (CMD) or Terminal and run the following command to install the required packages:

```bash
pip install uiautomator2 requests
```

### **3. Connect Your Android Device**

- **Enable Developer Options**: 
  - Go to `Settings` > `About phone`.
  - Tap `Build number` seven times to enable Developer Options.
- **Enable USB Debugging**: 
  - Go to `Settings` > `Developer Options`.
  - Enable `USB Debugging`.
- **Connect the Device to Your PC**:
  - Use a USB cable to connect your Android device to your computer.
  - Ensure that the device is detected, and allow USB debugging if prompted on the device.

### **4. Place Sauces App on Home Screen**

Ensure the Sauces app is placed on the home screen of your Android device. This is necessary for the automation to work correctly.

---

## **Running the Script**

### **1. Clone the Repository**

In Command Prompt or Terminal, navigate to the directory where you want to clone the repository, and run:

```bash
git clone https://github.com/iemtejasvi/Sauces.git
```

### **2. Change Directory**

Navigate to the cloned repository's directory:

```bash
cd Sauces
```

### **3. Update the Referral Code**

Open the script file (`sauces.py`) and update the referral code from `"iemtejas"` to your own referral code. Save the file after making the changes.

### **4. Execute the Script**

Run the script using Python:

```bash
python sauces.py
```

### **5. Monitor the Script**

- The script will start executing and automating the referral process.
- **Possible Issues**:
  - **Script Failures**: The script may fail due to various mobile-specific issues like UI elements not loading in time, device lag, or network issues. If the script fails, monitor the logs and adjust timeouts if necessary.
  - **Timeout Issues**: If the script frequently fails due to timeouts, consider increasing the timeout values in the script.

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## **3 very Important Steps**

1. **Update the referral code.** The current referral code is "iemtejas." Locate it in the code and replace it with your own referral code.  
   
2. **Modify the app name.** Update the script with the name of the app you are working on. For example, if you want to run the script on DoctorX, find the last line of the code, such as `automate_registration("Crypto Mayors")`, and replace `"Crypto Mayors"` with the exact name of the app you are working on. Ensure the name matches the app name exactly.  

3. **Place the app on the home screen.** This is the most important step, so make sure the app is positioned correctly on the home screen.  
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## **Limitations**

- **Device Dependent**: The script's performance may vary based on the device's speed, responsiveness, and internet connection.
- **Manual Monitoring**: It is recommended to manually monitor the script to handle any unexpected errors.
- **Potential for Failure**: The script can sometimes fail due to mobile device limitations or app updates, which might require adjustments to the script.

---

## **Submitting Issues or Improvements**

If you encounter any errors or have suggestions for improvement, feel free to submit them to the repository. You can create an issue or submit a pull request with your improvements.

---

This guide should help you set up and run the script with minimal issues. Make sure to follow each step carefully to ensure proper execution.
