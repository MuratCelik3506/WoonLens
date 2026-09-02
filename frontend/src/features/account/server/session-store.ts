import { createCipheriv, createDecipheriv, createHash, randomBytes } from "node:crypto";

import { createClient, type RedisClientType } from "redis";

import { getAccountServerConfig } from "@/lib/config/server-env";

const LOGIN_TTL_SECONDS = 5 * 60;
const MAX_SESSION_TTL_SECONDS = 15 * 60;
const IV_BYTES = 12;
const TAG_BYTES = 16;

export type LoginTransaction = Readonly<{
  codeVerifier: string;
  nonce: string;
  state: string;
  returnTo: string;
}>;

export type AccountSession = Readonly<{
  accessToken: string;
  expiresAt: number;
}>;

let redisClient: RedisClientType | undefined;
let connection: Promise<RedisClientType> | undefined;

async function redis(): Promise<RedisClientType> {
  if (!redisClient) {
    redisClient = createClient({ url: getAccountServerConfig().redisUrl });
    redisClient.on("error", () => undefined);
  }
  if (!redisClient.isOpen) {
    connection ??= redisClient.connect().then(() => redisClient!);
    await connection;
  }
  return redisClient;
}

function storageKey(kind: "login" | "session", handle: string): string {
  const digest = createHash("sha256").update(handle).digest("hex");
  return `woonlens:${kind}:${digest}`;
}

function encryptionKey(): Buffer {
  const key = Buffer.from(getAccountServerConfig().sessionEncryptionKey, "base64");
  if (key.length !== 32) {
    throw new Error("WOONLENS_SESSION_ENCRYPTION_KEY must encode exactly 32 bytes");
  }
  return key;
}

function seal(value: unknown): string {
  const iv = randomBytes(IV_BYTES);
  const cipher = createCipheriv("aes-256-gcm", encryptionKey(), iv);
  const ciphertext = Buffer.concat([
    cipher.update(JSON.stringify(value), "utf8"),
    cipher.final(),
  ]);
  return Buffer.concat([iv, cipher.getAuthTag(), ciphertext]).toString("base64url");
}

function open<T>(value: string): T | null {
  try {
    const payload = Buffer.from(value, "base64url");
    const iv = payload.subarray(0, IV_BYTES);
    const tag = payload.subarray(IV_BYTES, IV_BYTES + TAG_BYTES);
    const ciphertext = payload.subarray(IV_BYTES + TAG_BYTES);
    const decipher = createDecipheriv("aes-256-gcm", encryptionKey(), iv);
    decipher.setAuthTag(tag);
    return JSON.parse(
      Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8"),
    ) as T;
  } catch {
    return null;
  }
}

export function newOpaqueHandle(): string {
  return randomBytes(32).toString("base64url");
}

export async function saveLoginTransaction(
  handle: string,
  transaction: LoginTransaction,
): Promise<void> {
  await (
    await redis()
  ).set(storageKey("login", handle), seal(transaction), {
    EX: LOGIN_TTL_SECONDS,
    NX: true,
  });
}

export async function consumeLoginTransaction(
  handle: string,
): Promise<LoginTransaction | null> {
  const value = await (await redis()).getDel(storageKey("login", handle));
  return value ? open<LoginTransaction>(value) : null;
}

export async function saveAccountSession(
  handle: string,
  accessToken: string,
  expiresIn: number,
): Promise<void> {
  const ttl = Math.max(1, Math.min(expiresIn, MAX_SESSION_TTL_SECONDS));
  const session: AccountSession = {
    accessToken,
    expiresAt: Math.floor(Date.now() / 1000) + ttl,
  };
  await (
    await redis()
  ).set(storageKey("session", handle), seal(session), {
    EX: ttl,
    NX: true,
  });
}

export async function readAccountSession(
  handle: string,
): Promise<AccountSession | null> {
  const value = await (await redis()).get(storageKey("session", handle));
  if (!value) return null;
  const session = open<AccountSession>(value);
  if (!session) {
    await deleteAccountSession(handle);
    return null;
  }
  if (session.expiresAt <= Math.floor(Date.now() / 1000)) {
    await deleteAccountSession(handle);
    return null;
  }
  return session;
}

export async function deleteAccountSession(handle: string): Promise<void> {
  await (await redis()).del(storageKey("session", handle));
}
