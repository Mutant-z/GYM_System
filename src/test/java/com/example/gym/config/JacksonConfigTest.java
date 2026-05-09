package com.example.gym.config;

import com.example.gym.gym.dto.CreateGymBookingDTO;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.http.converter.json.Jackson2ObjectMapperBuilder;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

class JacksonConfigTest {

    private final ObjectMapper objectMapper = buildObjectMapper();

    @Test
    void shouldDeserializeBookingDateTimeWithSpaceSeparator() throws Exception {
        CreateGymBookingDTO dto = objectMapper.readValue("""
                {
                  "gymRoomId": 1,
                  "startTime": "2026-04-16 15:00:00",
                  "endTime": "2026-04-16 16:00:00",
                  "headCount": 1
                }
                """, CreateGymBookingDTO.class);

        assertThat(dto.getStartTime()).isEqualTo(LocalDateTime.of(2026, 4, 16, 15, 0));
        assertThat(dto.getEndTime()).isEqualTo(LocalDateTime.of(2026, 4, 16, 16, 0));
    }

    @Test
    void shouldKeepDeserializingIsoBookingDateTime() throws Exception {
        CreateGymBookingDTO dto = objectMapper.readValue("""
                {
                  "gymRoomId": 1,
                  "startTime": "2026-04-16T15:00:00",
                  "endTime": "2026-04-16T16:00:00",
                  "headCount": 1
                }
                """, CreateGymBookingDTO.class);

        assertThat(dto.getStartTime()).isEqualTo(LocalDateTime.of(2026, 4, 16, 15, 0));
        assertThat(dto.getEndTime()).isEqualTo(LocalDateTime.of(2026, 4, 16, 16, 0));
    }

    private static ObjectMapper buildObjectMapper() {
        Jackson2ObjectMapperBuilder builder = new Jackson2ObjectMapperBuilder();
        new JacksonConfig().jackson2ObjectMapperBuilderCustomizer().customize(builder);
        return builder.build();
    }
}
