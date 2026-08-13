# Whitfield Ops

Whitfield Fulfillment — Professional Warehouse Management System UI

Build a high-end, professional Warehouse Management System frontend for a company called:

Whitfield Fulfillment

This is not a marketing landing page.

This is an authenticated operational SaaS dashboard used every day by warehouse owners, managers, receiving staff, and fulfillment staff.

The backend already exists in FastAPI + MongoDB.

Your responsibility is to build the frontend architecture, UI/UX, role-specific navigation, dashboard layouts, tables, forms, workflows, states, and API integration layer.

Do not invent business logic that belongs on the backend.

1. PRODUCT CONTEXT

Whitfield Fulfillment operates two warehouses:

Reno, Nevada

Columbus, Ohio

The company receives inventory from multiple sellers, stores stock, fulfills customer orders, tracks damaged goods, reserves stock safely, packs orders, ships packages, and maintains a full audit trail.

The original business used Excel and suffered from:

duplicate receiving,

incorrect stock counts,

overselling,

simultaneous edits,

no audit history,

difficulty knowing who changed quantities,

no role-based access,

limited visibility into live warehouse operations.

This WMS solves those operational issues.

The UI should visually communicate:

control, confidence, speed, traceability, operational intelligence.

2. TECH STACK

Frontend:

React
TypeScript
Vite
Tailwind CSS
shadcn/ui
TanStack Router
TanStack Query
Axios
Lucide Icons


Follow this frontend architecture:

src/
├── app/
├── routes/
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── receiving/
│   ├── inventory/
│   ├── orders/
│   ├── fulfillment/
│   ├── sellers/
│   ├── products/
│   ├── audit/
│   ├── users/
│   └── warehouses/
├── components/
│   ├── ui/
│   ├── layout/
│   ├── feedback/
│   ├── data-display/
│   └── forms/
├── hooks/
├── lib/
│   ├── api/
│   ├── auth/
│   ├── utils/
│   └── constants/
├── types/
└── main.tsx


Do not put everything inside App.tsx.

Pages should remain thin.

Business UI should live inside feature components.

Use reusable components.

3. DESIGN DIRECTION

The visual design must feel like:

Linear + Vercel + modern enterprise logistics software

Not:

generic Bootstrap admin,

childish,

overly colorful,

traditional ERP,

template-like,

cluttered.

The application should feel premium and custom designed.

4. CORE COLOR SYSTEM

Use a sophisticated dark-neutral + violet/indigo palette inspired by the supplied reference image.

Primary palette:

Deep Charcoal
#0D0F14

Soft Black
#13161D

Surface
#181B23

Elevated Surface
#20232D

Electric Indigo
#6366F1

Deep Indigo
#4F46E5

Soft Violet
#8B5CF6

Lavender
#C4B5FD

Muted Lavender
#DDD6FE

Cool Gray
#94A3B8

Soft Border
rgba(255,255,255,0.08)


Light surfaces may use:

#F7F8FC
#FFFFFF
#F1F3F9


Accent colors:

Success: Emerald
Warning: Amber
Danger: Rose/Red
Information: Blue


Do not make the entire product purple.

Violet/indigo should be an accent and identity color.

5. GRAINY GRADIENT VISUAL LANGUAGE

The supplied reference image should inspire the visual identity.

Use atmospheric gradients such as:

radial-gradient(
  circle at 20% 10%,
  rgba(196,181,253,.55),
  transparent 35%
),
radial-gradient(
  circle at 70% 25%,
  rgba(99,102,241,.55),
  transparent 40%
),
radial-gradient(
  circle at 80% 80%,
  rgba(79,70,229,.35),
  transparent 40%
)


combined with deep charcoal backgrounds.

Add a subtle grain/noise texture over large decorative gradient areas.

Noise must be:

subtle,

premium,

low opacity,

not distracting.

Use grain primarily for:

login/signup background,

dashboard hero card,

empty states,

selected large feature areas.

Do not apply heavy grain over tables or forms.

6. GRADIENT RULES

Use gradients intentionally.

Good locations:

login visual panel,

active navigation indicator,

important KPI cards,

selected warehouse pill,

hero/overview card,

major CTA,

AI features later,

subtle page background glow.

Avoid:

