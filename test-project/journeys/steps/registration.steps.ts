/**
 * Registration Feature Step Definitions
 * Playwright-based implementations for registration flow tests
 */

import { Page, expect } from '@playwright/test';

const APP_URL = 'http://localhost:3000';

/**
 * Step: Given the registration page is displayed
 */
export async function registrationPageIsDisplayed(page: Page): Promise<void> {
  await page.goto(`${APP_URL}/register`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#name', { timeout: 5000 });
}

/**
 * Step: When the user fills in valid registration details
 */
export async function fillValidRegistrationDetails(page: Page): Promise<void> {
  const timestamp = Date.now();
  await page.fill('#name', `Test User ${timestamp}`);
  await page.fill('#email', `testuser${timestamp}@example.com`);
  await page.fill('#password', 'SecurePass123');
  await page.fill('#confirmPassword', 'SecurePass123');
}

/**
 * Step: When the user fills in details with an existing email
 */
export async function fillDuplicateEmailDetails(page: Page): Promise<void> {
  await page.fill('#name', 'Existing User');
  await page.fill('#email', 'existing@example.com');
  await page.fill('#password', 'SecurePass123');
  await page.fill('#confirmPassword', 'SecurePass123');
}

/**
 * Step: When the user fills in details with a weak password
 */
export async function fillWeakPasswordDetails(page: Page): Promise<void> {
  const timestamp = Date.now();
  await page.fill('#name', `Test User ${timestamp}`);
  await page.fill('#email', `weakpass${timestamp}@example.com`);
  await page.fill('#password', '123');
  await page.fill('#confirmPassword', '123');
}

/**
 * Step: When the user submits the registration form
 */
export async function submitRegistrationForm(page: Page): Promise<void> {
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1000);
}

/**
 * Step: Then the registration is successful
 */
export async function verifyRegistrationSuccess(page: Page): Promise<void> {
  // Check for success indicators: either redirect or success message
  const currentUrl = page.url();
  const hasSuccessMessage = await page.locator('.alert-success, .success-message').count() > 0;
  const redirected = currentUrl !== `${APP_URL}/register`;
  
  expect(redirected || hasSuccessMessage).toBeTruthy();
}

/**
 * Step: And the user is redirected to the dashboard
 */
export async function verifyRedirectToDashboard(page: Page): Promise<void> {
  const currentUrl = page.url();
  // Dashboard could be at / or /dashboard
  expect(currentUrl).toMatch(/^(http:\/\/localhost:3000\/|http:\/\/localhost:3000\/dashboard)/);
  
  // Wait for dashboard content to load
  await page.waitForTimeout(500);
}

/**
 * Step: Then an error message about duplicate email is shown
 */
export async function verifyDuplicateEmailError(page: Page): Promise<void> {
  const errorLocator = page.locator('.field-error, .alert-error, .error-message');
  const errorCount = await errorLocator.count();
  
  expect(errorCount).toBeGreaterThan(0);
  
  // Check if any error mentions email
  const errorText = await errorLocator.first().textContent();
  expect(errorText?.toLowerCase()).toMatch(/email|already|exists|duplicate/i);
}

/**
 * Step: And the user remains on the registration page
 */
export async function verifyRemainsOnRegistrationPage(page: Page): Promise<void> {
  const currentUrl = page.url();
  expect(currentUrl).toBe(`${APP_URL}/register`);
  
  // Form should still be visible
  await expect(page.locator('#email')).toBeVisible();
}

/**
 * Step: Then an error message about password requirements is shown
 */
export async function verifyPasswordRequirementsError(page: Page): Promise<void> {
  const errorLocator = page.locator('.field-error, .alert-error, .error-message');
  const errorCount = await errorLocator.count();
  
  expect(errorCount).toBeGreaterThan(0);
  
  // Check if any error mentions password
  const errorText = await errorLocator.first().textContent();
  expect(errorText?.toLowerCase()).toMatch(/password|weak|characters|requirements/i);
}

/**
 * Export all steps as a map for the test runner
 */
export const registrationSteps = {
  'the registration page is displayed': registrationPageIsDisplayed,
  'the user fills in valid registration details': fillValidRegistrationDetails,
  'the user fills in details with an existing email': fillDuplicateEmailDetails,
  'the user fills in details with a weak password': fillWeakPasswordDetails,
  'the user submits the registration form': submitRegistrationForm,
  'the registration is successful': verifyRegistrationSuccess,
  'the user is redirected to the dashboard': verifyRedirectToDashboard,
  'an error message about duplicate email is shown': verifyDuplicateEmailError,
  'the user remains on the registration page': verifyRemainsOnRegistrationPage,
  'an error message about password requirements is shown': verifyPasswordRequirementsError,
};