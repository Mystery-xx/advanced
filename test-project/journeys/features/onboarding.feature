# Onboarding Journey: Registration → Email Confirm → Login → Profile → Edit → Verify

Feature: User Onboarding Journey
  Complete onboarding flow from registration to profile verification

  Scenario: New user completes full onboarding
    # Direction: Registration → Email confirm → Login → Profile → Edit → Verify
    Given the registration page is accessible
    When a new user submits valid registration details
    Then a confirmation email is sent to the user
    When the user clicks the email confirmation link
    Then the email address is verified
    When the user logs in with confirmed credentials
    Then the user is redirected to the profile page
    When the user updates their profile information
    Then the profile changes are saved and displayed