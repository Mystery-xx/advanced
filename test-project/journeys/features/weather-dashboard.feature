# Weather Dashboard Journey: Login → Weather Dashboard → View Current → Create Alert → Export → Verify

Feature: Weather Dashboard Journey
  Complete weather dashboard flow from login to alert verification with MCP integration

  Background:
    Given the user is on the login page
    When the user logs in with valid credentials
    Then the user is redirected to the weather dashboard

  Scenario: View current weather and create alert
    # Direction: Login → Weather Dashboard → View current → Create alert → Export → Verify
    Given the weather dashboard displays current weather for the default city
    When the user views current weather conditions
    Then the temperature, humidity, and wind speed are displayed
    When the user creates a weather alert for temperature threshold
    Then the alert is saved and appears in the alerts list
    When the user exports the weather data
    Then the export file is generated and downloaded
    And the user verifies the alert configuration is active