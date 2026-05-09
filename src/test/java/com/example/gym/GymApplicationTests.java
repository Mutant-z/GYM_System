package com.example.gym;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = "frontend.dev-server.enabled=false")
class GymApplicationTests {

    @Test
    void contextLoads() {
    }

}