gradient on every card,

gradient text everywhere,

rainbow gradients,

excessive glowing buttons.

Use mostly:

lavender
→ violet
→ indigo
→ deep navy


7. TYPOGRAPHY

Use a professional modern sans-serif.

Prefer:

Inter
Geist
Manrope


Typography hierarchy:

Page title:
28–32px
600–700

Section title:
18–20px
600

Card metric:
28–36px
600–700

Body:
14–16px

Supporting text:
12–14px


Avoid excessive bold text.

Use whitespace and typography hierarchy instead.

8. CORNER / SURFACE SYSTEM

Use:

Cards: 14–18px radius
Inputs: 10–12px
Buttons: 10–12px
Modals: 16–20px
Pills: fully rounded


Cards should use:

1px subtle border
soft shadow
slight background contrast


Avoid huge drop shadows.

Use thin borders more than shadows.

9. APPLICATION SHELL

After authentication the app should use a persistent desktop SaaS shell.

Structure:

┌──────────────────────────────────────────────────────────────┐
│ Sidebar │ Topbar                                             │
│         ├────────────────────────────────────────────────────┤
│         │                                                    │
│         │                 Page Content                       │
│         │                                                    │
└──────────────────────────────────────────────────────────────┘


Sidebar width around:

240–270px


Allow collapse to icon mode.

10. SIDEBAR

Top section:

Whitfield
Fulfillment


or:

Whitfield WMS


Create a minimal custom monogram icon using:

W


inside an indigo/violet geometric container.

Do not use a random warehouse stock icon as the primary brand.

Sidebar sections:

OVERVIEW

Dashboard

OPERATIONS

Receiving
Inventory
Orders
Fulfillment

CATALOG

Sellers
Products

MANAGEMENT

Audit Logs
Users

SYSTEM

Warehouses
Settings


But navigation items must be role-aware.

Do not show pages the current role should not use.

11. SIDEBAR ACTIVE STATE

Active navigation should use:

subtle indigo background
small violet/indigo gradient indicator
bright text


Example visual:

▌ Dashboard


or rounded active container.

Inactive navigation:

muted gray


Hover:

slightly elevated background


12. SIDEBAR BOTTOM

At bottom show:

Current user:

Avatar

Chaitanya Pawar
OWNER

•••


Click opens:

Profile
Settings
Sign out


Also show warehouse scope when relevant.

Example:

Reno Warehouse


13. TOPBAR

Topbar should contain:

Left:

Page breadcrumb / title


Right:

Global search
Warehouse selector
Notifications
User avatar


Warehouse selector example:

Reno, NV
⌄


OWNER may switch warehouses.

Warehouse-scoped staff only see assigned warehouse(s).

14. AUTHENTICATION EXPERIENCE

Create two polished auth screens:

/login
/signup


Auth layout should use a two-panel composition on desktop.

Example:

┌─────────────────────────┬──────────────────────────┐
│                         │                          │
│ Grainy violet/indigo    │ Login Form               │
│ visual                  │                          │
│                         │                          │
│ Operational message     │                          │
│                         │                          │
└─────────────────────────┴──────────────────────────┘


On mobile collapse to one panel.

15. LOGIN VISUAL PANEL

Use the supplied image aesthetic.

Create:

deep charcoal background
lavender cloud
electric indigo bloom
subtle blue/violet gradients
fine grain texture


Overlay minimal content:

Whitfield Fulfillment

Operations,
without the spreadsheet chaos.


Supporting text:

Receive, reserve, fulfill and trace inventory
across every warehouse from one workspace.


Optionally display small floating operational cards:

Reno
1,248 units available

Columbus
842 units available


These may initially be decorative or connected later.

Keep them subtle.

16. LOGIN FORM

Right side should contain:

Welcome back

Sign in to Whitfield Fulfillment


Fields:

Email
Password


Features:

show/hide password
remember me
forgot password
sign in


Primary CTA:

Sign in


Use subtle violet → indigo gradient for primary CTA.

Button must have strong accessibility contrast.

Below:

New to Whitfield?
Create an account


Do not add social login unless backend supports it.

17. SIGNUP PAGE

Signup should visually match login.

Fields based on backend user model should include:

First name
Last name
Email
Password / account setup


