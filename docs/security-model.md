# Security & Data Isolation Model

- Customer Isolation: Memory and conversation records are strictly segmented by customer ID.
- Provider Independence: Business logic interacts strictly through an abstract provider interface.
- Auditability: Every incoming enquiry, classification, proposed action, and approval state is persisted with timestamps.
