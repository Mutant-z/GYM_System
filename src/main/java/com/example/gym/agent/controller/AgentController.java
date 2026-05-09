package com.example.gym.agent.controller;

import com.example.gym.agent.dto.AgentChatRequest;
import com.example.gym.agent.service.AgentGatewayService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/chat")
public class AgentController {

    private static final Logger log = LoggerFactory.getLogger(AgentController.class);

    private final AgentGatewayService agentGatewayService;

    public AgentController(AgentGatewayService agentGatewayService) {
        this.agentGatewayService = agentGatewayService;
    }

    @PostMapping
    public Map<String, Object> chat(@Valid @RequestBody AgentChatRequest request) {
        log.info(
                "Agent chat request received: text='{}', userId={}, conversationId={}, metadataKeys={}",
                summarize(request.getText()),
                request.getUserId(),
                request.getConversationId(),
                request.getMetadata() == null ? 0 : request.getMetadata().keySet()
        );
        return agentGatewayService.chat(request);
    }

    private String summarize(String text) {
        if (text == null) {
            return "";
        }
        String trimmed = text.trim();
        return trimmed.length() <= 80 ? trimmed : trimmed.substring(0, 80) + "...";
    }
}
