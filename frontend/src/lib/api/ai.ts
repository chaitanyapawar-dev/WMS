import { http } from "./client";

export interface AIChatRequest {
  message: string;
  current_route?: string;
  active_warehouse_id?: string;
}

export interface AIChatResponse {
  answer: string;
  tool_calls: string[];
  sources: AISource[];
  request_id: string;
}

export interface AISource {
  title: string;
  source: string;
  section: string;
}

/** POST /v1/ai/chat through the shared authenticated Axios client. */
export async function chat(payload: AIChatRequest): Promise<AIChatResponse> {
  return (await http.post<AIChatResponse>("/ai/chat", payload)).data;
}
