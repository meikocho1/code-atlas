export interface WelcomeEmailJob {
  email: string;
  name: string;
}

export class EmailQueue {
  private jobs: WelcomeEmailJob[] = [];

  enqueue(job: WelcomeEmailJob): void {
    this.jobs.push(job);
  }

  dequeue(): WelcomeEmailJob | undefined {
    return this.jobs.shift();
  }
}
