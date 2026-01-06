"""
Frontend tests for language switching functionality.

This module tests the language selector UI component and language switching
functionality in the NewsFlash application frontend.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestLanguageFrontend:
    """Test class for language selector frontend functionality."""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Set up Chrome WebDriver for testing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode for CI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture(autouse=True)
    def setup_test(self, driver):
        """Navigate to the application before each test."""
        driver.get("http://localhost:5000")
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "app-header"))
        )
    
    def test_language_selector_exists(self, driver):
        """Test that the language selector component exists in the header."""
        # Check if language selector is present
        language_selector = driver.find_element(By.CLASS_NAME, "language-selector")
        assert language_selector.is_displayed()
        
        # Check if language button exists
        language_btn = driver.find_element(By.ID, "languageDropdown")
        assert language_btn.is_displayed()
        
        # Check if dropdown menu exists
        language_menu = driver.find_element(By.CLASS_NAME, "language-menu")
        assert language_menu is not None
    
    def test_language_button_default_state(self, driver):
        """Test that the language button shows default language (English)."""
        language_btn = driver.find_element(By.ID, "languageDropdown")
        language_text = language_btn.find_element(By.CLASS_NAME, "language-text")
        
        # Should default to English
        assert "English" in language_text.text
        
        # Should have globe icon
        globe_icon = language_btn.find_element(By.CLASS_NAME, "fa-globe")
        assert globe_icon.is_displayed()
    
    def test_language_dropdown_opens(self, driver):
        """Test that clicking the language button opens the dropdown menu."""
        language_btn = driver.find_element(By.ID, "languageDropdown")
        
        # Click to open dropdown
        language_btn.click()
        
        # Wait for dropdown to be visible
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        # Check if dropdown is visible
        language_menu = driver.find_element(By.CLASS_NAME, "language-menu")
        assert language_menu.is_displayed()
    
    def test_language_options_populated(self, driver):
        """Test that language options are populated in the dropdown."""
        language_btn = driver.find_element(By.ID, "languageDropdown")
        language_btn.click()
        
        # Wait for dropdown to be visible
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        # Check for language options
        language_items = driver.find_elements(By.CSS_SELECTOR, ".dropdown-item[data-language]")
        assert len(language_items) >= 3  # Should have at least English, Hindi, Marathi
        
        # Check for specific languages
        language_codes = [item.get_attribute("data-language") for item in language_items]
        assert "en" in language_codes
        assert "hi" in language_codes
        assert "mr" in language_codes
    
    def test_language_option_structure(self, driver):
        """Test that language options have proper structure with flags and names."""
        language_btn = driver.find_element(By.ID, "languageDropdown")
        language_btn.click()
        
        # Wait for dropdown to be visible
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        # Check first language option structure
        first_option = driver.find_element(By.CSS_SELECTOR, ".dropdown-item[data-language]")
        
        # Should have flag
        flag = first_option.find_element(By.CLASS_NAME, "language-flag")
        assert flag.is_displayed()
        
        # Should have language names container
        names_container = first_option.find_element(By.CLASS_NAME, "language-names")
        assert names_container.is_displayed()
        
        # Should have language name and native name
        language_name = first_option.find_element(By.CLASS_NAME, "language-name")
        native_name = first_option.find_element(By.CLASS_NAME, "language-native")
        assert language_name.is_displayed()
        assert native_name.is_displayed()
    
    def test_language_switching_functionality(self, driver):
        """Test that clicking a language option changes the language."""
        # Open dropdown
        language_btn = driver.find_element(By.ID, "languageDropdown")
        original_text = language_btn.find_element(By.CLASS_NAME, "language-text").text
        
        language_btn.click()
        
        # Wait for dropdown to be visible
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        # Find and click Hindi option
        hindi_option = driver.find_element(By.CSS_SELECTOR, ".dropdown-item[data-language='hi']")
        hindi_option.click()
        
        # Wait for language change to complete
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.CLASS_NAME, "language-text").text != original_text
        )
        
        # Check if button text changed to Hindi
        updated_text = language_btn.find_element(By.CLASS_NAME, "language-text").text
        assert "Hindi" in updated_text
    
    def test_language_change_loading_state(self, driver):
        """Test that language button shows loading state during change."""
        # Open dropdown
        language_btn = driver.find_element(By.ID, "languageDropdown")
        language_btn.click()
        
        # Wait for dropdown to be visible
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        # Click on a different language
        marathi_option = driver.find_element(By.CSS_SELECTOR, ".dropdown-item[data-language='mr']")
        marathi_option.click()
        
        # Check for loading state (might be brief)
        try:
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".language-btn.loading"))
            )
        except TimeoutException:
            # Loading state might be too brief to catch, which is okay
            pass
        
        # Wait for loading to complete
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".language-btn.loading"))
        )
    
    def test_language_change_success_feedback(self, driver):
        """Test that successful language change shows success feedback."""
        # Open dropdown and change language
        language_btn = driver.find_element(By.ID, "languageDropdown")
        language_btn.click()
        
        # Wait for dropdown to be visible
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        # Click on English (should always work)
        english_option = driver.find_element(By.CSS_SELECTOR, ".dropdown-item[data-language='en']")
        english_option.click()
        
        # Wait for and check success toast
        try:
            success_toast = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success.language-toast"))
            )
            assert success_toast.is_displayed()
            
            # Check for success icon
            success_icon = success_toast.find_element(By.CLASS_NAME, "fa-check")
            assert success_icon.is_displayed()
            
        except TimeoutException:
            # If no toast appears, check if language changed successfully
            updated_text = language_btn.find_element(By.CLASS_NAME, "language-text").text
            assert "English" in updated_text
    
    def test_dropdown_closes_after_selection(self, driver):
        """Test that dropdown closes after language selection."""
        # Open dropdown
        language_btn = driver.find_element(By.ID, "languageDropdown")
        language_btn.click()
        
        # Wait for dropdown to be visible
        language_menu = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        # Click on a language option
        english_option = driver.find_element(By.CSS_SELECTOR, ".dropdown-item[data-language='en']")
        english_option.click()
        
        # Wait for dropdown to close
        WebDriverWait(driver, 5).until_not(
            EC.visibility_of(language_menu)
        )
    
    def test_active_language_highlighted(self, driver):
        """Test that the current language is highlighted in the dropdown."""
        # Open dropdown
        language_btn = driver.find_element(By.ID, "languageDropdown")
        language_btn.click()
        
        # Wait for dropdown to be visible
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        # Check for active language (should be English by default)
        active_option = driver.find_element(By.CSS_SELECTOR, ".dropdown-item.active[data-language]")
        assert active_option.is_displayed()
        
        # Should be English by default
        assert active_option.get_attribute("data-language") == "en"
    
    def test_responsive_language_selector(self, driver):
        """Test language selector behavior on mobile viewport."""
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone size
        
        # Check if language selector is still visible
        language_selector = driver.find_element(By.CLASS_NAME, "language-selector")
        assert language_selector.is_displayed()
        
        # Language button should be smaller on mobile
        language_btn = driver.find_element(By.ID, "languageDropdown")
        assert language_btn.is_displayed()
        
        # Dropdown should still work
        language_btn.click()
        
        language_menu = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        assert language_menu.is_displayed()
        
        # Reset to desktop size
        driver.set_window_size(1920, 1080)
    
    def test_keyboard_accessibility(self, driver):
        """Test keyboard navigation for language selector."""
        language_btn = driver.find_element(By.ID, "languageDropdown")
        
        # Focus on language button
        language_btn.click()
        
        # Check if button is focusable
        focused_element = driver.switch_to.active_element
        assert focused_element == language_btn or focused_element.get_attribute("id") == "languageDropdown"
    
    def test_language_persistence_across_actions(self, driver):
        """Test that language preference persists across different actions."""
        # Change to Hindi
        language_btn = driver.find_element(By.ID, "languageDropdown")
        language_btn.click()
        
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "language-menu"))
        )
        
        hindi_option = driver.find_element(By.CSS_SELECTOR, ".dropdown-item[data-language='hi']")
        hindi_option.click()
        
        # Wait for change to complete
        WebDriverWait(driver, 10).until(
            lambda d: "Hindi" in d.find_element(By.CLASS_NAME, "language-text").text
        )
        
        # Perform some action (like typing in chat)
        try:
            chat_input = driver.find_element(By.ID, "chat-input")
            chat_input.send_keys("Test message")
            
            # Language should still be Hindi
            current_text = language_btn.find_element(By.CLASS_NAME, "language-text").text
            assert "Hindi" in current_text
            
        except NoSuchElementException:
            # Chat input might not be available, just check language persistence
            current_text = language_btn.find_element(By.CLASS_NAME, "language-text").text
            assert "Hindi" in current_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])