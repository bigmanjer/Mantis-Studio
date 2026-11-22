import "server-only";
import { createCipheriv, createDecipheriv, createHash, randomBytes } from "crypto";

// Encrypts users' own AI keys at rest. Set MANTIS_ENCRYPTION_SECRET to a long random string.
function key(): Buffer {
  const secret = process.env.MANTIS_ENCRYPTION_SECRET;
  if (!secret || secret.length < 32) throw new Error("MANTIS_ENCRYPTION_SECRET must be at least 32 characters");
  return createHash("sha256").update(secret).digest();
}

export function encrypt(plain: string): string {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", key(), iv);
  const data = Buffer.concat([cipher.update(plain, "utf8"), cipher.final()]);
  return [iv, cipher.getAuthTag(), data].map((b) => b.toString("base64")).join(".");
}

export function decrypt(payload: string): string {
  const [iv, tag, data] = payload.split(".").map((p) => Buffer.from(p, "base64"));
  const decipher = createDecipheriv("aes-256-gcm", key(), iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(data), decipher.final()]).toString("utf8");
}

export function maskKey(k: string): string {
  return k.length <= 8 ? "••••" : `${k.slice(0, 4)}••••${k.slice(-4)}`;
}
