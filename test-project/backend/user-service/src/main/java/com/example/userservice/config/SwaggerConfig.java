package com.example.userservice.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI userServiceOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("User Service API")
                .description("REST API for user management with role-based access control")
                .version("1.0.0")
                .contact(new Contact()
                    .name("API Support")
                    .email("support@example.com")));
    }
}