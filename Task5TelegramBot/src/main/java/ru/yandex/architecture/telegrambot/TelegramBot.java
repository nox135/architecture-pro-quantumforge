package ru.yandex.architecture.telegrambot;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.telegram.telegrambots.bots.TelegramLongPollingBot;
import org.telegram.telegrambots.meta.api.methods.send.SendMessage;
import org.telegram.telegrambots.meta.api.objects.Update;
import org.telegram.telegrambots.meta.exceptions.TelegramApiException;
import ru.yandex.architecture.telegrambot.config.BotConfig;
import ru.yandex.architecture.telegrambot.dto.QueryResponse;
import ru.yandex.architecture.telegrambot.service.PythonApiClient;

@Slf4j
@Component
@RequiredArgsConstructor
public class TelegramBot extends TelegramLongPollingBot {

    private final BotConfig botConfig;
    private final PythonApiClient pythonApiClient;

    @Override
    public String getBotUsername() {
        return botConfig.getUsername();
    }

    @Override
    public String getBotToken() {
        return botConfig.getToken();
    }

    @Override
    public void onUpdateReceived(Update update) {
        if (update.hasMessage() && update.getMessage().hasText()) {
            String messageText = update.getMessage().getText();
            Long chatId = update.getMessage().getChatId();
            String userName = update.getMessage().getFrom().getUserName();

            log.info("Получено сообщение от пользователя {} (chatId: {}): {}", userName, chatId, messageText);

            // Обработка команд
            if (messageText.startsWith("/")) {
                handleCommand(chatId, messageText);
                return;
            }

            // Обработка обычных сообщений
            handleQuery(chatId, messageText);
        }
    }

    private void handleCommand(Long chatId, String command) {
        SendMessage message = new SendMessage();
        message.setChatId(chatId.toString());

        switch (command) {
            case "/start":
            case "/help":
                message.setText("Привет! Я бот для работы с RAG-сервисом.\n\n" +
                        "Просто отправь мне вопрос о вселенной Star Wars, и я найду ответ в базе знаний.\n\n" +
                        "Команды:\n" +
                        "/start - приветствие\n" +
                        "/help - справка\n" +
                        "/health - проверка состояния сервиса");
                break;
            case "/health":
                boolean isHealthy = pythonApiClient.healthCheck();
                message.setText(isHealthy 
                        ? "✅ Сервис работает нормально" 
                        : "❌ Сервис недоступен. Проверьте, запущен ли Python API сервер.");
                break;
            default:
                message.setText("Неизвестная команда. Используйте /help для справки.");
        }

        sendMessage(message);
    }

    private void handleQuery(Long chatId, String query) {
        SendMessage message = new SendMessage();
        message.setChatId(chatId.toString());

        try {
            // Отправляем индикатор печати
            sendTypingAction(chatId);

            // Вызываем Python API
            QueryResponse response = pythonApiClient.query(query);

            // Формируем ответ
            StringBuilder responseText = new StringBuilder();
            responseText.append(response.getAnswer());

            if (response.getChunksCount() != null && response.getChunksCount() > 0) {
                responseText.append("\n\n📚 Найдено источников: ").append(response.getChunksCount());
            }

            message.setText(responseText.toString());

        } catch (Exception e) {
            log.error("Ошибка при обработке запроса", e);
            message.setText("❌ Произошла ошибка при обработке вашего запроса. " +
                    "Проверьте, что Python API сервер запущен и доступен.");
        }

        sendMessage(message);
    }

    private void sendMessage(SendMessage message) {
        try {
            execute(message);
        } catch (TelegramApiException e) {
            log.error("Ошибка при отправке сообщения в Telegram", e);
        }
    }

    private void sendTypingAction(Long chatId) {
        try {
            org.telegram.telegrambots.meta.api.methods.send.SendChatAction action = 
                    new org.telegram.telegrambots.meta.api.methods.send.SendChatAction();
            action.setChatId(chatId.toString());
            action.setAction(org.telegram.telegrambots.meta.api.methods.ActionType.TYPING);
            execute(action);
        } catch (TelegramApiException e) {
            log.warn("Не удалось отправить индикатор печати", e);
        }
    }
}

