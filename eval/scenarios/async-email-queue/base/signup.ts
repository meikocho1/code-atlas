import { EmailClient } from "./emailClient";

const emailClient = new EmailClient();

export interface SignupRequest {
  email: string;
  name: string;
}

export async function signup(request: SignupRequest): Promise<{ id: string }> {
  const id = crypto.randomUUID();
  await emailClient.sendWelcomeEmail(request.email, request.name);
  return { id };
}
