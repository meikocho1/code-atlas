import { EmailQueue } from "./emailQueue";

export const emailQueue = new EmailQueue();

export interface SignupRequest {
  email: string;
  name: string;
}

export async function signup(request: SignupRequest): Promise<{ id: string }> {
  const id = crypto.randomUUID();
  emailQueue.enqueue({ email: request.email, name: request.name });
  return { id };
}
