package pages;

import java.util.Objects;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

import utilities.SeleniumActions;

public class LoginPage {
    private static final By USERNAME_FIELD = By.id("username");
    private static final By PASSWORD_FIELD = By.id("password");
    private static final By LOGIN_BUTTON = By.id("login");

    private final SeleniumActions actions;

    public LoginPage(WebDriver driver) {
        this.actions = new SeleniumActions(Objects.requireNonNull(driver, "driver must not be null"));
    }

    public void login(String username, String password) {
        actions.sendKeys(USERNAME_FIELD, username);
        actions.sendKeys(PASSWORD_FIELD, password);
        actions.click(LOGIN_BUTTON);
    }
}
