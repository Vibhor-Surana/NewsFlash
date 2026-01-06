/**
 * Frontend JavaScript tests for language switching functionality
 * These tests can be run in the browser console or with a test runner
 */

class LanguageTests {
    constructor() {
        this.testResults = [];
        this.newsApp = window.newsApp;
    }

    // Test helper methods
    assert(condition, message) {
        if (condition) {
            this.testResults.push({ status: 'PASS', message });
            console.log(`✅ PASS: ${message}`);
        } else {
            this.testResults.push({ status: 'FAIL', message });
            console.error(`❌ FAIL: ${message}`);
        }
    }

    assertEqual(actual, expected, message) {
        this.assert(actual === expected, `${message} (expected: ${expected}, actual: ${actual})`);
    }

    assertNotEqual(actual, expected, message) {
        this.assert(actual !== expected, `${message} (should not equal: ${expected})`);
    }

    assertTrue(condition, message) {
        this.assert(condition === true, message);
    }

    assertFalse(condition, message) {
        this.assert(condition === false, message);
    }

    // Test methods
    testLanguageSelectorInitialization() {
        console.log('\n🧪 Testing Language Selector Initialization...');
        
        // Test that language selector elements exist
        const languageSelector = document.querySelector('.language-selector');
        this.assertTrue(languageSelector !== null, 'Language selector element exists');
        
        const languageBtn = document.getElementById('languageDropdown');
        this.assertTrue(languageBtn !== null, 'Language button exists');
        
        const languageMenu = document.querySelector('.language-menu');
        this.assertTrue(languageMenu !== null, 'Language menu exists');
        
        // Test that NewsApp has language properties
        this.assertTrue(this.newsApp.hasOwnProperty('currentLanguage'), 'NewsApp has currentLanguage property');
        this.assertTrue(this.newsApp.hasOwnProperty('supportedLanguages'), 'NewsApp has supportedLanguages property');
    }

    testDefaultLanguageState() {
        console.log('\n🧪 Testing Default Language State...');
        
        // Test default language is English
        this.assertEqual(this.newsApp.currentLanguage, 'en', 'Default language is English');
        
        // Test button shows English
        const languageText = document.querySelector('.language-text');
        this.assertTrue(languageText.textContent.includes('English'), 'Language button shows English');
    }

    testSupportedLanguagesStructure() {
        console.log('\n🧪 Testing Supported Languages Structure...');
        
        const languages = this.newsApp.supportedLanguages;
        
        // Test that supported languages object exists and has expected languages
        this.assertTrue(typeof languages === 'object', 'Supported languages is an object');
        this.assertTrue(languages.hasOwnProperty('en'), 'English is supported');
        this.assertTrue(languages.hasOwnProperty('hi'), 'Hindi is supported');
        this.assertTrue(languages.hasOwnProperty('mr'), 'Marathi is supported');
        
        // Test language object structure
        Object.entries(languages).forEach(([code, lang]) => {
            this.assertTrue(lang.hasOwnProperty('name'), `Language ${code} has name property`);
            this.assertTrue(lang.hasOwnProperty('native'), `Language ${code} has native property`);
            this.assertTrue(typeof lang.name === 'string', `Language ${code} name is string`);
            this.assertTrue(typeof lang.native === 'string', `Language ${code} native is string`);
        });
    }

    testLanguageFlagMapping() {
        console.log('\n🧪 Testing Language Flag Mapping...');
        
        // Test flag emoji mapping
        const enFlag = this.newsApp.getLanguageFlag('en');
        const hiFlag = this.newsApp.getLanguageFlag('hi');
        const mrFlag = this.newsApp.getLanguageFlag('mr');
        const unknownFlag = this.newsApp.getLanguageFlag('unknown');
        
        this.assertEqual(enFlag, '🇺🇸', 'English flag is US flag');
        this.assertEqual(hiFlag, '🇮🇳', 'Hindi flag is Indian flag');
        this.assertEqual(mrFlag, '🇮🇳', 'Marathi flag is Indian flag');
        this.assertEqual(unknownFlag, '🌐', 'Unknown language shows globe');
    }

