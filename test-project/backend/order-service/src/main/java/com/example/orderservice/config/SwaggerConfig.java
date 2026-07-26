package com.example.orderservice.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI orderServiceOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("Order Service API")
                .description("REST API for order management with status tracking")
                .version("1.0.0")
                .contact(new Contact()
                    .name("API Support")
                    .email("support@example.com")));
    }
}