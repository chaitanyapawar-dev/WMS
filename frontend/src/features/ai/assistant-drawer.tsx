import { useMutation } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { aiApi } from "@/lib/api";
import { errorMessage, normalizeError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { useWarehouseScope } from "@/lib/warehouse-scope";
import type { Role } from "@/types";

const SUGGESTIONS: Record<Role, string[]> = {
  OWNER: ["What needs attention across Whitfield?", "Compare Reno and Columbus inventory.", "Show open orders.", "What changed recently?"],
  MANAGER: ["What needs attention in Reno?", "Show pending receipts.", "Show damaged inventory.", "Which orders are ready to ship?"],
  RECEIVING_STAFF: ["Show my pending receipts.", "What product has UPC 194253397168?", "How much Widget A is available?", "Show open receiving work."],
  FULFILLMENT_STAFF: ["Which orders are waiting to be picked?", "Which orders are ready to ship?", "Show order ORD-1011.", "How much Widget A is available?"],
};

interface ConversationItem {
  question: string;
  answer: string;
  tools: string[];
}

/** Render the authenticated, read-only Whitfield AI chat drawer. */
export function AssistantDrawer() {
  const { user } = useAuth();
  const { scopeId } = useWarehouseScope();
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState<ConversationItem[]>([]);
  const suggestions = useMemo(() => (user ? SUGGESTIONS[user.role] : []), [user]);

  const chat = useMutation({
    mutationFn: (question: string) => aiApi.chat({ message: question, active_warehouse_id: scopeId === "ALL" ? undefined : scopeId }),
    onSuccess: (response, question) => {
      setConversation((items) => [...items, { question, answer: response.answer, tools: response.tool_calls }]);
      setMessage("");
    },
    onError: (error) => {
      const normalized = normalizeError(error);
      const message = normalized.status === 503
        ? "I couldn't reach the AI service right now. The warehouse system is still available."
        : errorMessage(error);
      toast.error(message);
    },
  });

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    const question = message.trim();
    if (!question || chat.isPending) return;
    chat.mutate(question);
  };

  if (!user) return null;

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="h-9 gap-1.5 rounded-xl border-primary/30 bg-primary/5 text-primary hover:bg-primary/10">
          <Sparkles className="size-3.5" aria-hidden />
          <span className="hidden sm:inline">Ask Whitfield</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="flex w-full flex-col border-primary/20 bg-background/95 p-0 sm:max-w-md">
        <SheetHeader className="border-b border-border px-6 py-5">
          <SheetTitle className="flex items-center gap-2"><Sparkles className="size-5 text-primary" aria-hidden />Whitfield Assistant</SheetTitle>
          <SheetDescription>Read-only answers grounded in live warehouse data.</SheetDescription>
        </SheetHeader>
        <ScrollArea className="min-h-0 flex-1 px-6 py-5">
          {conversation.length === 0 ? (
            <div className="space-y-3">
              <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Suggested prompts</p>
              <div className="grid gap-2">
                {suggestions.map((suggestion) => (
                  <button key={suggestion} type="button" onClick={() => setMessage(suggestion)} className="rounded-lg border border-border bg-surface-elevated px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground">
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              {conversation.map((item, index) => (
                <div key={`${item.question}-${index}`} className="space-y-2">
                  <div className="ml-8 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">{item.question}</div>
                  <div className="mr-4 rounded-lg border border-border bg-surface-elevated px-3 py-2 text-sm leading-6 whitespace-pre-wrap">{item.answer}</div>
                  {item.tools.length > 0 && <p className="text-xs text-muted-foreground">Live data: {item.tools.join(", ")}</p>}
                </div>
              ))}
              {chat.isPending && <div className="mr-4 rounded-lg border border-border bg-surface-elevated px-3 py-2 text-sm text-muted-foreground">Checking live warehouse data...</div>}
            </div>
          )}
        </ScrollArea>
        <form onSubmit={submit} className="border-t border-border p-4">
          <div className="flex gap-2">
            <input value={message} onChange={(event) => setMessage(event.target.value)} maxLength={2000} placeholder="Ask about your warehouse..." aria-label="Ask Whitfield" className="h-10 min-w-0 flex-1 rounded-xl border border-input bg-transparent px-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring" disabled={chat.isPending} />
            <Button type="submit" disabled={!message.trim() || chat.isPending} className="h-10 rounded-xl">Send</Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
