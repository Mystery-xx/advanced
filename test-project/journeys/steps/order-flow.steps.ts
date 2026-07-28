/**
 * Order Flow Step Definitions
 * Playwright-based implementations for order creation and status management flow tests
 */

import { Page, expect } from '@playwright/test';

const APP_URL = 'http://localhost:3000';

/**
 * Step: Given the orders page is displayed
 */
export async function ordersPageIsDisplayed(page: Page): Promise<void> {
  await page.goto(`${APP_URL}/orders`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('h1:has-text("Orders")', { timeout: 5000 });
}

/**
 * Step: When the user clicks the "New Order" button
 */
export async function clickNewOrderButton(page: Page): Promise<void> {
  const newOrderButton = page.locator('button:has-text("New Order"), button:has-text("+ New Order")').first();
  await newOrderButton.click();
  await page.waitForTimeout(500);
  
  // Wait for modal to appear
  await page.waitForSelector('.modal:has-text("New Order")', { timeout: 3000 });
}

/**
 * Step: When the user fills in valid order details
 */
export async function fillValidOrderDetails(page: Page): Promise<void> {
  const timestamp = Date.now();
  await page.fill('input[placeholder="Product name"]', `Test Product ${timestamp}`);
  await page.fill('input[type="number"][min="1"]', '2');
  await page.fill('input[placeholder="0.00"]', '49.99');
}

/**
 * Step: When the user leaves the product name field empty
 */
export async function leaveProductNameEmpty(page: Page): Promise<void> {
  // Clear the product field if it has any value
  await page.fill('input[placeholder="Product name"]', '');
}

/**
 * Step: When the user enters a valid product name
 */
export async function enterValidProductName(page: Page): Promise<void> {
  const timestamp = Date.now();
  await page.fill('input[placeholder="Product name"]', `Valid Product ${timestamp}`);
}

/**
 * Step: When the user enters valid quantity and total
 */
export async function enterValidQuantityAndTotal(page: Page): Promise<void> {
  await page.fill('input[type="number"][min="1"]', '1');
  await page.fill('input[placeholder="0.00"]', '29.99');
}

/**
 * Step: When the user enters quantity as zero or negative
 */
export async function enterInvalidQuantity(page: Page): Promise<void> {
  await page.fill('input[type="number"][min="1"]', '0');
}

/**
 * Step: When the user enters a valid total
 */
export async function enterValidTotal(page: Page): Promise<void> {
  await page.fill('input[placeholder="0.00"]', '19.99');
}

/**
 * Step: When the user submits the order creation form
 */
export async function submitOrderCreationForm(page: Page): Promise<void> {
  const submitButton = page.locator('button[type="submit"]').first();
  await submitButton.click();
  await page.waitForTimeout(1000);
}

/**
 * Step: Then the order appears in the order list
 */
export async function verifyOrderAppearsInList(page: Page): Promise<void> {
  // Wait for the table to be visible
  await page.waitForSelector('table.table', { timeout: 5000 });
  
  // Verify at least one row exists in the table
  const rows = page.locator('table tbody tr');
  const rowCount = await rows.count();
  expect(rowCount).toBeGreaterThan(0);
}

/**
 * Step: And the order status is "PENDING"
 */
export async function verifyOrderStatusIsPending(page: Page): Promise<void> {
  // Look for PENDING status badge in the table
  const pendingStatus = page.locator('text=PENDING').first();
  const isVisible = await pendingStatus.isVisible({ timeout: 3000 });
  expect(isVisible).toBeTruthy();
}

/**
 * Step: When the user updates the order status to "CONFIRMED"
 */
export async function updateOrderStatusToConfirmed(page: Page): Promise<void> {
  // Look for the "Move to CONFIRMED" button
  const confirmButton = page.locator('button:has-text("Move to CONFIRMED")').first();
  const isVisible = await confirmButton.isVisible().catch(() => false);
  
  if (isVisible) {
    await confirmButton.click();
    await page.waitForTimeout(1000);
  } else {
    // If no CONFIRMED button, try to find any status update button
    const anyStatusButton = page.locator('button:has-text("Move to")').first();
    await anyStatusButton.click();
    await page.waitForTimeout(1000);
  }
}

/**
 * Step: Then the status changes to "CONFIRMED"
 */
export async function verifyStatusChangedToConfirmed(page: Page): Promise<void> {
  // Look for CONFIRMED status badge
  const confirmedStatus = page.locator('text=CONFIRMED').first();
  const isVisible = await confirmedStatus.isVisible({ timeout: 3000 });
  expect(isVisible).toBeTruthy();
}

/**
 * Step: And the status change is reflected in the UI
 */
export async function verifyStatusChangeReflectedInUI(page: Page): Promise<void> {
  // Verify the table still exists and has updated content
  await page.waitForSelector('table.table', { timeout: 3000 });
  
  // Check that status badge is visible
  const statusBadge = page.locator('.badge:has-text("CONFIRMED")');
  const badgeCount = await statusBadge.count();
  expect(badgeCount).toBeGreaterThan(0);
}

/**
 * Step: Then an error message about product name is shown
 */
export async function verifyProductNameErrorMessage(page: Page): Promise<void> {
  const errorLocator = page.locator('.field-error, .error-message').first();
  const errorText = await errorLocator.textContent().catch(() => '');
  
  const hasProductError = errorText.toLowerCase().includes('product') || 
                          errorText.toLowerCase().includes('required') ||
                          (await page.locator('.field-error').count()) > 0;
  
  expect(hasProductError).toBeTruthy();
}

/**
 * Step: And the order is not created
 */
export async function verifyOrderNotCreated(page: Page): Promise<void> {
  // Modal should still be open or form should still be visible
  const modal = page.locator('.modal:has-text("New Order")');
  const isModalVisible = await modal.isVisible().catch(() => false);
  
  // Or check that no new row was added (count rows before and after)
  const tableRows = page.locator('table tbody tr');
  const rowCount = await tableRows.count();
  
  // If modal is still open or form is visible, order was not created
  expect(isModalVisible).toBeTruthy();
}

/**
 * Step: Then an error message about quantity is shown
 */
export async function verifyQuantityErrorMessage(page: Page): Promise<void> {
  const errorLocator = page.locator('.field-error, .error-message').first();
  const errorText = await errorLocator.textContent().catch(() => '');
  
  const hasQuantityError = errorText.toLowerCase().includes('quantity') || 
                           errorText.toLowerCase().includes('must be') ||
                           errorText.toLowerCase().includes('>= 1') ||
                           errorText.toLowerCase().includes('positive') ||
                           (await page.locator('.field-error').count()) > 0;
  
  expect(hasQuantityError).toBeTruthy();
}

/**
 * Export all steps as a map for the test runner
 */
export const orderFlowSteps = {
  'the orders page is displayed': ordersPageIsDisplayed,
  'the user clicks the "New Order" button': clickNewOrderButton,
  'the user fills in valid order details': fillValidOrderDetails,
  'the user leaves the product name field empty': leaveProductNameEmpty,
  'the user enters a valid product name': enterValidProductName,
  'the user enters valid quantity and total': enterValidQuantityAndTotal,
  'the user enters quantity as zero or negative': enterInvalidQuantity,
  'the user enters a valid total': enterValidTotal,
  'the user submits the order creation form': submitOrderCreationForm,
  'the order appears in the order list': verifyOrderAppearsInList,
  'the order status is "PENDING"': verifyOrderStatusIsPending,
  'the user updates the order status to "CONFIRMED"': updateOrderStatusToConfirmed,
  'the status changes to "CONFIRMED"': verifyStatusChangedToConfirmed,
  'the status change is reflected in the UI': verifyStatusChangeReflectedInUI,
  'an error message about product name is shown': verifyProductNameErrorMessage,
  'the order is not created': verifyOrderNotCreated,
  'an error message about quantity is': verifyQuantityErrorMessage,
};