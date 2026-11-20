# User journeys

```mermaid
flowchart TD
  E[Employee signs in] --> New[Create request with budget and delivery date]
  New --> Pending[Track pending approval]
  Pending --> Review[Team manager reviews]
  Review -->|Revision with reason| Edit[Employee revises and resubmits]
  Edit --> Pending
  Review -->|Reject with reason| Rejected[Employee sees rejection and history]
  Review -->|Approve| Rank[Manager sees top three explained suppliers]
  Rank --> Select[Manager selects matching supplier]
  Select --> PO[Create one purchase order]
  PO --> Vendor[Assigned vendor sees order]
  Vendor --> Processing --> Shipped --> Delivered
  Delivered --> Metrics[Delivered spend and monthly analytics update]
  Pending <--> Discuss[Employee and reviewer discuss using threaded comments]
  PO --> Track[Employee tracks order status]
```

```mermaid
flowchart LR
  Admin[Admin signs in] --> Users[Assign roles / manager / vendor supplier]
  Admin --> Directory[Manage suppliers and categories]
  Admin --> Reports[Inspect company KPIs and export reports]
  Manager[Manager signs in] --> Team[Review team queue]
  Team --> ReportsTeam[Inspect team reports]
  Vendor[Vendor signs in] --> Assigned[View only linked supplier orders]
  Assigned --> Update[Advance fulfilment status sequentially]
```

Unauthenticated deep links go to sign-in. Expired sessions are restored only with
a valid rotating refresh cookie. Unauthorized resources appear unavailable.
Concurrent approval or duplicate order attempts produce actionable conflict
messages. Empty recommendation results explain that the category needs suppliers.
