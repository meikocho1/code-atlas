// Represents a client for an external SMTP provider.
export class EmailClient {
  async sendWelcomeEmail(email: string, name: string): Promise<void> {
    throw new Error("not implemented");
  }
}
