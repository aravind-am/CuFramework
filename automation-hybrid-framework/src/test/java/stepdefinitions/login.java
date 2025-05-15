package stepdefinitions;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import utilities.BrowserIntialization;
import utilities.SeleniumActions;

public class login {
	
	SeleniumActions actions;
	WebDriver driver;
	
	@Given("I launch the browser")
	public void i_launch_the_browser() {
	    // Write code here that turns the phrase above into concrete actions
	   driver = BrowserIntialization.launch("chrome");
	   actions = new SeleniumActions(driver);
	   
	}

	@When("I open the login page")
	public void i_open_the_login_page() {
		actions.navigateTo("https://www.google.com/");
	   
	}

	@When("I enter username {string} and password {string}")
	public void i_enter_username_and_password(String userName, String password) {
		    actions.sendKeys(By.id("username"), userName);
	        actions.sendKeys(By.id("password"), password);
	}

	@Then("I should see the homepage")
	public void i_should_see_the_homepage() {
	    // Write code here that turns the phrase above into concrete actions
	    throw new io.cucumber.java.PendingException();
	}


}
