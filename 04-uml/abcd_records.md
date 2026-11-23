# Exercise 2 - ABCD Records 💿

Statement: https://gist.github.com/bdallard/2d2407c4de4c182afca6d3ec7235e9eb (slide 68) · Code: [`abcd_records.py`](abcd_records.py)

ABCD Records sells CDs and tapes by mail order, at discount prices, to record club members. Rules: only members order, non-members get an application form, Royal members (discount + priority, can order unavailable items) vs Regular members, payment by cash / check / bank draft, an Order Processing Clerk verifies and processes, a Collection Department Clerk handles payments, every order goes into a daily records file.

> **About the use case diagrams:** Mermaid has no real use case diagram, so I draw them as flowcharts: actors are stadium shapes, use cases are circles/ovals, the big box is the **system boundary**, and dotted arrows carry `<<include>>` / `<<extend>>`. `include` points from the base use case to the included one, `extend` points from the optional use case to the base one (like in UML).

## Level 1

### Task 1.1 - simple use case diagram

```mermaid
flowchart LR
    member([Member])
    clerk([Order Processing Clerk])

    subgraph abcd [ABCD Records]
        uc1((Place Order))
        uc2((Verify Membership))
        uc3((Process Order))
        uc4((Make Payment))
    end

    member --- uc1
    member --- uc4
    clerk --- uc2
    clerk --- uc3
```

### Task 1.2 - basic class diagram

```mermaid
classDiagram
    class Member {
        -member_number: str
        -name: str
        -address: str
        -phone: str
        +place_order(lines) Order
        +make_payment(order, amount)
    }
    class Order {
        -order_number: int
        -order_date: date
        -status: str
        -amount: float
        +add_item(title, quantity)
        +total() float
    }
    class OrderProcessingClerk {
        -clerk_id: str
        -name: str
        -desk: str
        +verify_membership(member) bool
        +process_order(order)
        +record_order(order)
    }

    Member "1" --> "0..*" Order : places
    OrderProcessingClerk "1" --> "0..*" Order : processes
    OrderProcessingClerk ..> Member : verifies
```

## Level 2

### Task 2.1 - complete use case diagram

- `<<include>>` = always done as part of the base use case: *Place Order* always verifies the membership and the item availability, *Process Order* always prints the invoice and the shipping list.
- `<<extend>>` = only under a condition: *Apply Discount* and *Order Unavailable Items* extend *Place Order* only for Royal members, *Send Membership Application* extends *Verify Membership* only when the customer is not a member.
- `Royal Member` is a specialization of `Member` (generalization arrow), it can do everything a member does plus the two Royal use cases.

```mermaid
flowchart LR
    nonmember([Non-Member])
    member([Member])
    royal([Royal Member])
    opc([Order Processing Clerk])
    cdc([Collection Department Clerk])

    subgraph abcd [ABCD Records - system boundary]
        place((Place Order))
        verify((Verify Membership))
        avail((Verify Item Availability))
        discount((Apply Discount))
        unavailable((Order Unavailable Items))
        application((Send Membership Application))
        process((Process Order))
        invoice((Print Invoice))
        shipping((Print Shipping List))
        pay((Make Payment))
    end

    royal -->|generalization| member
    member --- place
    member --- pay
    royal --- unavailable
    nonmember --- place
    nonmember --- application
    opc --- verify
    opc --- process
    cdc --- pay

    place -. "&lt;&lt;include&gt;&gt;" .-> verify
    place -. "&lt;&lt;include&gt;&gt;" .-> avail
    process -. "&lt;&lt;include&gt;&gt;" .-> invoice
    process -. "&lt;&lt;include&gt;&gt;" .-> shipping
    discount -. "&lt;&lt;extend&gt;&gt; Royal only" .-> place
    unavailable -. "&lt;&lt;extend&gt;&gt; item out of stock" .-> place
    application -. "&lt;&lt;extend&gt;&gt; not a member" .-> verify
```

### Task 2.2 - complete class diagram

