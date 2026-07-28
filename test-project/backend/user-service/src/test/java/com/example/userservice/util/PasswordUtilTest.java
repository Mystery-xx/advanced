package com.example.userservice.util;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@DisplayName("PasswordUtil Unit Tests")
class PasswordUtilTest {

    @Test
    @DisplayName("validatePassword should accept valid password with letters and numbers")
    void validatePassword_WithValidPassword_ShouldNotThrowException() {
        String validPassword = "Password123";

        PasswordUtil.validatePassword(validPassword);
    }

    @Test
    @DisplayName("validatePassword should accept minimum length password (8 chars)")
    void validatePassword_WithMinimumLength_ShouldNotThrowException() {
        String validPassword = "Pass1234";

        PasswordUtil.validatePassword(validPassword);
    }

    @Test
    @DisplayName("validatePassword should throw exception when password is null")
    void validatePassword_WithNullPassword_ShouldThrowException() {
        assertThatThrownBy(() -> PasswordUtil.validatePassword(null))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessage("Password is required");
    }

    @Test
    @DisplayName("validatePassword should throw exception when password is empty")
    void validatePassword_WithEmptyPassword_ShouldThrowException() {
        assertThatThrownBy(() -> PasswordUtil.validatePassword(""))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessage("Password is required");
    }

    @Test
    @DisplayName("validatePassword should throw exception when password is too short")
    void validatePassword_WithShortPassword_ShouldThrowException() {
        String shortPassword = "Pass1";

        assertThatThrownBy(() -> PasswordUtil.validatePassword(shortPassword))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessage("Password must be at least 8 characters");
    }

    @Test
    @DisplayName("validatePassword should throw exception when password has no letters")
    void validatePassword_WithNoLetters_ShouldThrowException() {
        String noLettersPassword = "12345678";

        assertThatThrownBy(() -> PasswordUtil.validatePassword(noLettersPassword))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessage("Password must contain at least one letter");
    }

    @Test
    @DisplayName("validatePassword should throw exception when password has no numbers")
    void validatePassword_WithNoNumbers_ShouldThrowException() {
        String noNumbersPassword = "Password";

        assertThatThrownBy(() -> PasswordUtil.validatePassword(noNumbersPassword))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessage("Password must contain at least one number");
    }

    @Test
    @DisplayName("validatePassword should accept password with special characters")
    void validatePassword_WithSpecialCharacters_ShouldNotThrowException() {
        String passwordWithSpecialChars = "Pass123!@#";

        PasswordUtil.validatePassword(passwordWithSpecialChars);
    }

    @Test
    @DisplayName("isValidPassword should return true for valid password")
    void isValidPassword_WithValidPassword_ShouldReturnTrue() {
        String validPassword = "Password123";

        boolean result = PasswordUtil.isValidPassword(validPassword);

        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("isValidPassword should return false for invalid password")
    void isValidPassword_WithInvalidPassword_ShouldReturnFalse() {
        String invalidPassword = "short";

        boolean result = PasswordUtil.isValidPassword(invalidPassword);

        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("isValidPassword should return false for null password")
    void isValidPassword_WithNullPassword_ShouldReturnFalse() {
        boolean result = PasswordUtil.isValidPassword(null);

        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("isValidPassword should return false for password without numbers")
    void isValidPassword_WithNoNumbers_ShouldReturnFalse() {
        String password = "NoNumbers";

        boolean result = PasswordUtil.isValidPassword(password);

        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("isValidPassword should return false for password without letters")
    void isValidPassword_WithNoLetters_ShouldReturnFalse() {
        String password = "12345678";

        boolean result = PasswordUtil.isValidPassword(password);

        assertThat(result).isFalse();
    }
}