Do NOT allow users to freely select:

OWNER
MANAGER
RECEIVING_STAFF
FULFILLMENT_STAFF


from signup.

Role assignment is a privileged backend responsibility.

If the backend's current registration behavior automatically assigns a role, respect that behavior.

Build the frontend API layer so the exact registration endpoint can be mapped to the existing FastAPI route.

Do not hardcode assumptions into multiple components.

18. AUTH API ARCHITECTURE

Centralize auth operations:

lib/api/auth.ts


Functions conceptually:

login()
signup()
getCurrentUser()
logout()


Backend already exposes login/current-user functionality.

The frontend should inspect or map the actual existing registration route rather than inventing a competing API.

Store auth information using the existing backend authentication strategy.

Never expose secrets in frontend source.

19. AUTH STATE

Create a central auth provider/store.

Current user should provide:

id
first_name
last_name
email
role
status
warehouse_ids


Use this to control:

navigation
route access
buttons
warehouse context
dashboard variation


Frontend role restrictions are UX only.

Backend remains authoritative.

20. ROLE-BASED DASHBOARD STRATEGY

There should NOT be four completely different applications.

Use:

same design system
same app shell
same component library


but dynamically alter:

dashboard metrics
quick actions
navigation
operational queues
alerts


based on user role.

Roles:

OWNER
MANAGER
RECEIVING_STAFF
FULFILLMENT_STAFF


21. OWNER DASHBOARD

OWNER dashboard is the executive + operational command center.

URL:

/dashboard


Header:

Good morning, Chaitanya

Here’s what’s happening across Whitfield today.


Right side:

Warehouse selector:
All Warehouses
Reno
Columbus


22. OWNER KPI ROW

Display 4 premium KPI cards:

Total On Hand
Available Stock
Reserved Stock
Damaged Stock


Example structure:

24,680
Total On Hand

+4.2%
vs previous period


Each card should have:

metric,

label,

subtle icon,

optional comparison,

mini sparkline if available later.

Do not invent fake live percentages when no backend data exists.

Use skeleton/placeholder state until real aggregate endpoint exists.

23. OWNER SECONDARY METRICS

Second row:

Pending Receipts
Open Orders
Ready to Ship
Shipped Today


These should be actionable.

Clicking a metric navigates to its filtered page.

24. OWNER OPERATIONS OVERVIEW

Large left card:

Warehouse Overview


Tabs:

Reno
Columbus


Inside:

On Hand
Reserved
Damaged
Open Receipts
Open Orders
Ready to Ship


Use compact bar/chart visualization.

Do not use decorative charts without operational meaning.

25. OWNER INVENTORY HEALTH

Card:

Inventory Health


Show:

Healthy
Low Stock
Reserved Heavy
Damaged


Use donut/progress visualization if data supports it.

26. OWNER ACTIVITY FEED

Card:

Recent Activity


Example entries:

Receipt REC-1042 completed
24 units received into Reno
2 min ago


Order ORD-8431 shipped
UPS • 1Z73...
8 min ago


Inventory adjusted
Widget A • -2 units
Chaitanya • Cycle count correction
18 min ago


Connect to audit/movement endpoints where possible.

27. OWNER QUICK ACTIONS

Compact section:

Quick actions


Buttons:

New Receipt
New Order
Add Seller
Add Product
View Audit Log


Do not make this a giant card.

28. MANAGER DASHBOARD

Manager dashboard should emphasize operations and exceptions, not company-wide executive analytics.

Header:

Operations Overview
Reno Warehouse


Main KPIs:

Pending Receipts
Orders Awaiting Pick
Orders Awaiting Pack
Ready to Ship


Secondary metrics:

Available Inventory
Reserved Inventory
Damaged Inventory
Today's Shipments


29. MANAGER PRIORITY QUEUE

Large card:

Needs Attention


Show actionable rows such as:

Receipt awaiting completion

Low available stock

Order waiting for picking

Packed order waiting for shipment

High damaged quantity


Use colored status indicators:

red = urgent
amber = attention
blue = informational
green = completed/healthy


30. MANAGER INVENTORY CONTROL

Managers need direct access to:

Inventory
Movements
Adjust Inventory
Audit history


On inventory row actions:

View
Movement History
Adjust Inventory


