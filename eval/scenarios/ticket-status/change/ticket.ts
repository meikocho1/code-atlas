export type TicketStatus = "open" | "on_hold" | "resolved" | "closed";

export interface Ticket {
  status: TicketStatus;
}

export function hold(ticket: Ticket): void {
  if (ticket.status !== "open") {
    throw new Error("only open tickets can be put on hold");
  }
  ticket.status = "on_hold";
}

export function resume(ticket: Ticket): void {
  if (ticket.status !== "on_hold") {
    throw new Error("only on-hold tickets can resume");
  }
  ticket.status = "open";
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
