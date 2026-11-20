export function triageMaternal(
  reading: Record<string, unknown>,
  signs: string[],
  context: Record<string, unknown>,
): { level: string; rule_ids: string[]; reasons: string[]; rules_version: string };

export function renderSms(level: string): string;

export function checksum(body: string): string;

export function encodeSms(
  deviceId: string,
  seq: number,
  reading: Record<string, unknown>,
  signs: string[],
): string;
