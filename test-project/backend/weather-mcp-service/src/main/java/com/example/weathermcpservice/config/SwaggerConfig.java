package com.example.weathermcpservice.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI weatherServiceOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("Weather MCP Service API")
                .description("REST API for weather information and alerts")
                .version("1.0.0")
                .contact(new Contact()
                    .name("API Support")
                    .email("support@example.com")));
    }
}