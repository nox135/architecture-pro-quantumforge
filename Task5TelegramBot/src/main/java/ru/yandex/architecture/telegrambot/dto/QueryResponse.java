package ru.yandex.architecture.telegrambot.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
public class QueryResponse {
    @JsonProperty("answer")
    private String answer;
    
    @JsonProperty("reasoning")
    private String reasoning;
    
    @JsonProperty("chunks_count")
    private Integer chunksCount;
    
    @JsonProperty("chunks")
    private List<ChunkInfo> chunks;
    
    @Data
    public static class ChunkInfo {
        @JsonProperty("text")
        private String text;
        
        @JsonProperty("source")
        private String source;
        
        @JsonProperty("distance")
        private Double distance;
    }
}