Adjustment must open a modal.

31. INVENTORY ADJUSTMENT MODAL

Title:

Adjust Inventory


Show current values:

On Hand: 126
Reserved: 18
Available: 108
Damaged: 3


Input:

Adjustment


Support:

+5
-3


Required:

Reason


Examples:

Cycle count correction
Damaged stock reconciliation
Physical count variance


Confirmation should clearly preview:

126 → 123 units


Do not create an absolute stock-value edit field.

32. RECEIVING STAFF DASHBOARD

Receiving staff dashboard should be extremely task-oriented.

Avoid executive charts.

Header:

Receiving
Reno Warehouse


Primary CTA:

+ New Receipt


Main KPI cards:

Today's Receipts
In Progress
Completed Today
Units Received Today


33. RECEIVING WORK QUEUE

Main table:

Active Receipts


Columns:

Receipt
Seller
Tracking / Ticket
Items
Received Qty
Status
Created
Action


Status pills:

Draft
In Progress
Completed
Cancelled


Primary row action:

Continue Receiving


34. NEW RECEIPT FLOW

Build a clean step-based receiving workflow.

Step 1

Shipment Information


Select:

Seller
Warehouse


Enter:

Tracking Number
Ticket Number


At least one tracking/ticket should be present according to backend validation.

CTA:

Create Receipt


35. RECEIPT WORKSPACE

After creation navigate to:

/receiving/:receiptId


Header:

REC-1048

Acme Corp
Reno Warehouse
Tracking: 1Z...


Status:

IN PROGRESS


36. UPC SCANNING AREA

This should be the strongest UX on the receiving page.

Large input:

Scan or enter UPC


Use barcode icon.

Auto-focus it.

Staff should be able to use a physical barcode scanner that behaves like keyboard input.

When UPC is found, show a product card:

Widget A

SKU: WIDGET-A
UPC: 194253397168
Seller: Acme Corp


Then quantity controls:

Good Quantity
[ - ] 24 [ + ]

Damaged Quantity
[ - ] 3 [ + ]


CTA:

Add to Receipt


37. RECEIVING PRODUCT ENTRY

Make entry keyboard-friendly.

Tab order should be excellent.

Allow:

UPC → Enter
Good Qty → Enter
Damaged Qty → Enter
Add


Display clear errors:

UPC not found

Product belongs to another seller

Receipt already completed

Duplicate shipment


Use inline errors, not browser alerts.

38. RECEIPT ITEMS TABLE

Below scanning:

Received Items


Columns:

Product
SKU
UPC
Good
Damaged
Total


Bottom summary:

Good Units        24
Damaged Units      3
Total Received    27


Primary CTA:

Complete Receipt


Require confirmation modal:

Complete REC-1048?

24 good units will be added to sellable inventory.
3 damaged units will be recorded separately.

This receipt cannot be edited normally after completion.


CTA:

Complete Receipt


39. RECEIPT COMPLETE SUCCESS

After successful completion show:

Receipt completed


with polished success state.

Actions:

View Inventory
Back to Receiving
Create Another Receipt


40. FULFILLMENT STAFF DASHBOARD

Fulfillment dashboard should emphasize the outbound queue.

Header:

Fulfillment
Reno Warehouse


Primary metrics:

Orders to Pick
Picking
Ready to Pack
Ready to Ship


Secondary:

Shipped Today
Reserved Units


41. FULFILLMENT WORK QUEUE

Main board/table.

Allow tabs:

All
Reserved
Picking
Picked
Packed
Ready to Ship


Columns:

Order
Seller
Items
Units
Status
Created
Action


Primary action depends on state:

RESERVED
→ Start Picking

PICKING
→ Mark Picked

PICKED
→ Pack Order

PACKED
→ Create Shipment

READY_TO_SHIP
→ Ship Order


The UI must follow backend state transitions.

Never let the frontend skip workflow states.

42. ORDERS PAGE

URL:

/orders


Header:

Orders


Actions:

+ New Order


Filters:

Search
Warehouse
Seller
Status
Date


Table:

Order #
Seller
Warehouse
Items
Units
Status
Created
Updated


Use sticky table header.

Use pagination or query-based pagination pattern.

43. NEW ORDER

Create an order builder.

