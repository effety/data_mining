import signal
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os

interrupted = False

def signal_handler(sig, frame):
    global interrupted
    print("You pressed Ctrl+C! Stopping gracefully...")
    interrupted = True

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

def setup_driver():
    webdriver_path = 'D:/data_mining/chromedriver.exe'
    service = webdriver.chrome.service.Service(executable_path=webdriver_path)
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_data(driver):
    csv_filename = os.path.expanduser("~/Desktop/profiles_data.csv")
    if os.path.exists(csv_filename):
        existing_df = pd.read_csv(csv_filename)
    else:
        existing_df = pd.DataFrame(columns=['Doctor Name', 'Expertise', 'Specialties'])

    try:
        driver.get("https://www.onedoc.ch/en/general-practitioner-gp")

        while not interrupted:
            profile_buttons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//a[@class="Button Button--small"]'))
            )

            main_window = driver.current_window_handle

            for index, button in enumerate(profile_buttons):
                if interrupted:
                    break
                try:
                    driver.execute_script("window.open(arguments[0]);", button.get_attribute('href'))
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(3)

                    doctor_name_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/header/div/div[2]/h1'))
                    )
                    doctor_name = doctor_name_element.text.strip()
                    
                    doctor_expert_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/header/div/div[2]/h2'))
                    )
                    doctor_expertise = doctor_expert_element.text.strip()

                    specialties_elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[5]/main/div/div[1]/div[1]/div[2]/div[1]/div[2]/div/div'))
                    )
                    
                    specialties = ', '.join([specialty.text.strip() for specialty in specialties_elements])
                    
                    profile_data = {
                        'Doctor Name': doctor_name,
                        'Expertise': doctor_expertise,
                        'Specialties': specialties,
                    }

                    # Convert profile_data to DataFrame and concatenate with existing_df
                    new_data_df = pd.DataFrame([profile_data])
                    existing_df = pd.concat([existing_df, new_data_df], ignore_index=True)

                    # Save the DataFrame to CSV
                    existing_df.drop_duplicates().to_csv(csv_filename, index=False)
                    print(f"Saved profile {index + 1} data to {csv_filename}")

                    driver.close()
                    driver.switch_to.window(main_window)
                    time.sleep(2)
                except Exception as e:
                    print(f"An error occurred while scraping profile {index + 1}: {e}")
                    driver.close()
                    driver.switch_to.window(main_window)
                    time.sleep(2)

            if interrupted:
                break

            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/main/div/div[3]/div[1]/div[21]/div[2]/a'))
                )
                next_button.click()
                time.sleep(3)
            except:
                print("No more pages left.")
                break

    except Exception as e:
        print(f"An error occurred during scraping: {e}")

    finally:
        # Ensure the latest data is saved
        existing_df.drop_duplicates().to_csv(csv_filename, index=False)
        driver.quit()

if __name__ == "__main__":
    try:
        driver = setup_driver()
        scrape_data(driver)

    except Exception as e:
        print(f"An error occurred: {e}")
