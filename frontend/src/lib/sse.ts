// backend의 SSE 포맷(app/api/routes/debate.py: `event: ...\ndata: ...\n\n`)을 파싱한다.
// 브라우저 EventSource는 POST 바디를 못 보내서 fetch + ReadableStream을 직접 읽는다.

export interface SSEEvent {
  event: string;
  data: string;
}

export async function* streamSSE(
  url: string,
  init: RequestInit,
): AsyncGenerator<SSEEvent> {
  const res = await fetch(url, init);

  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `요청 실패 (HTTP ${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sepIndex: number;
    while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);
      const parsed = parseEventBlock(rawEvent);
      if (parsed) yield parsed;
    }
  }
}

function parseEventBlock(block: string): SSEEvent | null {
  let event = "message";
  const dataLines: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (dataLines.length === 0) return null;
  return { event, data: dataLines.join("\n") };
}