    testLanguageButtonTextUpdate() {
        console.log('\n🧪 Testing Language Button Text Update...');
        
        const originalLanguage = this.newsApp.currentLanguage;
        
        // Simulate language change
        this.newsApp.currentLanguage = 'hi';
        this.newsApp.updateLanguageButtonText();
        
        const languageText = document.querySelector('.language-text');
        this.assertTrue(languageText.textContent.includes('Hindi'), 'Button text updates to Hindi');
        
        // Reset to original
        this.newsApp.currentLanguage = originalLanguage;
        this.newsApp.updateLanguageButtonText();
    }

    testDropdownPopulation() {
        console.log('\n🧪 Testing Dropdown Population...');
        
        // Trigger dropdown population
        this.newsApp.populateLanguageDropdown();
        
        // Check that language items were created
        const languageItems = document.querySelectorAll('.language-item');
        const expectedCount = Object.keys(this.newsApp.supportedLanguages).length;
        
        this.assertEqual(languageItems.length, expectedCount, `Dropdown has ${expectedCount} language items`);
        
        // Check that each language has proper structure
        languageItems.forEach((item, index) => {
            const button = item.querySelector('.dropdown-item[data-language]');
            const flag = item.querySelector('.language-flag');
            const names = item.querySelector('.language-names');
            const name = item.querySelector('.language-name');
            const native = item.querySelector('.language-native');
            
            this.assertTrue(button !== null, `Language item ${index} has button`);
            this.assertTrue(flag !== null, `Language item ${index} has flag`);
            this.assertTrue(names !== null, `Language item ${index} has names container`);
            this.assertTrue(name !== null, `Language item ${index} has name`);
            this.assertTrue(native !== null, `Language item ${index} has native name`);
        });
    }

    testActiveLanguageHighlighting() {
        console.log('\n🧪 Testing Active Language Highlighting...');
        
        // Set current language and update dropdown
        this.newsApp.currentLanguage = 'en';
        this.newsApp.updateLanguageDropdownSelection();
        
        // Check that English is marked as active
        const activeItem = document.querySelector('.dropdown-item.active[data-language]');
        this.assertTrue(activeItem !== null, 'An active language item exists');
        this.assertEqual(activeItem.dataset.language, 'en', 'English is marked as active');
        
        // Change to Hindi and test
        this.newsApp.currentLanguage = 'hi';
        this.newsApp.updateLanguageDropdownSelection();
        
        const newActiveItem = document.querySelector('.dropdown-item.active[data-language]');
        this.assertEqual(newActiveItem.dataset.language, 'hi', 'Hindi is now marked as active');
        
        // Reset to English
        this.newsApp.currentLanguage = 'en';
        this.newsApp.updateLanguageDropdownSelection();
    }

    testTTSLanguageIntegration() {
        console.log('\n🧪 Testing TTS Language Integration...');
        
        // Mock fetch to test TTS request includes language
        const originalFetch = window.fetch;
        let lastRequestBody = null;
        
        window.fetch = async (url, options) => {
            if (url === '/tts') {
                lastRequestBody = JSON.parse(options.body);
                return {
                    ok: true,
                    json: async () => ({ success: true, audio_url: 'test.mp3' })
                };
            }
            return originalFetch(url, options);
        };
        
        // Set language to Hindi
        this.newsApp.currentLanguage = 'hi';
        
        // Create a mock button for TTS
        const mockButton = document.createElement('button');
        mockButton.innerHTML = '<i class="fas fa-volume-up me-1"></i>Listen';
        document.body.appendChild(mockButton);
        
        // Test TTS call includes language
        this.newsApp.playTTS('Test text', mockButton).catch(() => {
            // Ignore audio playback errors in test
        });
        
        // Check that request included Hindi language
        setTimeout(() => {
            this.assertTrue(lastRequestBody !== null, 'TTS request was made');
            if (lastRequestBody) {
                this.assertEqual(lastRequestBody.language, 'hi', 'TTS request includes Hindi language');
            }
            
            // Cleanup
            document.body.removeChild(mockButton);
            window.fetch = originalFetch;
        }, 100);
    }

