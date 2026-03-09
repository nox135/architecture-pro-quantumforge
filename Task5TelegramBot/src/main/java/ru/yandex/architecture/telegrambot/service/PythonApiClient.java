package ru.yandex.architecture.telegrambot.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import ru.yandex.architecture.telegrambot.config.PythonApiConfig;
import ru.yandex.architecture.telegrambot.dto.QueryRequest;
import ru.yandex.architecture.telegrambot.dto.QueryResponse;

import java.time.Duration;

@Slf4j
@Service
@RequiredArgsConstructor
public class PythonApiClient {

    private final PythonApiConfig apiConfig;
    private final WebClient webClient;

    public QueryResponse query(String userQuery) {
        try {
            log.info("Отправка запроса в Python API: {}", userQuery);
            
            QueryRequest request = new QueryRequest(userQuery, 3);
            
            QueryResponse response = webClient.post()
                    .uri(apiConfig.getUrl() + "/query")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(QueryResponse.class)
                    .timeout(Duration.ofMillis(apiConfig.getTimeout()))
                    .block();
            
            log.info("Получен ответ от Python API. Чанков: {}", 
                    response != null ? response.getChunksCount() : 0);
            
            return response;
        } catch (WebClientResponseException e) {
            log.error("Ошибка при вызове Python API: {} - {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new RuntimeException("Ошибка при обращении к Python API: " + e.getMessage(), e);
        } catch (Exception e) {
            log.error("Неожиданная ошибка при вызове Python API", e);
            throw new RuntimeException("Ошибка при обращении к Python API: " + e.getMessage(), e);
        }
    }

    public boolean healthCheck() {
        try {
            String response = webClient.get()
                    .uri(apiConfig.getUrl() + "/health")
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(5000))
                    .block();
            
            log.info("Health check успешен: {}", response);
            return true;
        } catch (Exception e) {
            log.warn("Health check не удался: {}", e.getMessage());
            return false;
        }
    }
}

