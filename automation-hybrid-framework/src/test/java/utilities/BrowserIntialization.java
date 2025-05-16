package utilities;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;

import io.github.bonigarcia.wdm.WebDriverManager;

public class BrowserIntialization {
	private static WebDriver driver;

    public static WebDriver launch(String browserName) {
    	
    	if(driver == null) {
        if (browserName.equalsIgnoreCase("chrome")) {
            WebDriverManager.chromedriver().setup();
            driver = new ChromeDriver();
        } else if (browserName.equalsIgnoreCase("firefox")) {
            WebDriverManager.firefoxdriver().setup();
            driver = new FirefoxDriver();
        } else {
            throw new IllegalArgumentException("Browser not supported: " + browserName);
        }
        driver.manage().window().maximize();
        
    	}
    	return driver; 
    }
    

    public static WebDriver getDriver() {
        return driver;
    }

    public static void quit() {
        if (driver != null) {
            driver.quit();
            driver = null;
        }
    }
}
