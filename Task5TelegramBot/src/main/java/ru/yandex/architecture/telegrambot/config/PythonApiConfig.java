package ru.yandex.architecture.telegrambot.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "python.api")
public class PythonApiConfig {
    private String url = "http://localhost:8000";
    private int timeout = 30000;
}

