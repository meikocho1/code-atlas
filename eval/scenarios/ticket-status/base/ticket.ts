export type TicketStatus = "open" | "resolved" | "closed";

export interface Ticket {
  status: TicketStatus;
}

export function resolve(ticket: Ticket): void {
  if (ticket.status !== "open") {
    throw new Error("only open tickets can be resolved");
  }
  ticket.status = "resolved";
}

export function close(ticket: Ticket): void {
  if (ticket.status !== "resolved") {
    throw new Error("only resolved tickets can be closed");
  }
  ticket.status = "closed";
}
