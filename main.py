# pip install playwright playwright-stealth colorama pure-python-adb
# python -m playwright install

import subprocess
import sys
from ppadb.client import Client as AdbClient
import time
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth  # Import Stealth
import random
from colorama import init, Fore, Style
import datetime
import json

# Initialize colorama for colored logs
init(autoreset=True)

# Helper function to log messages with timestamps and color
def log(message, color=Fore.GREEN):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color}[{timestamp}] {message}{Style.RESET_ALL}")

class AndroidDeviceController:
    def __init__(self, host="127.0.0.1", port=5037, device_index=0):
        """
        Initializes the ADB client and connects to the first available Android device.
        """
        self.client = AdbClient(host=host, port=port)
        self.device = self.get_device(device_index)
        
    def get_device(self, device_index=0):
        """
        Retrieves the first connected device.
        """
        devices = self.client.devices()
        if len(devices) < device_index + 1:
            raise Exception(f"Device ({device_index}) not available!")
        return devices[device_index]

    def send_image_to_gallery(self, local_path, remote_path):
        """
        Sends an image to the Android device's internal storage and ensures it is visible in the Gallery.
        """
        self.push_image(local_path, remote_path)
        self.trigger_media_scanner(remote_path)

    def push_image(self, local_path, remote_path):
        """
        Pushes an image from the local machine to the Android device's internal storage.
        """
        try:
            subprocess.run(["adb", "-s", self.device.serial, "push", local_path, remote_path], check=True)
            log(f"Image {local_path} sent to {remote_path}", Fore.CYAN)
        except subprocess.CalledProcessError as e:
            log(f"Error pushing image: {e}", Fore.RED)
            raise

    def trigger_media_scanner(self, remote_path):
        """
        Triggers the media scanner to make the newly pushed image visible in the Gallery.
        """
        try:
            self.device.shell(f"am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remote_path}")
            log(f"Media scanner triggered for {remote_path}", Fore.CYAN)
        except Exception as e:
            log(f"Error triggering media scanner: {e}", Fore.RED)
            raise

    def tap(self, x, y):
        """
        Simulates a tap at the given screen coordinates (x, y).
        """
        try:
            self.device.shell(f"input tap {x} {y}")
            log(f"Tapped at ({x}, {y})", Fore.GREEN)
        except Exception as e:
            log(f"Error tapping at ({x}, {y}): {e}", Fore.RED)
            raise

    def remove_orphans(self):
        try:
            self.device.shell("rm /sdcard/Pictures/qris-*")
            log(f"Removing orphans", Fore.GREEN)
        except Exception as e:
            log(f"Error removing orphans {e}", Fore.RED)
            raise

    def type_text(self, text):
        """
        Simulates typing the given text on the device, one character at a time.
        """
        try:
            # Loop through each character in the text
            for char in text:
                # Ensure that spaces are handled correctly by using "%s"
                if char == " ":
                    char = "%s"
                
                # Send the character to the device
                self.device.shell(f"input text {char}")
                log(f"Typed character: {char}", Fore.GREEN)
                
                # Optional: Add a small delay between typing characters (e.g., 0.1 seconds)
                time.sleep(0.1)
        except Exception as e:
            log(f"Error typing text: {text}", Fore.RED)
            raise

def sleep_with_delay(seconds):
    """
    Helper function to add delay with time.sleep, maintaining consistency.
    """
    log(f"Waiting for {seconds} seconds...", Fore.YELLOW)
    time.sleep(seconds)

async def main():
    device_index = 0
    remote_config = None

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        # Open and load the JSON file
        with open(file_path, 'r') as file:
            remote_config = json.load(file)
    else:
        raise Exception("Config file must be inserted!")

    if len(sys.argv) > 2:
        device_index = int(sys.argv[2])

    ac = AndroidDeviceController(
        device_index=device_index
    )

    print("Starting profile", remote_config['name'])

    # Counter for the number of iterations
    iteration_counter = 1
    ac.remove_orphans()
    
    async with Stealth().use_async(async_playwright()) as p:
        # Launch the browser in stealth mode
        browser = await p.chromium.launch(headless=True)  # Set headless=False to see the browser
        page = await browser.new_page()

        # Navigate to the URL
        await page.goto("https://voteqrisbali.com/event/vote-donasi-buleleng-festival")

        while True:
            # Display the iteration count
            log(f"Starting iteration {iteration_counter}", Fore.CYAN)

            if iteration_counter % 4 == 0:
                ac.remove_orphans()
                log(f"Waiting for safe request", Fore.YELLOW)
                time.sleep(3)

            # Wait for the page to load completely
            await page.wait_for_load_state('load')
            log("Page loaded successfully!", Fore.GREEN)

            # Step 1: Click the parent element (button) of the "TV" span
            await page.click('xpath=//span[text()="TV"]/ancestor::button', timeout=5000)
            # sleep_with_delay(1)  # Wait for the action to complete

            # Step 2: Locate and click the next sibling button
            h3_locator = page.locator('h3.text-xl.font-bold.text-gray-900.mb-2.truncate >> text="I Gede Agus Kusuma Ariawan"')
            parent_locator = h3_locator.locator('..')
            grandparent_locator = parent_locator.locator('..')
            next_sibling_button_locator = grandparent_locator.locator('xpath=following-sibling::button')
            await next_sibling_button_locator.click()
            log("Next sibling button clicked successfully.", Fore.GREEN)

            sleep_with_delay(0.8)  # Wait after clicking the next button

            # Step 3: Submit the form and take a screenshot
            submit_button_locator = page.locator('button[type="submit"]')  # Adjust the selector as needed
            await submit_button_locator.click()  # Click the Submit button
            log("Submit button clicked successfully.", Fore.GREEN)
            sleep_with_delay(2.5)  # Wait for submit action to complete

            # Step 4: Take a screenshot of the <div> element and send it to gallery
            div_locator = page.locator('div.absolute.inset-0.flex.items-center.justify-center.p-6')
            await div_locator.screenshot(path="qris.jpg")  # Take a screenshot of the specific element
            log("Screenshot taken.", Fore.CYAN)
            
            ac.send_image_to_gallery('./qris.jpg', '/sdcard/Pictures/qris-' + str(random.randint(111111, 999999)) + '.jpg')

            # Simulate taps on various coordinates
            ac.tap(*remote_config['press_qris_button'])  # CLICK QRIS BUTTON
            sleep_with_delay(remote_config['delay_adjustment'] + remote_config['press_qris_button_delay'])

            ac.tap(*remote_config['press_input_image'])  # CLICK INPUT IMAGE
            sleep_with_delay(remote_config['delay_adjustment'] + remote_config['press_input_image_delay'])

            ac.tap(*remote_config['choose_image'])  # CLICK ON IMAGE FILE
            sleep_with_delay(remote_config['delay_adjustment'] + remote_config['choose_image_delay'])

            ac.tap(*remote_config['press_next_button'])  # CLICK ON "LANJUT BUTTON"
            sleep_with_delay(remote_config['delay_adjustment'] + remote_config['press_next_button_delay'])

            for pin_coords in remote_config['pin_taps']:
                ac.tap(*pin_coords)

            sleep_with_delay(remote_config['delay_adjustment'] + remote_config['pin_input_delay'])

            ac.tap(*remote_config['press_close_button'])  # CLOSE INVOICE

            # Step 5: Refresh the page
            await page.reload()
            log("Page refreshed successfully.", Fore.YELLOW)

            log("Restarting the procedure...", Fore.YELLOW)

            # Increment the iteration counter
            iteration_counter += 1

# Run the script asynchronously
asyncio.run(main())
