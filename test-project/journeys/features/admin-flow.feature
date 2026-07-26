# Admin Journey: Login → Admin Panel → Search → Filter → Block → Unblock → Verify

Feature: Admin User Management Flow
  Admin panel user management with search, filter, block, and unblock operations

  Background:
    Given the login page is accessible

  @admin @journey-3
  Scenario: Admin manages user access
    # Direction: Login as Admin → Admin panel → Search → Filter → Block → Unblock → Verify
    Given an admin user logs in with admin credentials
    When the admin navigates to the admin panel
    And the admin searches for a specific user by email
    And the admin filters users by role
    And the admin blocks a user account
    Then the user status shows as blocked
    When the admin unblocks the same user
    Then the user status shows as active
    And the user list reflects the updated status