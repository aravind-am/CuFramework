#Author: aam.aravind@gmail.com
#Keywords Summary :
#Feature: Login Test for a sample page
#Scenario: User is able to successfully login to the page

@tag=loginTests
Feature: Login Functionality

  Scenario: Valid login
    Given I launch the browser
    When I open the login page
    And I enter username "admin" and password "admin123"
    Then I should see the homepage
      