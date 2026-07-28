# User Flow Journey: Login → View Users → Logout

Feature: User Login and Navigation Flow
  Complete user flow from login through viewing users list to logout

  @user-flow @smoke
  Scenario: User logs in, views users list, and logs out successfully
    Given the login page is displayed
    When the user enters valid credentials
    And the user submits the login form
    Then the user is redirected to the users page
    And the user list is displayed correctly
    When the user clicks the logout button
    Then the user is logged out successfully
    And the user is redirected to the login page

  @user-flow @validation
  Scenario: Login fails with invalid credentials
    Given the login page is displayed
    When the user enters invalid credentials
    And the user submits the login form
    Then an error message about invalid credentials is shown
    And the user remains on the login page