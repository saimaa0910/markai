/**
 * @file index.ts
 * @description Top-Level AI Subsystem Exports & Contracts.
 */

export interface AIModelRequest {
  model: string;
  prompt: string;
  temperature?: number;
  maxTokens?: number;
}

export interface AIModelResponse {
  id: string;
  text: string;
  finishReason: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface AIEngineAdapter {
  execute(request: AIModelRequest): Promise<AIModelResponse>;
}
