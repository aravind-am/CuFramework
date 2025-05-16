package testrunners;

import io.cucumber.testng.AbstractTestNGCucumberTests;
import io.cucumber.testng.CucumberOptions;

@CucumberOptions(
		features="C:\\Users\\aamar\\eclipse-workspace\\automation-hybrid-framework\\src\\test\\resources\\features",
		glue= {"stepdefinitions"},
		plugin = {"pretty", "html:target/cucumber-reports.html"},
		monochrome = true
		)
public class TestRunner extends AbstractTestNGCucumberTests {

}
