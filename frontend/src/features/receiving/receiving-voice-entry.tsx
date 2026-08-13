import { Mic, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { type ReceivingVoicePreview, interpretReceivingVoice } from "@/lib/api/voice";
import { errorMessage } from "@/lib/api/client";

const MAX_RECORDING_MS = 12_000;

interface ReceivingVoiceEntryProps {
  receiptId: string;
  upc: string;
  onPreview: (preview: ReceivingVoicePreview) => void;
}

/** Capture one short receiving quantity recording and request a read-only preview. */
export function ReceivingVoiceEntry({ receiptId, upc, onPreview }: ReceivingVoiceEntryProps) {
  const [state, setState] = useState<"idle" | "requesting" | "recording" | "processing">("idle");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      recorderRef.current?.state === "recording" && recorderRef.current.stop();
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const releaseMicrophone = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  };

  const stopRecording = () => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  };

  const startRecording = async () => {
    if (!upc.trim()) {
      toast.error("Scan or enter a registered product UPC before using voice entry.");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      toast.error("Voice entry is not supported by this browser. You can still enter quantities manually.");
      return;
    }

    setState("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        const audio = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        releaseMicrophone();
        recorderRef.current = null;
        if (audio.size === 0) {
          setState("idle");
          toast.error("No audio was captured. Please try recording again.");
          return;
        }
        setState("processing");
        try {
          const preview = await interpretReceivingVoice({ audio, receiptId, upc: upc.trim() });
          onPreview(preview);
          if (!preview.requires_confirmation) {
            toast.error(preview.message || "I couldn't determine the quantities. Please enter them manually.");
          }
        } catch (error) {
          toast.error(errorMessage(error));
        } finally {
          setState("idle");
        }
      };
      recorder.start();
      setState("recording");
      timeoutRef.current = setTimeout(() => {
        toast.message("Voice recording stopped after 12 seconds.");
        stopRecording();
      }, MAX_RECORDING_MS);
    } catch {
      releaseMicrophone();
      setState("idle");
      toast.error("Microphone access is required for voice entry. You can still enter quantities manually.");
    }
  };

  if (state === "recording") {
    return (
      <Button type="button" variant="destructive" size="sm" onClick={stopRecording} className="h-9 rounded-lg">
        <Square /> Stop recording
      </Button>
    );
  }

  const processing = state === "requesting" || state === "processing";
  return (
    <Button type="button" variant="outline" size="sm" disabled={processing} onClick={startRecording} className="h-9 rounded-lg">
      <Mic /> {state === "processing" ? "Processing..." : state === "requesting" ? "Requesting microphone..." : "Voice entry"}
    </Button>
  );
}