Step 1:

Seller
Warehouse


Step 2:

Add Products


Search using:

SKU
UPC
Product Name


Selected product row:

Widget A
SKU WIDGET-A

Available: 24

Quantity:
[-] 5 [+]


Display current available inventory if endpoint provides it.

Never allow frontend availability to override backend reservation validation.

CTA:

Create Order


44. ORDER DETAIL PAGE

URL:

/orders/:orderId


Header:

ORD-1088


Status pill.

Top metadata:

Seller
Warehouse
Created
Created By


Items table:

Product
SKU
Ordered
Reserved
Picked


Right-side / top action panel based on status.

45. ORDER STATUS TIMELINE

Create a beautiful horizontal/vertical operational timeline:

Created
   ✓

Reserved
   ✓

Picking
   ✓

Picked
   ✓

Packed
   ●

Ready to Ship
   ○

Shipped
   ○


Use compact icons and timestamps.

This will visually communicate the workflow very well.

46. PICKING EXPERIENCE

When action:

Start Picking


change to dedicated picking state.

Show:

Pick List


Rows:

Widget A
SKU WIDGET-A

Required: 5
Picked: [5]


CTA:

Mark Order Picked


47. PACKING EXPERIENCE

After picked:

Packing


Show item verification and summary.

CTA:

Mark Packed


Do not introduce complex packaging logic the backend does not support.

48. SHIPMENT CREATION

After packed:

Form:

Carrier
Tracking Number
Weight

Dimensions
Length
Width
Height

Label Reference


Use unit suffixes.

Example:

Weight
[2.4] kg


Length [40] cm
Width  [30] cm
Height [18] cm


CTA:

Prepare Shipment


49. READY TO SHIP

Display a shipment card:

UPS

1Z999AA...

2.4 kg

40 × 30 × 18 cm


Primary action:

Ship Order


Confirmation modal:

Confirm shipment?

This will finalize this order and deduct shipped
units from on-hand and reserved inventory.


50. SHIPPED ORDER

After shipping:

Show green success state:

Shipped

UPS
1Z...


Timeline should show all completed stages.

No mutation buttons should remain except read-only actions.

51. INVENTORY PAGE

URL:

/inventory


Header:

Inventory


Filters:

Search
Warehouse
Seller
Availability


Table columns:

Product
SKU
UPC
Seller
Warehouse
On Hand
Reserved
Available
Damaged
Status


Use numeric alignment.

Available should be visually prominent.

52. INVENTORY STATUS

Use smart visual statuses:

Healthy
Low Stock
No Available Stock
Damaged Stock
Reserved Heavy


Do not invent backend status fields.

Derive display status from actual numeric values only when safe.

53. INVENTORY DETAIL DRAWER

Click a row to open side drawer or dedicated page.

Show:

Product Information

Warehouse
Seller
SKU
UPC


Stock:

On Hand
Reserved
Available
Damaged


Then:

Movement History


54. MOVEMENT HISTORY UI

Timeline/table:

Type
Quantity
Before
After
Reference
Performed By
Time
Reason


Examples:

RECEIVED
+24

ADJUSTMENT_DECREASE
-2

RESERVED
5

SHIPPED
-5


Use:

green = receive/increase
amber = reserve
red = decrease/adjust
blue/violet = shipped


but keep palette muted and professional.

55. SELLERS PAGE

URL:

/sellers


Header:

Sellers


CTA:

+ Add Seller


Table:

Seller
Code
Email
Phone
Status
Created


Owner/Manager can create/manage.

Operational staff primarily read.

56. ADD SELLER MODAL

Fields:

Seller Name
Seller Code
Email
Phone


CTA:

Create Seller


Validate inline.

57. PRODUCTS PAGE

URL:

/products


Filters:

Search
Seller
Status


Table:

Product
SKU
UPC
Seller
Status


CTA:

+ Add Product


58. ADD PRODUCT MODAL

Fields:

Seller
Product Name
SKU
UPC
Description


Show clear conflict error when:

SKU already exists
UPC already exists


59. AUDIT PAGE

URL:

/audit


Primarily Owner/Manager.

Header:

Audit Log


Subtitle:

Trace sensitive operational activity across Whitfield.


Filters:

