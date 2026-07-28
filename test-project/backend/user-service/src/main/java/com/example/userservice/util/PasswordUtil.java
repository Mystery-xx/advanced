package com.example.userservice.util;

import java.util.regex.Pattern;

public class PasswordUtil {

    private static final Pattern LETTER_PATTERN = Pattern.compile("[a-zA-Z]");
    private static final Pattern NUMBER_PATTERN = Pattern.compile("\\d");
    private static final int MIN_LENGTH = 8;

    private PasswordUtil() {
    }

    public static void validatePassword(String password) {
        if (password == null || password.isEmpty()) {
            throw new IllegalArgumentException("Password is required");
        }

        if (password.length() < MIN_LENGTH) {
            throw new IllegalArgumentException("Password must be at least 8 characters");
        }

        if (!LETTER_PATTERN.matcher(password).find()) {
            throw new IllegalArgumentException("Password must contain at least one letter");
        }

        if (!NUMBER_PATTERN.matcher(password).find()) {
            throw new IllegalArgumentException("Password must contain at least one number");
        }
    }

    public static boolean isValidPassword(String password) {
        try {
            validatePassword(password);
            return true;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }
}