import { Ticket, hold, resolve, resume } from "./ticket";

function assertEqual(actual: unknown, expected: unknown): void {
  if (actual !== expected) {
    throw new Error(`expected ${String(expected)} but got ${String(actual)}`);
  }
}

function testHoldThenResume(): void {
  const ticket: Ticket = { status: "open" };
  hold(ticket);
  assertEqual(ticket.status, "on_hold");
  resume(ticket);
  assertEqual(ticket.status, "open");
}

function testOnHoldTicketCannotResolveDirectly(): void {
  const ticket: Ticket = { status: "open" };
  hold(ticket);
  let threw = false;
  try {
    resolve(ticket);
  } catch {
    threw = true;
  }
  assertEqual(threw, true);
}

testHoldThenResume();
testOnHoldTicketCannotResolveDirectly();
console.log("ok");
