package utilities;

import java.io.FileInputStream;
import java.util.HashMap;
import org.apache.poi.xssf.usermodel.XSSFRow;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import io.cucumber.java.Before;
import io.cucumber.java.Scenario;

public class ExecutionHooks {
	
	private static String filePath;
	static HashMap<String, String> scenarioMap;
	
	public static HashMap<String, String> getScenarioExecutions(String filePath, String sheetName) {
		HashMap<String, String> map = new HashMap<>();
		
		try(FileInputStream fis = new FileInputStream(filePath);
				XSSFWorkbook wb = new XSSFWorkbook(fis)){
			XSSFSheet sheet = wb.getSheet(sheetName);
			int rowCount = sheet.getPhysicalNumberOfRows();
			
			for(int i= 1; i<rowCount; i++)
			{
				XSSFRow row = sheet.getRow(i);
				String scenario = row.getCell(0).getStringCellValue().trim();
				String executionFlag = row.getCell(1).getStringCellValue().trim();
				map.put(scenario, executionFlag);
			}
		} catch(Exception e) {
			e.printStackTrace();
		}
		return map;
	}
	
	public ExecutionHooks() {
		scenarioMap = getScenarioExecutions(filePath, "Scenarios");
	}
	
	@Before
	public static void getTestScenarios(Scenario scenario) {
		String scenarioName = scenario.getName();
		
		String executionFlag = scenarioMap.getOrDefault(scenarioName, "N");
		
		if(!executionFlag.equalsIgnoreCase("Y")) {
			System.out.println("Skipping scenario....>"+scenarioName);
			throw new io.cucumber.java.PendingException("Skipped by execution flag in Excel");
		}
	}
}
