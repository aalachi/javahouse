from selenium import webdriver
from selenium.webdriver.common.by import By


class Driver :
    def __init__(self, name):
        self.name = name
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=self.options)

    def get_driver(self):
        return self.driver

    def close_driver(self):
        self.driver.quit()

    def navigate_to(self, url):
        self.driver.get(url)
        




# run program
if __name__ == "__main__":
    driver = Driver("Avito")
    driver.navigate_to("https://www.mubawab.ma/fr/ct/casablanca/immobilier-a-vendre")

    input("Press Enter to continue...")

    elements = driver.get_driver().find_elements(By.CLASS_NAME, "contentBox")


    print(f"Found {len(elements)} elements with class name 'contentBox'.")
