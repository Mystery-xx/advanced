package com.example.paymentservice.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI paymentServiceOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("Payment Service API")
                .description("REST API for payment processing and refunds")
                .version("1.0.0")
                .contact(new Contact()
                    .name("API Support")
                    .email("support@example.com")));
    }
}