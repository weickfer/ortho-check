package com.orthoaudit.analyzer.config;

import com.bedatadriven.jackson.datatype.jts.JtsModule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Registra o módulo JTS no ObjectMapper do Jackson para
 * serializar/deserializar geometrias JTS como GeoJSON.
 */
@Configuration
public class JacksonConfig {

    @Bean
    public JtsModule jtsModule() {
        return new JtsModule();
    }
}
