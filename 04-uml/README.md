# 04 - UML exercises

Statement: https://gist.github.com/bdallard/2d2407c4de4c182afca6d3ec7235e9eb (slide 68)

All diagrams are written in **Mermaid**, so GitHub draws them directly in the `.md` files. For each exercise I also translated the final class diagram into Python, to check that the model actually works.

| Exercise | Diagrams + answers | Code |
|---|---|---|
| 1 - Hospital management system (tasks 1, 2, 3 + the 4 questions) | [`hospital.md`](hospital.md) | [`hospital.py`](hospital.py) |
| 2 - ABCD Records (levels 1, 2, 3) | [`abcd_records.md`](abcd_records.md) | [`abcd_records.py`](abcd_records.py) |

```bash
python3 hospital.py
python3 abcd_records.py
python3 -m pytest        # test_uml.py: 19 tests
```

## UML reminders I used

| Notation | Meaning | Example here |
|---|---|---|
| `A <\|-- B` | inheritance (B is an A) | `User <\|-- Patient` |
| `A *-- B` | composition: B can't exist without A | `Order *-- OrderLine` |
| `A o-- B` | aggregation: A groups B, but B lives on its own | `DailyRecordsFile o-- Order` |
| `A --> B` | association (A knows B) | `OrderLine --> Item` |
| `A ..> B` | dependency (A uses B for a moment) | `OrderProcessingClerk ..> Member` |
| `<<include>>` | always part of the base use case | Place Order → Verify Membership |
| `<<extend>>` | optional, only under a condition | Apply Discount → Place Order |
