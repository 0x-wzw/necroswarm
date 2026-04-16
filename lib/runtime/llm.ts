import OpenAI from "openai";

const DEFAULT_MAX_OUTPUT_TOKENS = 512;

export interface LLMRequest {
  model: string;
  system: string;
  prompt: string;
  maxOutputTokens?: number;
  temperature?: number;
}

export interface LLMResponse {
  content: string;
  model: string;
  usage: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
}

let client: OpenAI | null = null;

function getClient(): OpenAI | null {
  if (!process.env.OPENAI_API_KEY) {
    return null;
  }

  if (!client) {
    client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  }

  return client;
}

function toOpenAIModel(model: string): string {
  const [provider, name] = model.split(":");
  if (provider !== "openai" || !name) {
    throw new Error(`Unsupported model provider in ${model}`);
  }
  return name;
}

export async function callLLM(request: LLMRequest): Promise<LLMResponse> {
  const safeMaxOutput = Math.max(32, Math.min(request.maxOutputTokens ?? DEFAULT_MAX_OUTPUT_TOKENS, 8000));
  const apiModel = toOpenAIModel(request.model);
  const openai = getClient();

  if (!openai) {
    const simulatedText = `Simulated response for ${request.model}: ${request.prompt.slice(0, 120)}`;
    const inputTokens = Math.ceil((request.system.length + request.prompt.length) / 4);
    const outputTokens = Math.min(safeMaxOutput, Math.ceil(simulatedText.length / 4));
    return {
      content: simulatedText,
      model: request.model,
      usage: {
        input_tokens: inputTokens,
        output_tokens: outputTokens,
        total_tokens: inputTokens + outputTokens
      }
    };
  }

  const response = await openai.chat.completions.create({
    model: apiModel,
    messages: [
      { role: "system", content: request.system },
      { role: "user", content: request.prompt }
    ],
    max_tokens: safeMaxOutput,
    temperature: request.temperature ?? 0.2
  });

  const content = response.choices[0]?.message?.content ?? "";
  const inputTokens = response.usage?.prompt_tokens ?? 0;
  const outputTokens = response.usage?.completion_tokens ?? 0;

  return {
    content,
    model: request.model,
    usage: {
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      total_tokens: (response.usage?.total_tokens ?? inputTokens + outputTokens)
    }
  };
}
