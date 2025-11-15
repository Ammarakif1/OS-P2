
#Bank simulation with threaded tellers and customers

import argparse
import random
import time
from dataclasses import dataclass
from queue import Queue
from threading import Thread, Semaphore, Lock, Event


MS = 1e-3


def ms_sleep(ms: int) -> None:
    time.sleep(ms * MS)


def log(thread_type: str, tid: int, counterpart: str, msg: str) -> None:
    print(f"{thread_type} {tid} [{counterpart}]: {msg}")


@dataclass
class TellerSync:
    customer_arrived: Semaphore
    ask_txn: Semaphore
    txn_given: Semaphore
    txn_done: Semaphore
    customer_left: Semaphore


class Shared:
    def __init__(self, num_tellers: int, total_customers: int):
        
        self.num_tellers = num_tellers
        self.total_customers = total_customers
        # Opening n closing coordination
        self.bank_open = Event()
        self.ready_count_lock = Lock()
        self.ready_count = 0
        self.tellers = []
        self.finished_lock = Lock()
        self.customers_finished = 0

        # Resource semaphores
        self.door_sem = Semaphore(2)
        self.manager_sem = Semaphore(1)
        self.safe_sem = Semaphore(2)
        # Queuetellers and customers
        self.line_lock = Lock()
        self.line_q: "Queue[tuple[int, Semaphore]]" = Queue()
        self.ready_tellers_q: "Queue[int]" = Queue()
        #  teller rv semaphores
        self.teller_sync: list[TellerSync] = [
            TellerSync(
                customer_arrived=Semaphore(0),
                ask_txn=Semaphore(0),
                txn_given=Semaphore(0),
                txn_done=Semaphore(0),
                customer_left=Semaphore(0),
            )
            for _ in range(num_tellers)
        ]


class Teller(Thread):
    def __init__(self, tid: int, shared: Shared):
        super().__init__(name=f"Teller-{tid}")
        self.tid = tid
        self.shared = shared
        self.current_customer: int | None = None

    def announce_ready(self) -> None:
        # Consoleloging readiness and help open the bank
        log("Teller", self.tid, "—", "ready to serve")
        with self.shared.ready_count_lock:
            self.shared.ready_count += 1
            if self.shared.ready_count == self.shared.num_tellers:
                log("Teller", self.tid, "—", "bank is now open")
                self.shared.bank_open.set()
        self.shared.ready_tellers_q.put(self.tid)
        self.call_next_from_line_if_any()

    def call_next_from_line_if_any(self) -> None:
        # Ping a waiting customer if one is queued
        try:
            if self.shared.line_q.qsize() > 0:
                cust_id, cust_sem = self.shared.line_q.get_nowait()
                log("Teller", self.tid, f"Customer {cust_id}", "calls from line")
                cust_sem.release()
        except Exception:
            pass

    def run(self) -> None:
        #  Wait for customers and process transactions
        self.announce_ready()
        sync = self.shared.teller_sync[self.tid]
        while True:
            sync.customer_arrived.acquire()
            cust_id = self.current_customer
            if cust_id is None:
                continue
            if cust_id == -1:
                return
            log("Teller", self.tid, f"Customer {cust_id}", "asks for transaction")
            sync.ask_txn.release()
            sync.txn_given.acquire()
            action = getattr(self, "requested_action", "Deposit")
            if action == "Withdraw":
                log("Teller", self.tid, "Manager", "going to manager")
                self.shared.manager_sem.acquire()
                log("Teller", self.tid, "Manager", "using manager")
                wait_ms = random.randint(5, 30)
                log("Teller", self.tid, "Manager", f"interaction {wait_ms}ms start")
                ms_sleep(wait_ms)
                log("Teller", self.tid, "Manager", "interaction done")
                self.shared.manager_sem.release()
                log("Teller", self.tid, "Manager", "done with manager")
            log("Teller", self.tid, "Safe", "going to safe")
            self.shared.safe_sem.acquire()
            log("Teller", self.tid, "Safe", "using safe")
            wait_ms = random.randint(10, 50)
            log("Teller", self.tid, "Safe", f"transaction {wait_ms}ms start")
            ms_sleep(wait_ms)
            log("Teller", self.tid, "Safe", "transaction done")
            self.shared.safe_sem.release()
            log("Teller", self.tid, "Safe", "done with safe")
            log("Teller", self.tid, f"Customer {cust_id}", "completes transaction")
            sync.txn_done.release()
            with self.shared.finished_lock:
                self.shared.customers_finished += 1
                all_done = self.shared.customers_finished >= self.shared.total_customers
            if all_done:
                log("Teller", self.tid, "—", "closing teller")
                return
            self.current_customer = None
            self.announce_ready()