    testSearchLanguageIntegration() {
        console.log('\n🧪 Testing Search Language Integration...');
        
        // Mock fetch to test search request includes language
        const originalFetch = window.fetch;
        let lastRequestBody = null;
        
        window.fetch = async (url, options) => {
            if (url === '/search_news') {
                lastRequestBody = JSON.parse(options.body);
                return {
                    ok: true,
                    json: async () => ({ success: true, results: {} })
                };
            }
            return originalFetch(url, options);
        };
        
        // Set language to Marathi
        this.newsApp.currentLanguage = 'mr';
        
        // Set some topics to enable search
        this.newsApp.currentTopics = ['test topic'];
        
        // Trigger search
        this.newsApp.searchNews().catch(() => {
            // Ignore search errors in test
        });
        
        // Check that request included Marathi language
        setTimeout(() => {
            this.assertTrue(lastRequestBody !== null, 'Search request was made');
            if (lastRequestBody) {
                this.assertEqual(lastRequestBody.language, 'mr', 'Search request includes Marathi language');
            }
            
            // Cleanup
            window.fetch = originalFetch;
        }, 100);
    }

    // Run all tests
    async runAllTests() {
        console.log('🚀 Starting Language Frontend Tests...\n');
        
        this.testResults = [];
        
        try {
            this.testLanguageSelectorInitialization();
            this.testDefaultLanguageState();
            this.testSupportedLanguagesStructure();
            this.testLanguageFlagMapping();
            this.testLanguageButtonTextUpdate();
            this.testDropdownPopulation();
            this.testActiveLanguageHighlighting();
            this.testTTSLanguageIntegration();
            this.testSearchLanguageIntegration();
            
            // Wait a bit for async tests
            await new Promise(resolve => setTimeout(resolve, 200));
            
        } catch (error) {
            console.error('Test execution error:', error);
            this.testResults.push({ status: 'ERROR', message: error.message });
        }
        
        this.printResults();
    }

    printResults() {
        console.log('\n📊 Test Results Summary:');
        console.log('========================');
        
        const passed = this.testResults.filter(r => r.status === 'PASS').length;
        const failed = this.testResults.filter(r => r.status === 'FAIL').length;
        const errors = this.testResults.filter(r => r.status === 'ERROR').length;
        
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`💥 Errors: ${errors}`);
        console.log(`📈 Total: ${this.testResults.length}`);
        
        if (failed > 0 || errors > 0) {
            console.log('\n❌ Failed/Error Tests:');
            this.testResults
                .filter(r => r.status !== 'PASS')
                .forEach(r => console.log(`   ${r.status}: ${r.message}`));
        }
        
        const successRate = ((passed / this.testResults.length) * 100).toFixed(1);
        console.log(`\n🎯 Success Rate: ${successRate}%`);
        
        return {
            passed,
            failed,
            errors,
            total: this.testResults.length,
            successRate: parseFloat(successRate)
        };
    }
}

// Auto-run tests when loaded (if NewsApp is available)
if (typeof window !== 'undefined') {
    window.LanguageTests = LanguageTests;
    
    // Run tests after a short delay to ensure NewsApp is initialized
    setTimeout(() => {
        if (window.newsApp) {
            console.log('🔧 Language Tests loaded. Run tests with: new LanguageTests().runAllTests()');
        } else {
            console.warn('⚠️ NewsApp not found. Tests cannot run automatically.');
        }
    }, 1000);
}