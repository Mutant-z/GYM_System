package com.example.gym.agent.service;

import com.example.gym.agent.dto.AgentChatRequest;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.common.api.ResultCode;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class AgentGatewayService {

    private static final Logger log = LoggerFactory.getLogger(AgentGatewayService.class);
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;
    private final String agentBaseUrl;
    private final Duration requestTimeout;

    public AgentGatewayService(
            ObjectMapper objectMapper,
            @Value("${agent.base-url:http://localhost:8000}") String agentBaseUrl,
            @Value("${agent.request-timeout:180s}") Duration requestTimeout
    ) {
        this.objectMapper = objectMapper;
        this.agentBaseUrl = agentBaseUrl;
        this.requestTimeout = requestTimeout;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .version(HttpClient.Version.HTTP_1_1)
                .build();
    }

    public Map<String, Object> chat(AgentChatRequest request) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("text", request.getText());
        payload.put("user_id", request.getUserId());
        payload.put("auth_token", request.getAuthToken());
        payload.put("conversation_id", request.getConversationId());
        payload.put("metadata", request.getMetadata());

        String targetUrl = agentBaseUrl.replaceAll("/+$", "") + "/chat";
        log.info(
                "Forwarding agent chat request to Python service: url={}, userId={}, conversationId={}, textLength={}, metadataKeys={}",
                targetUrl,
                request.getUserId(),
                request.getConversationId(),
                request.getText() == null ? 0 : request.getText().length(),
                request.getMetadata() == null ? 0 : request.getMetadata().keySet()
        );

        HttpRequest httpRequest;
        try {
            httpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(targetUrl))
                    .timeout(requestTimeout)
                    .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                    .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(payload)))
                    .build();
        } catch (Exception ex) {
            log.error("Failed to build request for Python agent", ex);
            throw new BusinessException(ResultCode.INTERNAL_ERROR, "failed to build agent request");
        }

        HttpResponse<String> response;
        try {
            response = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString());
        } catch (IOException | InterruptedException ex) {
            if (ex instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            log.error("Python agent request failed", ex);
            if (ex instanceof java.net.http.HttpTimeoutException) {
                long timeoutSeconds = requestTimeout.truncatedTo(ChronoUnit.SECONDS).toSeconds();
                throw new BusinessException(
                        ResultCode.SERVICE_UNAVAILABLE,
                        "agent request timed out after " + timeoutSeconds + "s"
                );
            }
            throw new BusinessException(ResultCode.SERVICE_UNAVAILABLE, "agent service is unavailable");
        }

        String body = response.body();
        log.info(
                "Python agent response received: status={}, bodyLength={}",
                response.statusCode(),
                body == null ? 0 : body.length()
        );
        Map<String, Object> parsedBody;
        try {
            parsedBody = objectMapper.readValue(body, MAP_TYPE);
        } catch (Exception ex) {
            log.error("Python agent response is not valid JSON: body={}", truncate(body), ex);
            throw new BusinessException(ResultCode.INTERNAL_ERROR, "agent response is not valid json");
        }

        if (response.statusCode() >= 500) {
            log.warn("Python agent returned 5xx: status={}, payload={}", response.statusCode(), truncate(body));
            throw new BusinessException(ResultCode.SERVICE_UNAVAILABLE, extractMessage(parsedBody, "agent service error"));
        }
        if (response.statusCode() >= 400) {
            log.warn("Python agent returned 4xx: status={}, payload={}", response.statusCode(), truncate(body));
            throw new BusinessException(ResultCode.BAD_REQUEST, extractMessage(parsedBody, "agent request failed"));
        }

        log.info("Python agent chat completed successfully: keys={}", parsedBody.keySet());
        return parsedBody;
    }

    private String extractMessage(Map<String, Object> payload, String fallback) {
        if (payload == null) {
            return fallback;
        }
        Object detail = payload.get("detail");
        if (detail instanceof String detailText && !detailText.isBlank()) {
            return detailText;
        }
        if (detail instanceof List<?> detailList && !detailList.isEmpty()) {
            return detailList.toString();
        }
        Object message = payload.get("message");
        if (message instanceof String messageText && !messageText.isBlank()) {
            return messageText;
        }
        Object answer = payload.get("answer");
        if (answer instanceof String answerText && !answerText.isBlank()) {
            return answerText;
        }
        return fallback;
    }

    private String truncate(String text) {
        if (text == null) {
            return "";
        }
        String trimmed = text.trim();
        if (trimmed.length() <= 600) {
            return trimmed;
        }
        return trimmed.substring(0, 600) + "...";
    }
}