Warehouse
User
Action
Entity
Date


Table:

Action
Entity
User
Role
Warehouse
Time
Details


60. AUDIT DETAILS

Click row → side drawer.

Example:

INVENTORY_ADJUSTED

Product
Widget A

User
Chaitanya Pawar

Reason
Cycle count correction

Previous
126

New
124

Warehouse
Reno

Timestamp
...


Do not expose raw sensitive backend payloads.

61. USERS PAGE

Owner-only if backend supports required endpoints.

Display:

Name
Email
Role
Warehouse Access
Status


Do not invent update APIs that do not exist.

If backend currently lacks role-management endpoints, create the UI structure but disable mutation controls or mark integration TODO.

62. WAREHOUSES PAGE

Display:

Reno, NV
Columbus, OH


Cards can show operational summaries later.

Avoid creating unsupported warehouse editing.

These are core seeded facilities.

63. OWNER VS MANAGER NAVIGATION

OWNER sees:

Dashboard
Receiving
Inventory
Orders
Fulfillment
Sellers
Products
Audit Logs
Users
Warehouses


MANAGER sees:

Dashboard
Receiving
Inventory
Orders
Fulfillment
Sellers
Products
Audit Logs


within authorized warehouse scope.

64. RECEIVING STAFF NAVIGATION

Show primarily:

Dashboard
Receiving
Inventory
Products


Potential read-only Order access only if backend permits it.

Hide:

Users
Management configuration
Inventory adjustment


65. FULFILLMENT STAFF NAVIGATION

Show:

Dashboard
Orders
Fulfillment
Inventory
Products


Hide:

New Receipt
Inventory Adjust
Users
Audit Management
Seller management


66. ROUTE GUARDS

Implement frontend route guard components.

Example:

<AuthenticatedRoute />
<RoleRoute allowedRoles=[...] />


But remember:

Frontend protection is for UX.

Backend API permission remains authoritative.

If backend returns 403, show:

You don't have permission to perform this action.


Do not crash or silently redirect unexpectedly.

67. API LAYER

Create centralized typed API modules:

lib/api/auth.ts
lib/api/warehouses.ts
lib/api/sellers.ts
lib/api/products.ts
lib/api/receipts.ts
lib/api/inventory.ts
lib/api/orders.ts
lib/api/audit.ts


Do not put Axios calls inside random components.

68. BACKEND API MAP

Use the existing FastAPI backend.

Authentication

Existing backend includes login/current-user functionality.

Map the actual routes present in OpenAPI.

Current user functionality includes:

GET /v1/auth/me


Use actual login/registration paths exposed by backend rather than inventing alternatives.

Warehouses

GET /v1/warehouses
GET /v1/warehouses/{warehouse_id}


Sellers

POST /v1/sellers
GET /v1/sellers
GET /v1/sellers/{seller_id}
PATCH /v1/sellers/{seller_id}/status


Products

POST /v1/products
GET /v1/products
GET /v1/products/upc/{upc}
GET /v1/products/{product_id}
PATCH /v1/products/{product_id}/status


Receipts

POST /v1/receipts
GET /v1/receipts
GET /v1/receipts/{receipt_id}
POST /v1/receipts/{receipt_id}/items
POST /v1/receipts/{receipt_id}/complete


Inventory

GET /v1/inventory
GET /v1/inventory/{inventory_id}
POST /v1/inventory/{inventory_id}/adjust
GET /v1/inventory/{inventory_id}/movements


Audit

GET /v1/audit-logs


Orders

POST /v1/orders
GET /v1/orders
GET /v1/orders/{order_id}

POST /v1/orders/{order_id}/reserve
POST /v1/orders/{order_id}/start-picking
POST /v1/orders/{order_id}/picked
POST /v1/orders/{order_id}/packed
POST /v1/orders/{order_id}/shipment
POST /v1/orders/{order_id}/ship
POST /v1/orders/{order_id}/cancel


Before integration, inspect the actual FastAPI OpenAPI JSON and match exact request/response shapes.

Do not assume field names if OpenAPI says otherwise.

69. TANSTACK QUERY

Use TanStack Query throughout.

Create query keys such as:

['current-user']

['warehouses']

['sellers', filters]

['products', filters]

['receipts', filters]

