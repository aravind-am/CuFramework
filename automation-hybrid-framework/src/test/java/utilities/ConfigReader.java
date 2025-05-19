package utilities;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

public class ConfigReader {
	private static Properties properties;

    static {
        try(InputStream fis = ConfigReader.class.getResourceAsStream("/config/config.properties")) {
            if(fis != null) {
            	 //properties = new Properties();
                 properties.load(fis);
            }
           
        } catch (IOException e) {
            e.printStackTrace();
            throw new RuntimeException("Failed to load config.properties");
        }
    }

	public static String getProperty(String property) {
		
		return  properties.getProperty(property);
		
	}

}
