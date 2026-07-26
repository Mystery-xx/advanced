Feature: Order Flow Journey
  Complete order flow from login to delivery verification

  Background:
    Given the user is on the login page
    When the user logs in with valid credentials
    Then the user is redirected to the home page

  Scenario: Complete order with status transitions
    Given the user browses available products
    When the user adds products to cart
    And the user proceeds to checkout
    And the user enters shipping information
    And the user completes payment
    Then the order status is NEW
    When the payment is confirmed
    Then the order status becomes PAID
    When the order is shipped
    Then the order status becomes SHIPPED
    When the order is delivered
    Then the order status becomes DELIVERED
    And the user can track the order
    And the user verifies the final order status