['receipt', id]

['inventory', filters]

['inventory-movements', inventoryId]

['orders', filters]

['order', id]

['audit-logs', filters]


After mutations invalidate only relevant data.

Example receipt completion:

invalidate receipt
invalidate receipt list
invalidate inventory
invalidate dashboard summary
invalidate movement history
invalidate audit


70. GLOBAL SEARCH

Top navigation global search should eventually search:

Order #
Receipt #
Tracking #
SKU
UPC
Seller


If backend does not support unified search, implement visual component but connect only supported searches.

Do not fetch every table and search client-side at large scale.

71. TABLE DESIGN

Tables must be professional.

Use:

sticky headers
48–56px row height
subtle separators
hover state
aligned numeric columns
status badges
row action menu
skeleton loading
empty state
pagination


Avoid giant bordered spreadsheet-looking grids.

72. EMPTY STATES

Every major feature needs intentional empty states.

Examples:

Inventory:

No inventory found
Try changing your filters or receive new stock.


Orders:

No orders in this queue
New orders will appear here once created.


Receiving:

No active receipts
Create a receipt when the next shipment arrives.


Use subtle illustration/icon + small gradient glow.

73. LOADING STATES

Never show plain:

Loading...


Use:

skeleton cards,

skeleton table rows,

disabled action states,

spinner inside buttons for mutations.

74. ERROR STATES

Use toast + inline context.

Example:

Could not reserve inventory

Only 4 units are currently available.


For 409, surface meaningful backend business message.

For 403:

You don't have permission to perform this action.


For network errors:

Unable to connect to Whitfield WMS.
Try again.


75. CONFIRMATION MODALS

Sensitive actions require confirmation:

Complete Receipt
Inventory Adjustment
Cancel Order
Ship Order


Use clear consequences.

Never use browser confirm().

Use polished shadcn AlertDialog/Dialog.

76. TOASTS

Success examples:

Receipt created

Inventory adjusted

Order reserved

Order marked picked

Shipment prepared

Order shipped


Failures should not expose raw server stack traces.

77. STATUS BADGE SYSTEM

Standardize status components.

Receipt:

DRAFT
IN_PROGRESS
COMPLETED
CANCELLED


Order:

NEW
RESERVED
PICKING
PICKED
PACKED
READY_TO_SHIP
SHIPPED
CANCELLED


Warehouse/product/seller status should also use the shared badge component.

78. ACCESSIBILITY

Ensure:

keyboard navigation
visible focus states
aria labels
proper form labels
accessible dialogs
sufficient contrast
not relying solely on color


Receiving is especially keyboard-focused.

79. RESPONSIVE DESIGN

Primary target:

desktop warehouse laptop
1440px


Also support:

1024px tablet
mobile basic usability


Tables can become horizontal-scroll views on smaller displays.

Receiving screen should remain usable on tablets.

80. DARK + LIGHT MODE

Design should primarily shine in dark mode.

Also implement a professional light mode.

Dark mode:

charcoal
deep navy
violet accents


Light mode:

off-white
cool gray
subtle lavender accents


Avoid pure white everywhere.

Add theme switch in user menu/settings.

81. DASHBOARD CHARTS

Use charts sparingly.

Useful:

Inventory composition

Orders by status

Receipts over time

Shipments today

Warehouse comparison


Do not create meaningless charts just to fill space.

If aggregate backend data does not yet exist:

Build the component structure with empty/loading states instead of inserting fake analytics.

82. MICRO-INTERACTIONS

Use subtle animations:

150–250ms


Examples:

sidebar hover,

card hover,

modal appearance,

dropdown,

table selection,

success state,

status timeline.

Avoid dramatic motion.

83. DASHBOARD HERO

Owner dashboard may have one premium top section.

Example:

Operations Overview

Everything across Reno and Columbus
is operating normally.


Background:

charcoal
+ indigo radial glow
+ subtle lavender grain


Small indicators:

● Reno Operational
● Columbus Operational


Do not make hero excessively tall.

84. VISUAL DENSITY

This is operational software.

Use medium-high information density.

Do not build huge cards with one number occupying half the page.

Optimize for:

scanability
decision speed
task completion


while preserving premium visual design.

85. ICONS

Use Lucide icons.

