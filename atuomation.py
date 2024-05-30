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
        existing_df = pd.DataFrame(columns=['Image URL', 'Doctor Name', 'Speciality', 'Specialties', 'Expertise', 'Access', 'Opening Hours', 'Healthcare Professional', 'Speaking Languages', 'Phone Number', 'Page URL', 'Page Number'])

    try:
        driver.get("https://www.onedoc.ch/en/general-practitioner-gp")
        current_page = 1

        while not interrupted:
            print(f"Scraping Page: {current_page}")
            current_page_url = driver.current_url
            print(f"Current Page URL: {current_page_url}")

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

                    # Image URL
                    image_url_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/header/div/div[1]/img'))
                    )
                    image_url = image_url_element.get_attribute('src')
                    
                    doctor_name_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/header/div/div[2]/h1'))
                    )
                    doctor_name = doctor_name_element.text.strip()
                    
                    doctor_speciality_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/header/div/div[2]/h2'))
                    )
                    doctor_speciality = doctor_speciality_element.text.strip()
                    
                    # Specialties
                    try:
                        specialties_elements = WebDriverWait(driver, 5).until(
                            EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[5]/main/div/div[1]/div[1]/div[2]/div[3]/div[2]'))
                        )
                    except:
                        try:
                            specialties_elements = WebDriverWait(driver, 5).until(
                                EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[5]/main/div/div[1]/div[1]/div[2]/div[1]/div[2]'))
                            )
                        except:
                            specialties_elements = WebDriverWait(driver, 5).until(
                                EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[5]/main/div/div[1]/div[1]/div[2]/div/div[2]'))
                            )

                    specialties = ', '.join([specialty.text.strip().replace('\n', ', ') for specialty in specialties_elements])

                    # Expertise
                    try:
                        expertise_elements = WebDriverWait(driver, 5).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, 'od-profile-expertise-expandable'))
                        )
                        expertise = ', '.join([element.text.strip().replace('\n', ', ') for element in expertise_elements])
                    except:
                        expertise = ""

                    # Access
                    try:
                        access_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/div[1]/div[1]/div[6]/div/div[1]/div[2]'))
                        )
                        access = access_element.text.strip().replace('\n', ', ')
                    except:
                        try:
                            access_element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/div[1]/div[1]/div[4]/div/div[1]/div[2]'))
                            )
                            access = access_element.text.strip().replace('\n', ', ')
                        except:
                            access = ""

                    # Opening Hours
                    opening_hours = ""
                    try:
                        opening_hours_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/div[1]/div[1]/div[6]/div/div[1]/div[4]'))
                        )
                        opening_hours = opening_hours_element.text.strip()
                    except:
                        try:
                            opening_hours_element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/main/div/div[1]/div[1]/div[4]/div/div[1]/div[4]'))
                            )
                            opening_hours = opening_hours_element.text.strip()
                        except:
                            pass
                    
                    if opening_hours.startswith("Opening hours"):
                        opening_hours = opening_hours.replace("Opening hours", "").strip()

                    # Healthcare Professional
                    healthcare_professional = ""
                    try:
                        healthcare_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@class="od-profile-card-section-body cw-rich-text"]'))
                        )
                        healthcare_professional = healthcare_element.text.strip()
                    except:
                        pass

                    # Speaking Languages
                    speaking_languages = ""
                    try:
                        languages_section = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@class="od-profile-card-section-description-item"]'))
                        )
                        languages_header = languages_section.find_element(By.XPATH, './/h4[contains(text(), "Spoken languages")]')
                        if languages_header:
                            languages_text = languages_header.find_element(By.XPATH, './following-sibling::p').text.strip()
                            speaking_languages = languages_text.replace(" and ", ", ")
                    except:
                        pass

                    # Phone Number
                    phone_number = ""
                    try:
                        # Check if any of the phone number section XPaths exist
                        phone_section_xpath = [
                            '/html/body/div[5]/main/div/div[1]/div[1]/div[7]/div/div[2]/div[4]',
                            '/html/body/div[5]/main/div/div[1]/div[1]/div[9]/div/div[2]/div[4]'
                        ]
                        phone_number_xpath = [
                            '/html/body/div[5]/main/div/div[1]/div[1]/div[7]/div/div[2]/div[4]/div[2]/p/a',
                            '/html/body/div[5]/main/div/div[1]/div[1]/div[7]/div/div[2]/div[3]/div[2]/p/a',
                            '/html/body/div[5]/main/div/div[1]/div[1]/div[9]/div/div[2]/div[4]/div[2]/p/a'
                        ]

                        phone_number_element = None
                        for section_xpath, number_xpath in zip(phone_section_xpath, phone_number_xpath):
                            try:
                                phone_section_element = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, section_xpath))
                                )
                                if phone_section_element:
                                    phone_section_element.click()
                                    time.sleep(2)  # Allow time for the section to expand
                                    phone_number_element = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.XPATH, number_xpath))
                                    )
                                    phone_number = phone_number_element.text.strip()
                                    break  # Exit loop if phone number is found
                            except:
                                continue
                        
                    except Exception as e:
                        print(f"Error while retrieving phone number: {e}")

                    profile_data = {
                        'Image URL': image_url,
                        'Doctor Name': doctor_name,
                        'Speciality': doctor_speciality,
                        'Specialties': specialties,
                        'Expertise': expertise,
                        'Access': access,
                        'Opening Hours': opening_hours,
                        'Healthcare Professional': healthcare_professional,
                        'Speaking Languages': speaking_languages,
                        'Phone Number': phone_number,
                        'Page URL': current_page_url,
                        'Page Number': current_page
                    }

                    new_data_df = pd.DataFrame([profile_data])
                    existing_df = pd.concat([existing_df, new_data_df], ignore_index=True)

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
                current_page += 1
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
