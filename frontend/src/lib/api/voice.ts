import { http } from "./client";

export type ReceivingVoiceIntentType = "RECEIVING_QUANTITY" | "UNCLEAR" | "UNSUPPORTED";

export interface ReceivingVoicePreview {
  transcript: string;
  intent: {
    type: ReceivingVoiceIntentType;
    good_qty: number | null;
    damaged_qty: number | null;
  };
  context: {
    receipt_id: string;
    product_id: string;
    product_name: string;
    upc: string;
  };
  requires_confirmation: boolean;
  message: string | null;
  request_id: string;
}

export interface InterpretReceivingVoicePayload {
  audio: Blob;
  receiptId: string;
  upc: string;
}

/** Send a short browser recording to FastAPI for a non-mutating receiving preview. */
export async function interpretReceivingVoice(
  payload: InterpretReceivingVoicePayload,
): Promise<ReceivingVoicePreview> {
  const formData = new FormData();
  formData.append("audio", payload.audio, "receiving-voice.webm");
  formData.append("workflow", "receiving");
  formData.append("receipt_id", payload.receiptId);
  formData.append("upc", payload.upc);

  return (await http.postForm<ReceivingVoicePreview>("/voice/interpret", formData)).data;
}