Choices:
- `Customer` is the common parent of `NonMember` and `Member`, because both have a name and an address and a non-member can try to order. `Member` is abstract with two concrete types.
- Each member type answers `discount_rate()` and `can_order_unavailable()` itself (polymorphism, no `if member_type == "royal"`).
- `Order *-- OrderLine` is a composition (a line has no meaning without its order); a line points to one `Item`.
- `LineStatus` says if a line is shipped now (`IN_STOCK`) or later (`BACKORDERED`).

```mermaid
classDiagram
    class Customer {
        <<abstract>>
        #name: str
        #address: str
    }
    class NonMember
    class Member {
        <<abstract>>
        #member_number: str
        #joined_on: date
        +discount_rate()* float
        +can_order_unavailable()* bool
        +has_priority()* bool
    }
    class RoyalMember {
        +discount_rate() 0.15
        +can_order_unavailable() True
        +has_priority() True
    }
    class RegularMember {
        +discount_rate() 0.05
        +can_order_unavailable() False
        +has_priority() False
    }
    class MembershipApplication {
        -applicant: NonMember
        -sent_on: date
        -accepted: bool
    }
    class Item {
        <<abstract>>
        #catalog_number: str
        #title: str
        #artist: str
        #unit_price: float
        #quantity_in_stock: int
        +is_available(quantity) bool
        +reserve(quantity)
        +restock(quantity)
    }
    class CD {
        -number_of_tracks: int
    }
    class Tape {
        -length_minutes: int
    }
    class Order {
        -order_number: int
        -order_date: date
        -status: OrderStatus
        +add_line(item, quantity, status)
        +gross_amount() float
        +discount() float
        +total() float
    }
    class OrderLine {
        -quantity: int
        -status: LineStatus
        +amount() float
    }
    class LineStatus {
        <<enumeration>>
        IN_STOCK
        BACKORDERED
    }
    class Invoice {
        -invoice_number: int
        -amount_due: float
        -paid: bool
        +render() str
    }
    class ShippingList {
        -lines: list~OrderLine~
        -priority: bool
        +render() str
    }
    class Payment {
        <<abstract>>
        #amount: float
        #received_on: date
        +describe()* str
    }
    class Cash
    class Check {
        -check_number: str
        -bank_name: str
    }
    class BankDraft {
        -draft_number: str
        -issuing_bank: str
    }
    class OrderProcessingClerk {
        +verify_membership(customer) bool
        +send_membership_application(customer) MembershipApplication
        +process_order(member, wishlist) tuple
    }
    class CollectionDepartmentClerk {
        +collect(invoice, payment) str
    }
    class DailyRecordsFile {
        -day: date
        -orders: list~Order~
        +record(order)
        +export() str
    }

    Customer <|-- NonMember
    Customer <|-- Member
    Member <|-- RoyalMember
    Member <|-- RegularMember
    Item <|-- CD
    Item <|-- Tape
    Payment <|-- Cash
    Payment <|-- Check
    Payment <|-- BankDraft

    NonMember "1" -- "0..1" MembershipApplication : receives
    Member "1" --> "0..*" Order : places
    Order "1" *-- "1..*" OrderLine : contains
    OrderLine "0..*" --> "1" Item : refers to
    OrderLine --> LineStatus
    Order "1" -- "1" Invoice : billed with
    Order "1" -- "0..1" ShippingList : shipped with
    Invoice "1" -- "0..1" Payment : settled by
    OrderProcessingClerk "1" --> "0..*" Order : processes
    CollectionDepartmentClerk "1" --> "0..*" Payment : collects
    DailyRecordsFile "1" o-- "0..*" Order : records
```

#### Scenario: a Royal member orders 2 CDs, one is unavailable, and pays by check

