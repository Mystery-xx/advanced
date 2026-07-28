/**
 * User Flow Step Definitions
 * Playwright-based implementations for login → view users → logout flow tests
 */

import { Page, expect } from '@playwright/test';

const APP_URL = 'http://localhost:3000';

/**
 * Step: Given the login page is displayed
 */
export async function loginPageIsDisplayed(page: Page): Promise<void> {
  await page.goto(`${APP_URL}/login`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#email', { timeout: 5000 });
}

/**
 * Step: When the user enters valid credentials
 */
export async function enterValidCredentials(page: Page): Promise<void> {
  const timestamp = Date.now();
  await page.fill('#email', `testuser${timestamp}@example.com`);
  await page.fill('#password', 'SecurePass123');
}

/**
 * Step: When the user enters invalid credentials
 */
export async function enterInvalidCredentials(page: Page): Promise<void> {
  await page.fill('#email', 'invalid@example.com');
  await page.fill('#password', 'wrongpassword');
}

/**
 * Step: When the user submits the login form
 */
export async function submitLoginForm(page: Page): Promise<void> {
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1500);
}

/**
 * Step: Then the user is redirected to the users page
 */
export async function verifyRedirectToUsersPage(page: Page): Promise<void> {
  const currentUrl = page.url();
  expect(currentUrl).toBe(`${APP_URL}/users`);
  
  // Wait for users page content to load
  await page.waitForTimeout(500);
}

/**
 * Step: And the user list is displayed correctly
 */
export async function verifyUserListDisplayed(page: Page): Promise<void> {
  // Wait for the table to be visible
  await page.waitForSelector('table.table', { timeout: 5000 });
  
  // Verify table headers exist
  const headers = page.locator('table thead th');
  const headerCount = await headers.count();
  expect(headerCount).toBeGreaterThan(0);
  
  // Verify at least one user row exists (could be mock data)
  const rows = page.locator('table tbody tr');
  const rowCount = await rows.count();
  expect(rowCount).toBeGreaterThan(0);
  
  // Verify expected columns are present
  const headerTexts = await headers.allTextContents();
  expect(headerTexts).toContainEqual(expect.stringContaining('Name'));
  expect(headerTexts).toContainEqual(expect.stringContaining('Email'));
  expect(headerTexts).toContainEqual(expect.stringContaining('Role'));
  expect(headerTexts).toContainEqual(expect.stringContaining('Status'));
}

/**
 * Step: When the user clicks the logout button
 */
export async function clickLogoutButton(page: Page): Promise<void> {
  // Look for logout button in header
  const logoutButton = page.locator('button:has-text("Logout"), button:has-text("logout")').first();
  await logoutButton.click();
  await page.waitForTimeout(1000);
}

/**
 * Step: Then the user is logged out successfully
 */
export async function verifyUserLoggedOut(page: Page): Promise<void> {
  // Verify auth tokens are cleared (check if login page is shown)
  const currentUrl = page.url();
  
  // After logout, should be redirected to login page
  expect(currentUrl).toBe(`${APP_URL}/login`);
  
  // Verify login form is visible (not authenticated content)
  await expect(page.locator('#email')).toBeVisible();
  await expect(page.locator('#password')).toBeVisible();
}

/**
 * Step: And the user is redirected to the login page
 */
export async function verifyRedirectToLoginPage(page: Page): Promise<void> {
  const currentUrl = page.url();
  expect(currentUrl).toBe(`${APP_URL}/login`);
}

/**
 * Step: Then an error message about invalid credentials is shown
 */
export async function verifyInvalidCredentialsError(page: Page): Promise<void> {
  const errorLocator = page.locator('.alert-error, .error-message, .field-error').first();
  const errorText = await errorLocator.textContent().catch(() => '');
  
  const hasError = errorText.toLowerCase().includes('invalid') || 
                   errorText.toLowerCase().includes('credentials') ||
                   errorText.toLowerCase().includes('try again') ||
                   (await page.locator('.alert-error').count()) > 0;
  
  expect(hasError).toBeTruthy();
}

/**
 * Step: And the user remains on the login page
 */
export async function verifyRemainsOnLoginPage(page: Page): Promise<void> {
  const currentUrl = page.url();
  expect(currentUrl).toBe(`${APP_URL}/login`);
  
  // Login form should still be visible
  await expect(page.locator('#email')).toBeVisible();
  await expect(page.locator('#password')).toBeVisible();
}

/**
 * Export all steps as a map for the test runner
 */
export const userFlowSteps = {
  'the login page is displayed': loginPageIsDisplayed,
  'the user enters valid credentials': enterValidCredentials,
  'the user enters invalid credentials': enterInvalidCredentials,
  'the user submits the login form': submitLoginForm,
  'the user is redirected to the users page': verifyRedirectToUsersPage,
  'the user list is displayed correctly': verifyUserListDisplayed,
  'the user clicks the logout button': clickLogoutButton,
  'the user is logged out successfully': verifyUserLoggedOut,
  'the user is redirected to the login page': verifyRedirectToLoginPage,
  'an error message about invalid credentials is shown': verifyInvalidCredentialsError,
  'the user remains on the login page': verifyRemainsOnLoginPage,
};