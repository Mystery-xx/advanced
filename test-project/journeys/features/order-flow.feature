# Order Flow Journey: Create Order → Update Status → Verify in List → Validation Errors

Feature: Order Creation and Status Management Flow
  Order lifecycle scenarios including creation, status updates, and validation

  @order-flow @smoke
  Scenario: User creates a new order and updates its status
    Given the orders page is displayed
    When the user clicks the "New Order" button
    And the user fills in valid order details
    And the user submits the order creation form
    Then the order appears in the order list
    And the order status is "P"
    When user updates the order status toCONFIRMED
    Then the status changes toCONFIRMED"
    And the status change is reflected in the UI

  @order-flow @validation
  Scenario: Order creation fails with empty product name
    Given the orders page is displayed
    When the user clicks the "New Order" button
    And the user leaves the product name field empty
    And the user enters valid quantity and total
    And the user submits the order creation form
    Then an error message about product name is shown
    And the order is not created

  @order-flow @validation
  Scenario: Order creation fails with invalid quantity
    Given the orders page is displayed
    When the user clicks the "New Order" button
    And the user enters a valid product name
    And the user enters quantity as zero or negative
    And the user enters a valid total
    And the user submits the order creation form
    Then an error message about quantity is shown
    And the order is not created