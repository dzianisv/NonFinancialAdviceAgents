#!/usr/bin/env bun
/**
 * fetch_nostr.ts — Lyn Alden Nostr fetcher.
 *
 * Queries multiple public relays via Bun's native WebSocket for kind:1 notes
 * and kind:6 reposts authored by Lyn's pubkey, dedupes by event id, filters to
 * a --days window. Never crashes — degrades to a loud [UNAVAILABLE] line.
 */

const PUBKEY = "eab0e756d32b80bcd464f3d844b8040303075a13eabc3599a762c9ac7ab91f4f";
const RELAYS = ["wss://relay.primal.net", "wss://relay.damus.io", "wss://nos.lol"];
const TIMEOUT_MS = 15_000;

export interface NostrNote {
  kind: "note" | "repost";
  text: string;
  date: string; // ISO
  id: string;
  reposted_from?: string;
}

interface NostrEvent {
  id: string;
  pubkey: string;
  created_at: number;
  kind: number;
  content: string;
  tags: string[][];
}

function queryRelay(url: string, filter: any, timeoutMs: number): Promise<NostrEvent[]> {
  return new Promise((resolve) => {
    const events: NostrEvent[] = [];
    let settled = false;
    let ws: WebSocket;

    const finish = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      try {
        ws.send(JSON.stringify(["CLOSE", "sub1"]));
      } catch {}
      try {
        ws.close();
      } catch {}
      resolve(events);
    };

    const timer = setTimeout(finish, timeoutMs);

    try {
      ws = new WebSocket(url);
    } catch {
      clearTimeout(timer);
      resolve(events);
      return;
    }

    ws.onopen = () => {
      try {
        ws.send(JSON.stringify(["REQ", "sub1", filter]));
      } catch {
        finish();
      }
    };
    ws.onmessage = (msg: MessageEvent) => {
      try {
        const data = JSON.parse(String(msg.data));
        if (data[0] === "EVENT" && data[1] === "sub1" && data[2]) {
          events.push(data[2] as NostrEvent);
        } else if (data[0] === "EOSE" && data[1] === "sub1") {
          finish();
        }
      } catch {
        /* ignore malformed frames */
      }
    };
    ws.onerror = () => finish();
    ws.onclose = () => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        resolve(events);
      }
    };
  });
}

function tagValue(tags: string[][], name: string): string | undefined {
  const t = tags?.find((x) => x[0] === name);
  return t?.[1];
}

function toNote(ev: NostrEvent): NostrNote {
  if (ev.kind === 6) {
    let text = "";
    let reposted_from: string | undefined;
    if (ev.content && ev.content.trim()) {
      try {
        const inner = JSON.parse(ev.content);
        text = (inner.content ?? "").trim();
        reposted_from = inner.pubkey;
      } catch {
        text = ev.content.trim();
      }
    }
    if (!reposted_from) reposted_from = tagValue(ev.tags, "p");
    if (!text) {
      const eid = tagValue(ev.tags, "e");
      text = eid ? `[repost of event ${eid}]` : "[repost]";
    }
    return {
      kind: "repost",
      text,
      date: new Date(ev.created_at * 1000).toISOString(),
      id: ev.id,
      ...(reposted_from ? { reposted_from } : {}),
    };
  }
  return {
    kind: "note",
    text: (ev.content ?? "").trim(),
    date: new Date(ev.created_at * 1000).toISOString(),
    id: ev.id,
  };
}

export async function fetchNostr(days: number): Promise<NostrNote[]> {
  const since = Math.floor((Date.now() - days * 86_400_000) / 1000);
  const filter = { authors: [PUBKEY], kinds: [1, 6], since, limit: 200 };

  const results = await Promise.allSettled(
    RELAYS.map((r) => queryRelay(r, filter, TIMEOUT_MS))
  );

  const byId = new Map<string, NostrEvent>();
  for (const r of results) {
    if (r.status === "fulfilled") {
      for (const ev of r.value) {
        if (ev?.id && ev.created_at >= since) byId.set(ev.id, ev);
      }
    }
  }

  const notes = [...byId.values()]
    .map(toNote)
    .sort((a, b) => Date.parse(b.date) - Date.parse(a.date));
  return notes;
}

function parseArgs(argv: string[]) {
  const days = argv.includes("--days")
    ? parseInt(argv[argv.indexOf("--days") + 1] ?? "30", 10) || 30
    : 30;
  return { days, json: argv.includes("--json") };
}

if (import.meta.main) {
  const { days, json } = parseArgs(process.argv.slice(2));
  try {
    const notes = await fetchNostr(days);
    if (notes.length === 0) {
      console.log(
        `[UNAVAILABLE] Nostr relays returned no events for Lyn within ${days}d window`
      );
      process.exit(0);
    }
    if (json) {
      console.log(JSON.stringify(notes, null, 2));
    } else {
      for (const n of notes) {
        const d = n.date.slice(0, 10);
        const from = n.reposted_from ? ` from:${n.reposted_from.slice(0, 12)}…` : "";
        const snippet = n.text.replace(/\s+/g, " ").slice(0, 200);
        console.log(`${d} [${n.kind}${from}] ${snippet} — https://primal.net/e/${n.id}`);
      }
    }
  } catch (e: any) {
    console.log(`[UNAVAILABLE] Nostr fetch failed across all relays — ${e?.message ?? e}`);
    process.exit(0);
  }
}
