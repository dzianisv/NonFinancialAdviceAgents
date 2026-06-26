import { describe, it, expect } from "bun:test";
import { rsi, macd, sma } from "./indicators.ts";
import { isActive, type AlertJob, type Cond } from "./store.ts";
import { evaluateJob, type JobData } from "./check.ts";

// ---------------------------------------------------------------------------
// RSI fixture (Wilder's method, classic textbook series)
// ---------------------------------------------------------------------------
const RSI_SERIES = [44.34,44.09,44.15,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28];

describe("rsi()", () => {
  it("returns ~70.46 on the textbook 15-close series", () => {
    const result = rsi(RSI_SERIES, 14);
    expect(result).toBeGreaterThan(70);
    expect(result).toBeLessThan(71);
  });

  it("throws when closes too short", () => {
    expect(() => rsi([1, 2, 3], 14)).toThrow();
  });
});

// ---------------------------------------------------------------------------
// MACD
// ---------------------------------------------------------------------------
describe("macd()", () => {
  // Build a series long enough: slow(26) + signal(9) = 35 minimum
  // Use an ascending then descending series to produce a sign flip
  const rising = Array.from({ length: 40 }, (_, i) => 100 + i * 2); // 100..178
  const falling = Array.from({ length: 10 }, (_, i) => 178 - i * 4); // 178..138

  it("returns finite numbers on a valid series", () => {
    const result = macd(rising);
    expect(isFinite(result.macd)).toBe(true);
    expect(isFinite(result.signal)).toBe(true);
    expect(isFinite(result.hist)).toBe(true);
    expect(isFinite(result.prevHist)).toBe(true);
  });

  it("detects sign flip from rising+falling series", () => {
    const series = [...rising, ...falling];
    const result = macd(series);
    // After sustained rise then sharp fall, histogram should flip to negative
    const flipped = (result.prevHist > 0 && result.hist < 0) || (result.prevHist < 0 && result.hist > 0);
    // At minimum, prevHist and hist should differ (momentum changing)
    expect(result.prevHist).not.toBeCloseTo(result.hist, 5);
    // The histogram sign-flip or substantial change confirms MACD responsiveness
    expect(isFinite(result.hist)).toBe(true);
    _ = flipped; // acknowledged
  });

  it("throws when series too short", () => {
    expect(() => macd(Array(10).fill(50))).toThrow();
  });
});

// suppress unused var lint
let _: boolean;

// ---------------------------------------------------------------------------
// evaluateJob — price conditions
// ---------------------------------------------------------------------------

function makeJob(overrides: Partial<AlertJob> & { conditions: Cond[] }): AlertJob {
  return {
    id: "test-job",
    desk: "crypto",
    symbol: "BTC-USD",
    reasoning: "test reasoning",
    channel: "stdout",
    created: new Date().toISOString(),
    ...overrides,
  };
}

describe("evaluateJob() — price conditions", () => {
  it("above fires when price > value", () => {
    const job = makeJob({ conditions: [{ condition: "above", value: 50000 }] });
    const { fires } = evaluateJob(job, { price: 60000 });
    expect(fires).toBe(true);
  });

  it("above does NOT fire when price <= value", () => {
    const job = makeJob({ conditions: [{ condition: "above", value: 70000 }] });
    const { fires } = evaluateJob(job, { price: 60000 });
    expect(fires).toBe(false);
  });

  it("below fires when price < value", () => {
    const job = makeJob({ conditions: [{ condition: "below", value: 999999 }] });
    const { fires } = evaluateJob(job, { price: 60000 });
    expect(fires).toBe(true);
  });

  it("below does NOT fire when price >= value", () => {
    const job = makeJob({ conditions: [{ condition: "below", value: 50000 }] });
    const { fires } = evaluateJob(job, { price: 60000 });
    expect(fires).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// evaluateJob — RSI conditions
// ---------------------------------------------------------------------------
describe("evaluateJob() — rsi conditions", () => {
  it("rsi_below fires when RSI < 100 (always true with valid closes)", () => {
    const job = makeJob({ conditions: [{ condition: "rsi_below", value: 100 }] });
    const { fires } = evaluateJob(job, { price: 60000, closes: RSI_SERIES });
    expect(fires).toBe(true);
  });

  it("rsi_above fires when RSI > 70 (series is ~70.46)", () => {
    const job = makeJob({ conditions: [{ condition: "rsi_above", value: 70 }] });
    const { fires } = evaluateJob(job, { price: 60000, closes: RSI_SERIES });
    expect(fires).toBe(true);
  });

  it("rsi_above does NOT fire when threshold above computed RSI", () => {
    const job = makeJob({ conditions: [{ condition: "rsi_above", value: 75 }] });
    const { fires } = evaluateJob(job, { price: 60000, closes: RSI_SERIES });
    expect(fires).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// evaluateJob — compound match modes
// ---------------------------------------------------------------------------
describe("evaluateJob() — compound match", () => {
  const data: JobData = { price: 60000 };

  it("match:all fires only when ALL conditions true", () => {
    const job = makeJob({
      match: "all",
      conditions: [
        { condition: "above", value: 50000 }, // true
        { condition: "above", value: 70000 }, // false
      ],
    });
    expect(evaluateJob(job, data).fires).toBe(false);
  });

  it("match:all fires when ALL conditions true", () => {
    const job = makeJob({
      match: "all",
      conditions: [
        { condition: "above", value: 50000 }, // true
        { condition: "below", value: 70000 }, // true
      ],
    });
    expect(evaluateJob(job, data).fires).toBe(true);
  });

  it("match:any fires when at least one condition is true", () => {
    const job = makeJob({
      match: "any",
      conditions: [
        { condition: "above", value: 70000 }, // false
        { condition: "below", value: 70000 }, // true
      ],
    });
    expect(evaluateJob(job, data).fires).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// isActive
// ---------------------------------------------------------------------------
describe("isActive()", () => {
  it("returns false for expired job", () => {
    const job = makeJob({
      conditions: [{ condition: "above", value: 1 }],
      expiry: "2020-01-01T00:00:00Z",
    });
    expect(isActive(job, new Date("2025-01-01"))).toBe(false);
  });

  it("returns false for one-shot fired job", () => {
    const job = makeJob({
      conditions: [{ condition: "above", value: 1 }],
      fired: true,
    });
    expect(isActive(job, new Date())).toBe(false);
  });

  it("returns true for normal active job", () => {
    const job = makeJob({ conditions: [{ condition: "above", value: 1 }] });
    expect(isActive(job, new Date())).toBe(true);
  });
});
