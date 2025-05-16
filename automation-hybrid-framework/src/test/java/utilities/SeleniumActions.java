package utilities;

import java.net.URL;
import java.time.Duration;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class SeleniumActions {
	
	 private WebDriver driver;
	 private WebDriverWait wait;
	 private Actions action;
	 
	 public SeleniumActions(WebDriver driver){
		 this.driver = driver;
		 this.wait = new WebDriverWait(driver, Duration.ofSeconds(30), Duration.ofMillis(10));
		 this.action = new Actions(driver);
	 }
	 
	 	public void navigateTo(String URL) {
	 		driver.navigate().to(URL);
	 	}
	 	
	    public void click(By locator) {
	        wait.until(ExpectedConditions.elementToBeClickable(locator)).click();
	    }

	    public void sendKeys(By locator, String text) {
	        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
	        element.clear();
	        element.sendKeys(text);
	    }

	    public void mouseHover(By locator) {
	        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
	        action.moveToElement(element).perform();
	    }

	    public String getText(By locator) {
	        return wait.until(ExpectedConditions.visibilityOfElementLocated(locator)).getText();
	    }

	    public boolean isDisplayed(By locator) {
	        try {
	            return wait.until(ExpectedConditions.visibilityOfElementLocated(locator)).isDisplayed();
	        } catch (Exception e) {
	            return false;
	        }
	    }

	    public void clickUsingActions(By locator) {
	        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(locator));
	        action.moveToElement(element).click().perform();
	    }
}
