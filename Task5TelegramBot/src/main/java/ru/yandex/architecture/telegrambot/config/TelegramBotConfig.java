package ru.yandex.architecture.telegrambot.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;
import org.telegram.telegrambots.meta.TelegramBotsApi;
import org.telegram.telegrambots.meta.exceptions.TelegramApiException;
import org.telegram.telegrambots.updatesreceivers.DefaultBotSession;
import ru.yandex.architecture.telegrambot.TelegramBot;

import jakarta.annotation.PostConstruct;

@Configuration
@RequiredArgsConstructor
public class TelegramBotConfig {

    private final TelegramBot telegramBot;

    @PostConstruct
    public void registerBot() {
        try {
            TelegramBotsApi api =  new TelegramBotsApi(DefaultBotSession.class);
            api.registerBot(telegramBot);
            System.out.println("Telegram бот успешно зарегистрирован");
        } catch (TelegramApiException e) {
            System.err.println("Ошибка при регистрации Telegram бота: " + e.getMessage());
            throw new RuntimeException("Не удалось зарегистрировать Telegram бота", e);
        }
    }
}