| Step | Who | What happens in the model |
|---|---|---|
| 1 | Royal member | asks for CD "Thriller" (in stock) and CD "Kind of Blue" (out of stock) |
| 2 | Order clerk | `verify_membership()` → it's a `RoyalMember`, OK |
| 3 | Order clerk | "Thriller" is available → line `IN_STOCK`, stock decreases |
| 4 | Order clerk | "Kind of Blue" is not available, but `can_order_unavailable()` is `True` for Royal → line `BACKORDERED` (a regular member would get nothing for this line) |
| 5 | System | discount 15% on the total, `Invoice` with the amount due, `ShippingList` with only "Thriller", marked priority |
| 6 | Order clerk | the order is written in the `DailyRecordsFile` |
| 7 | Collection clerk | receives a `Check` for the exact amount → invoice paid, order status `PAID` |

This scenario is the `__main__` of `abcd_records.py` and is also a test.

## Level 3 - advanced sequence diagrams

### 1. Complete order processing

```mermaid
sequenceDiagram
    autonumber
    actor M as Member
    actor OPC as Order Processing Clerk
    participant O as :Order
    participant I as :Item
    participant DRF as :DailyRecordsFile
    actor CDC as Collection Dept Clerk

    M->>OPC: order form (items, quantities)
    OPC->>OPC: verify_membership(member)
    OPC->>O: create(member)
    loop each requested item
        OPC->>I: is_available(quantity)
        alt in stock
            OPC->>I: reserve(quantity)
            OPC->>O: add_line(item, qty, IN_STOCK)
        else out of stock and member can backorder
            OPC->>O: add_line(item, qty, BACKORDERED)
        else out of stock
            OPC-->>M: item refused
        end
    end
    OPC->>O: total() with the member discount
    OPC->>OPC: print Invoice and ShippingList
    OPC->>DRF: record(order)
    OPC-->>M: invoice + parcel
    M->>CDC: payment
    CDC->>CDC: collect(invoice, payment)
    CDC-->>M: receipt
```

### 2. Membership verification (success and failure)

```mermaid
sequenceDiagram
    actor C as Customer
    actor OPC as Order Processing Clerk
    participant F as :MembersFile

    C->>OPC: order form
    OPC->>F: find(customer)
    alt customer is a member
        F-->>OPC: member record (Royal or Regular)
        OPC-->>C: order accepted, processing continues
    else customer is not a member
        F-->>OPC: not found
        OPC->>OPC: send_membership_application(customer)
        OPC-->>C: order refused + membership application form
    end
```

### 3. Payment processing (all payment types)

```mermaid
sequenceDiagram
    actor M as Member
    actor CDC as Collection Dept Clerk
    participant Inv as :Invoice
    participant P as :Payment

    M->>CDC: pay(invoice_number, payment)
    CDC->>Inv: amount_due
    Inv-->>CDC: amount
    alt Cash
        CDC->>P: Cash(amount)
    else Check
        CDC->>P: Check(amount, check_number, bank_name)
    else Bank Draft
        CDC->>P: BankDraft(amount, draft_number, issuing_bank)
    end
    CDC->>P: describe()
    alt amount covers the invoice
        CDC->>Inv: mark as paid
        CDC-->>M: receipt
    else amount too low
        CDC-->>M: payment rejected
    end
```

### 4. Item reordering for Royal members

```mermaid
sequenceDiagram
    actor R as Royal Member
    actor OPC as Order Processing Clerk
    participant I as :Item
    participant Q as :ReorderList
    participant S as Supplier

    R->>OPC: order "Kind of Blue" x1
    OPC->>I: is_available(1)
    I-->>OPC: false
    OPC->>OPC: can_order_unavailable(R) = true
    OPC->>Q: add(backordered line)
    OPC-->>R: line BACKORDERED, priority delivery
    Q->>S: purchase order
    S-->>Q: receive_delivery(item, quantity)
    Q->>I: restock(quantity)
    loop waiting lines for this item, oldest first
        Q->>I: reserve(line quantity)
        Q->>Q: line status = IN_STOCK
    end
    Q-->>OPC: lines ready to ship
    OPC-->>R: backordered CD shipped (priority)
```
