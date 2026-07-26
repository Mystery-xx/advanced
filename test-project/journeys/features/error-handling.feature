# Error Handling Journey: Open Form → Invalid Email → Verify Error → Fix → Weak Password → Verify Error → Fix → Success

Feature: Error Handling and Recovery Journey
  Form validation error scenarios with recovery paths

  Scenario: User encounters and recovers from validation errors
    # Direction: Open form → Invalid email → Verify error → Fix → Weak password → Verify error → Fix → Success
    Given the registration form is displayed
    When the user submits the form with an invalid email format
    Then an error message "Please enter a valid email address" is shown
    When the user corrects the email to a valid format
    And the user enters a weak password "123"
    And the user submits the form
    Then an error message "Password must be at least 8 characters with uppercase, lowercase, and number" is shown
    When the user enters a strong password "SecurePass123"
    And the user submits the form again
    Then the registration is successful and the user is redirected to the dashboard