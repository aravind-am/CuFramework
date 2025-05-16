package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

import utilities.SeleniumActions;

public class loginPage {
	private WebDriver driver;
    private SeleniumActions actions;

    public loginPage(WebDriver driver) {
        this.driver = driver;
        this.actions = new SeleniumActions(driver);
    }

    private By usernameField = By.id("username");
    private By passwordField = By.id("password");
    private By loginButton = By.id("login");

    public void login(String username, String password) {
        actions.sendKeys(usernameField, username);
        actions.sendKeys(passwordField, password);
        actions.click(loginButton);
    }
}
