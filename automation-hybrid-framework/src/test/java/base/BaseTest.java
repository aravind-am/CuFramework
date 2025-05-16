package base;

import io.cucumber.java.After;
import io.cucumber.java.Before;
import utilities.BrowserIntialization;

public class BaseTest {

	@Before
	public void setup() {
		BrowserIntialization.launch("chrome");
	}
	
	@After
	public void tearDown() {
		BrowserIntialization.quit();
	}
	
}