class Customer(Thread):
    def __init__(self, cid: int, shared: Shared):
        super().__init__(name=f"Customer-{cid}")
        self.cid = cid
        self.shared = shared
        self.transaction = random.choice(["Deposit", "Withdraw"])
        self.called_sem = Semaphore(0)

    def run(self) -> None:
        #  arrive n interact with teller n exit
        arrival_ms = random.randint(0, 100)
        log("Customer", self.cid, "—", f"arrival wait {arrival_ms}ms start")
        ms_sleep(arrival_ms)
        log("Customer", self.cid, "—", "arrival wait done")
        self.shared.bank_open.wait()
        log("Customer", self.cid, "Door", "entering")
        self.shared.door_sem.acquire()
        log("Customer", self.cid, "Door", "entered")
        self.shared.door_sem.release()
        teller_id = self.select_or_enqueue()
        log("Customer", self.cid, f"Teller {teller_id}", "introduces self")
        sync = self.shared.teller_sync[teller_id]
        teller_thread: "Teller" = self.shared.tellers[teller_id]
        teller_thread.current_customer = self.cid
        sync.customer_arrived.release()
        sync.ask_txn.acquire()
        log("Customer", self.cid, f"Teller {teller_id}", f"tells transaction {self.transaction}")
        teller_thread.requested_action = self.transaction
        sync.txn_given.release()
        sync.txn_done.acquire()
        log("Customer", self.cid, f"Teller {teller_id}", "transaction complete acknowledged")
        log("Customer", self.cid, "Door", "leaving")
        self.shared.door_sem.acquire()
        log("Customer", self.cid, "Door", "left")
        self.shared.door_sem.release()
        sync.customer_left.release()

    def select_or_enqueue(self) -> int:
        # Choose a ready teller or wait in line
        teller_id: int | None = None
        try:
            teller_id = self.shared.ready_tellers_q.get_nowait()
            log("Customer", self.cid, f"Teller {teller_id}", "selects teller")
        except Exception:
            teller_id = None
        if teller_id is not None:
            return teller_id
        with self.shared.line_lock:
            self.shared.line_q.put((self.cid, self.called_sem))
            log("Customer", self.cid, "—", "waits in line")
        self.called_sem.acquire()
        teller_id = self.shared.ready_tellers_q.get()
        log("Customer", self.cid, f"Teller {teller_id}", "goes to called teller")
        return teller_id


def run_simulation(num_customers: int = 50, num_tellers: int = 3, seed: int | None = None) -> None:
   
    if seed is not None:
        random.seed(seed)
    shared = Shared(num_tellers=num_tellers, total_customers=num_customers)
    tellers = [Teller(tid=i, shared=shared) for i in range(num_tellers)]
    shared.tellers = tellers
    for t in tellers:
        t.start()
    shared.bank_open.wait()
    customers = [Customer(cid=i + 1, shared=shared) for i in range(num_customers)]
    for c in customers:
        c.start()
    for c in customers:
        c.join()
    for t in tellers:
        if t.is_alive() and t.current_customer is None:
            t.current_customer = -1
            shared.teller_sync[t.tid].customer_arrived.release()
    for t in tellers:
        t.join()
    print("Simulation complete.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=50)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    run_simulation(num_customers=args.customers, seed=args.seed)


if __name__ == "__main__":
    main()

