import { EmailClient } from "./emailClient";
import { EmailQueue } from "./emailQueue";

export class EmailWorker {
  constructor(private queue: EmailQueue, private client: EmailClient) {}

  async processNext(): Promise<boolean> {
    const job = this.queue.dequeue();
    if (!job) return false;
    await this.client.sendWelcomeEmail(job.email, job.name);
    return true;
  }
}
