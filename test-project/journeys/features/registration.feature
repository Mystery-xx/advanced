# Registration Journey: Valid Registration → Duplicate Email → Invalid Password → Dashboard

Feature: User Registration Flow
  Registration scenarios with valid and invalid data

  @registration @smoke
  Scenario: Successful registration with valid data
    Given the registration page is displayed
    When the user fills in valid registration details
    And the user submits the registration form
    Then the registration is successful
    And the user is redirected to the dashboard

  @registration @error-handling
  Scenario: Registration fails with duplicate email
    Given the registration page is displayed
    When the user fills in details with an existing email
    And the user submits the registration form
    Then an error message about duplicate email is shown
    And the user remains on the registration page

  @registration @validation
  Scenario: Registration fails with invalid password
    Given the registration page is displayed
    When the user fills in details with a weak password
    And the user submits the registration form
    Then an error message about password requirements is shown
    And the user remains on the registration page