Examples:

LayoutDashboard
PackageOpen
Boxes
ShoppingCart
ClipboardList
Truck
Store
Barcode
History
Users
Warehouse
Search
Bell
Settings


Use consistent 16/18/20px sizing.

Do not mix icon libraries.

86. REAL DATA RULE

Do not permanently hardcode dashboard inventory/order/receipt values.

Backend data should be the source of truth.

Temporary mock data may only be used during isolated visual construction.

Before a page is considered integrated, remove mock operational data.

87. DO NOT MODIFY BACKEND BUSINESS RULES

Frontend must respect:

available = on_hand - reserved

received = good + damaged

completed receipt cannot be edited normally

inventory adjustment requires delta + reason

reservation can fail with 409

orders follow state transitions

shipment must be prepared before shipping

shipped order cannot mutate stock again


Do not recreate these guarantees solely in JavaScript.

The server decides.

88. IMPORTANT FRONTEND PRINCIPLE

Every page should answer one of these questions immediately:

Dashboard:

What needs my attention?


Receiving:

What shipment am I receiving?


Inventory:

What stock do I actually have?


Orders:

What must be fulfilled?


Fulfillment:

What action comes next?


Audit:

Who changed what and why?


Design around these questions.

89. MVP FRONTEND PRIORITY

Implement in this order:

1. Design system
2. Login
3. App shell
4. Role-aware navigation
5. Inventory
6. Receiving
7. Orders
8. Fulfillment
9. Owner dashboard
10. Manager dashboard
11. Receiving dashboard
12. Fulfillment dashboard
13. Sellers
14. Products
15. Movement history
16. Audit
17. Polish / responsiveness


Do not spend hours perfecting analytics before receiving/orders work.

90. DEMO FLOW TO OPTIMIZE FOR

The UI must make this demo extremely smooth:

Login as OWNER
      ↓
Dashboard
      ↓
Create Receipt
      ↓
Enter/scan UPC
      ↓
24 Good
3 Damaged
      ↓
Complete Receipt
      ↓
Open Inventory
      ↓
Show 24 On Hand / 3 Damaged
      ↓
Create Order
      ↓
Reserve
      ↓
Start Picking
      ↓
Picked
      ↓
Packed
      ↓
Create Shipment
      ↓
Ship
      ↓
Inventory decreases
      ↓
Open movement/audit history
      ↓
Show full traceability


The evaluator should understand the WMS without needing technical explanation.

91. ROLE DEMO EXPERIENCE

Also optimize for quick role demonstrations.

OWNER

Show:

entire operation
all warehouses
inventory
orders
audit
management


MANAGER

Show:

warehouse operations
exceptions
inventory control
adjustments
audit


RECEIVING STAFF

Show:

simple receiving queue
barcode-oriented workflow
minimal distractions


FULFILLMENT STAFF

Show:

order queue
pick
pack
ship
minimal distractions


This differentiation is important.

92. DESIGN QUALITY BAR

Before considering a screen complete, ask:

Does this look like software a real logistics company could pay for?

Can a warehouse worker understand the next action immediately?

Does the page feel intentionally designed rather than generated?

Is hierarchy obvious?

Are actions clear?

Are dangerous actions protected?

Are loading, error and empty states designed?

Is it visually consistent with the rest of Whitfield?


If not, refine it.

93. FINAL DESIGN IDENTITY

Whitfield WMS should feel:

Professional
Confident
Fast
Technical
Operational
Modern
Reliable
Premium


Visual signature:

deep charcoal surfaces
+
electric indigo
+
soft violet/lavender
+
subtle grain
+
precise typography
+
high-quality tables
+
restrained gradients


Use the uploaded grainy violet/black reference image as inspiration for atmosphere, not as a literal full-page copy.

94. IMPORTANT

Do not generate a marketing homepage.

Start with the authenticated product experience.

Build the UI as if this will be demonstrated tomorrow to:

a warehouse owner
+
an FDE mentor
+
a technical evaluator


The frontend should visually demonstrate that the spreadsheet workflow has become a controlled, modern operations platform.

Begin with the design system, authentication screen, and app shell, then build the operational workflows in the priority order above.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/931d5c13-e0e3-4102-b4f3-2648a756fe0e).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
