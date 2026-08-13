# Whitfield WMS Frontend Audit

## 1. Executive Summary

- **Build Status**: `PASS` (Built in 336ms + Nitro SSR build in 468ms with zero errors)
- **Dev Server Status**: `PASS` (`http://localhost:8080/`)
- **Frontend Framework**: React 19.2.0 with Vite 8.2.1, `@tanstack/react-start` 1.168.32, `@tanstack/react-router` 1.170.18, and Nitro 3.0 SSR
- **Routing**: `@tanstack/react-router` with file-based routing defined in `src/routes/` and generated route tree in `src/routeTree.gen.ts`
- **API Client**: Centralized Axios client (`src/lib/api/client.ts`) with automated fallback to `src/lib/api/demo-backend.ts` when `VITE_API_BASE_URL` is empty/unset
- **Query Layer**: `@tanstack/react-query` v5.101.1
- **Auth Strategy**: `AuthProvider` React Context (`src/lib/auth/auth-context.tsx`) with localStorage JWT persistence (`whitfield.token`), request interceptor for `Authorization: Bearer <token>`, and hardcoded demo users for local presentation
- **Current Data Strategy**: In-memory mock/demo state engine (`src/lib/api/demo-backend.ts`) wrapped inside 1:1 typed API service modules (`auth.ts`, `inventory.ts`, `orders.ts`, `receipts.ts`, `sellers.ts`, `products.ts`, `audit.ts`, `users.ts`, `warehouses.ts`)
- **Supabase / Lovable Backend Dependency**: **NO** (No Supabase package/auth/DB exists. Only dev plugin `@lovable.dev/vite-tanstack-config` and preview error reporting helper exist)
- **Overall Integration Readiness**: **READY TO CONNECT**. The Lovable generated architecture was exceptionally well engineered with a clean, pre-built API abstraction layer (`LIVE_API` flag checking `VITE_API_BASE_URL`).

---

## 2. Folder Structure

```text
D:\WMS\frontend\src
├── components/                  # UI and Layout Components
│   ├── data-display/            # KPI cards and status badges (kpi-card.tsx, status-badge.tsx)
│   ├── feedback/                # Empty states, table skeletons, loading indicators (states.tsx)
│   ├── layout/                  # Navigation components (app-sidebar.tsx, app-topbar.tsx, brand.tsx, page-header.tsx)
│   └── ui/                      # 46 shadcn/ui components (button, table, dialog, input, select, etc.)
├── features/                    # Domain Features & Pages
│   ├── auth/                    # Login and Signup forms & auth layout (login-form.tsx, signup-form.tsx, auth-layout.tsx)
│   ├── dashboard/               # Main dashboard with role-aware metrics & warehouse overview (dashboard-page.tsx)
│   └── shared/                  # Shared CRUD resource pages (resource-pages.tsx: Receiving, Inventory, Orders, Sellers, Products, Users, Audit)
├── hooks/                       # Utility hooks
│   └── use-mobile.tsx           # Mobile breakpoint helper hook
├── lib/                         # Core Application Libraries & API Architecture
│   ├── api/                     # 1:1 Typed API Service Layer
│   │   ├── client.ts            # Centralized Axios instance, token helpers, LIVE_API detection, error normalizer
│   │   ├── demo-backend.ts      # Stateful in-memory mock backend logic for standalone presentation
│   │   ├── auth.ts              # Login, signup, getCurrentUser, logout service module
│   │   ├── inventory.ts         # Inventory listing, details, adjustment, movement history service module
│   │   ├── orders.ts            # Order listing, details, creation, state transitions, shipment creation
│   │   ├── receipts.ts          # Inbound receipt listing, details, creation, item scanning, completion
│   │   ├── products.ts          # Product catalog listing, UPC lookup, creation, status toggle
│   │   ├── sellers.ts           # Seller listing, creation, status toggle
│   │   ├── warehouses.ts        # Facility listing and detail lookup
│   │   ├── audit.ts             # Audit log listing with filters
│   │   ├── users.ts             # Team member user listing
│   │   └── index.ts             # Barrel export for all API service modules
│   ├── auth/                    # React Auth Context & useAuth hook (auth-context.tsx)
│   ├── constants/               # Navigation configuration & role access rules (navigation.ts)
│   ├── utils/                   # Formatting utilities (format.ts)
│   ├── error-capture.ts         # Error capture utilities
│   ├── error-page.ts            # Server-side SSR error page template
│   ├── lovable-error-reporting.ts # Editor preview error forwarder
│   ├── theme.tsx                # Dark / Light theme provider & state
│   ├── utils.ts                 # Tailwind class merger (clsx + tailwind-merge)
│   └── warehouse-scope.tsx      # Global facility selector provider & state (WarehouseScopeProvider)
├── routes/                      # TanStack Router File Routes
│   ├── __root.tsx               # Root route wrapping application with QueryClient, Theme, Auth, Outlet, Toaster
│   ├── index.tsx                # Root redirect route (to /dashboard or /login)
│   ├── login.tsx                # Login page route
│   ├── signup.tsx               # Signup page route
│   ├── _shell.tsx               # Authenticated shell layout (Sidebar, Topbar, WarehouseScope, Auth Guard)
│   ├── _shell.dashboard.tsx     # Dashboard route
│   ├── _shell.receiving.index.tsx # Receiving list route
│   ├── _shell.receiving.new.tsx # New receipt creation route
│   ├── _shell.receiving.$receiptId.tsx # Receipt workspace / scanning detail route
│   ├── _shell.inventory.tsx    # Inventory table & stock adjustment route
│   ├── _shell.orders.index.tsx  # Orders list route
│   ├── _shell.orders.new.tsx    # Order creation route
│   ├── _shell.orders.$orderId.tsx # Order details, line items, timeline & shipment route
│   ├── _shell.fulfillment.tsx   # Warehouse fulfillment queue route
│   ├── _shell.sellers.tsx       # Sellers management route
│   ├── _shell.products.tsx      # Product catalog route
│   ├── _shell.audit.tsx         # Audit log route
│   ├── _shell.users.tsx         # User management route
│   └── _shell.settings.tsx      # Settings & profile route
├── types/                       # TypeScript Domain Models
│   └── index.ts                 # Shared domain interfaces (User, Warehouse, Seller, Product, Receipt, InventoryRecord, Movement, Order, Shipment, AuditLog)
├── routeTree.gen.ts             # Generated TanStack router route tree
├── router.tsx                   # TanStack Router factory with TanStack Query context
├── server.ts                    # SSR entrypoint wrapper
├── start.ts                     # TanStack Start server configuration & CSRF middleware
└── styles.css                   # Global CSS tokens, custom dark theme, glassmorphism, scrollbars
```

---

## 3. Dependency Summary

| Category | Library | Version | Usage |
| :--- | :--- | :--- | :--- |
| **Core Framework** | `react`, `react-dom` | `^19.2.0` | UI rendering |
| **Build Tooling** | `vite` | `^8.2.0` | Next-gen Vite build system |
| **Server Engine** | `nitro`, `@tanstack/react-start` | `3.0.260603-beta`, `1.168.32` | SSR engine & server functions |
| **Routing** | `@tanstack/react-router` | `1.170.18` | Type-safe file-based router |
| **Data Fetching** | `@tanstack/react-query` | `^5.101.1` | Asynchronous state & caching |
| **HTTP Client** | `axios` | `^1.19.0` | REST API communication |
| **UI Primitive** | `@radix-ui/*` (25 packages) | Various | Accessible unstyled primitives |
| **Styling** | `tailwindcss`, `@tailwindcss/vite` | `^4.2.1` | Utility-first CSS styling |
| **Form Handling** | `react-hook-form` | `^7.71.2` | Form state management |
| **Validation** | `zod`, `@hookform/resolvers` | `^3.24.2`, `^5.2.2` | Schema validation |
| **Icons** | `lucide-react` | `^0.575.0` | Icon system |
| **Toast** | `sonner` | `^2.0.7` | Rich toast notifications |
| **Charts** | `recharts` | `^2.15.4` | Data visualization |

---

## 4. Application Architecture

The application initialization follows a strict hierarchy:

```text
src/start.ts / src/server.ts
          ↓
  src/router.tsx (Configures QueryClient + TanStack Router)
          ↓
  src/routes/__root.tsx (Root Component)
          ├── QueryClientProvider (TanStack Query)
          ├── ThemeProvider (Dark/Light mode)
          └── AuthProvider (User auth context & token validation)
                    ├── Outlet (Renders child routes)
                    └── Toaster (Sonner rich notifications)
                              ↓
                    src/routes/_shell.tsx (Authenticated App Shell)
                              ├── WarehouseScopeProvider (Facility filter state)
                              ├── AppSidebar (Navigation & Role guards)
                              ├── AppTopbar (Search, Facility Selector, User menu)
                              └── Page Components (Dashboard, Inventory, Receiving, Orders, etc.)
```

---

## 5. Route Map

| Route | Component / Page | Role Access | Protected? | Data Source |
| :--- | :--- | :--- | :--- | :--- |
| `/` | `index.tsx` | ALL | No | Redirect to `/dashboard` or `/login` |
| `/login` | `login.tsx` / `LoginForm` | Public | No | `authApi.login` (Demo / API) |
| `/signup` | `signup.tsx` / `SignupForm` | Public | No | `authApi.signup` (Demo / API) |
| `/dashboard` | `_shell.dashboard.tsx` / `DashboardPage` | `OWNER`, `MANAGER`, `RECEIVING_STAFF`, `FULFILLMENT_STAFF` | Yes | `inventoryApi`, `ordersApi`, `receiptsApi`, `auditApi` |
| `/receiving` | `_shell.receiving.index.tsx` / `ReceivingPage` | `OWNER`, `MANAGER`, `RECEIVING_STAFF` | Yes | `receiptsApi.list` |
| `/receiving/new` | `_shell.receiving.new.tsx` / `NewReceiptPage` | `OWNER`, `MANAGER`, `RECEIVING_STAFF` | Yes | `receiptsApi.create`, `sellersApi.list`, `warehousesApi.list` |
| `/receiving/:receiptId` | `_shell.receiving.$receiptId.tsx` / `ReceiptDetailPage` | `OWNER`, `MANAGER`, `RECEIVING_STAFF` | Yes | `receiptsApi.get`, `receiptsApi.addItem`, `receiptsApi.complete` |
| `/inventory` | `_shell.inventory.tsx` / `InventoryPage` | `OWNER`, `MANAGER`, `RECEIVING_STAFF`, `FULFILLMENT_STAFF` | Yes | `inventoryApi.list`, `inventoryApi.adjust` |
| `/orders` | `_shell.orders.index.tsx` / `OrdersPage` | `OWNER`, `MANAGER`, `FULFILLMENT_STAFF` | Yes | `ordersApi.list` |
| `/orders/new` | `_shell.orders.new.tsx` / `NewOrderPage` | `OWNER`, `MANAGER`, `FULFILLMENT_STAFF` | Yes | `ordersApi.create`, `sellersApi.list`, `productsApi.list` |
| `/orders/:orderId` | `_shell.orders.$orderId.tsx` / `OrderDetailPage` | `OWNER`, `MANAGER`, `FULFILLMENT_STAFF` | Yes | `ordersApi.get`, `ordersApi.transition`, `ordersApi.createShipment` |
| `/fulfillment` | `_shell.fulfillment.tsx` / `OrdersPage(fulfillmentMode=true)` | `OWNER`, `MANAGER`, `FULFILLMENT_STAFF` | Yes | `ordersApi.list` (Filtered by work queue) |
| `/sellers` | `_shell.sellers.tsx` / `SellersPage` | `OWNER`, `MANAGER` | Yes | `sellersApi.list` |
| `/products` | `_shell.products.tsx` / `ProductsPage` | `OWNER`, `MANAGER`, `RECEIVING_STAFF`, `FULFILLMENT_STAFF` | Yes | `productsApi.list` |
| `/audit` | `_shell.audit.tsx` / `AuditPage` | `OWNER`, `MANAGER` | Yes | `auditApi.list` |
| `/users` | `_shell.users.tsx` / `UsersPage` | `OWNER` | Yes | `usersApi.list` |
| `/settings` | `_shell.settings.tsx` / `SettingsPage` | `OWNER`, `MANAGER`, `RECEIVING_STAFF`, `FULFILLMENT_STAFF` | Yes | `useAuth`, `useTheme`, `LIVE_API` indicator |

---

## 6. Authentication Architecture

- **Login Component**: `src/features/auth/login-form.tsx`
  - Fields: `email` (default: `owner@whitfield.com`), `password` (default: `whitfield`), `remember` checkbox, show/hide password toggle.
- **Signup Component**: `src/features/auth/signup-form.tsx`
  - Fields: `first_name`, `last_name`, `email`, `password` (validated length ≥ 8).
- **Auth Provider**: `src/lib/auth/auth-context.tsx` (`AuthProvider` and `useAuth` hook)
  - Uses TanStack Query key `["current-user", token]` to trigger `authApi.getCurrentUser(token)`.
- **Token Handling**:
  - Saved in `localStorage` under key `whitfield.token`.
  - HTTP Interceptor in `src/lib/api/client.ts` attaches `Authorization: Bearer <token>` header to all requests.
- **Protected Routes & Role Guards**:
  - Encapsulated in `src/routes/_shell.tsx`.
  - Redirects unauthenticated users to `/login`.
  - Compares current user role against `ROUTE_ROLES` dictionary in `src/lib/constants/navigation.ts`. If forbidden, redirects to `/dashboard`.
- **Hardcoded Demo Accounts**:
  - `owner@whitfield.com` (Role: `OWNER`)
  - `manager@whitfield.com` (Role: `MANAGER`)
  - `receiving@whitfield.com` (Role: `RECEIVING_STAFF`)
  - `fulfillment@whitfield.com` (Role: `FULFILLMENT_STAFF`)
  - Password for all: `whitfield`

---

## 7. Role-Based UI

| Role | Dashboard View | Navigation Items Visible | Action Capabilities |
| :--- | :--- | :--- | :--- |
| **OWNER** | Full Operations Overview, Reno/Columbus status widgets, Executive KPIs (On Hand, Available, Reserved, Damaged), Recent Activity, Quick Actions | Dashboard, Receiving, Inventory, Orders, Fulfillment, Sellers, Products, Audit Logs, Users, Warehouses, Settings | Unlimited access to all actions, scope switching across ALL facilities |
| **MANAGER** | Operations Overview, Executive KPIs, Recent Activity, Quick Actions | Dashboard, Receiving, Inventory, Orders, Fulfillment, Sellers, Products, Audit Logs, Warehouses, Settings | Full operational actions within assigned warehouse(s) |
| **RECEIVING_STAFF** | Receiving Dashboard (Active Receipts, Completed Receipts, Good Units, Damaged Units), Needs Attention Queue | Dashboard, Receiving, Inventory, Products, Settings | Create Receipt, Scan UPC, Good/Damaged Qty, Complete Receipt |
| **FULFILLMENT_STAFF** | Fulfillment Dashboard (To Pick, Picking, Ready to Pack, Ready to Ship), Needs Attention Queue | Dashboard, Inventory, Orders, Fulfillment, Products, Settings | Reserve, Start Picking, Complete Picking, Pack, Create Shipment, Mark Shipped |

---

## 8. Dashboard Architecture

Component: `src/features/dashboard/dashboard-page.tsx`

The dashboard dynamically inspects `user.role`:
1. **Executive Layout (`OWNER` / `MANAGER`)**:
   - Executive Banner with warehouse operational indicators (Reno, Columbus).
   - Row 1 KPIs: Total On Hand, Available Stock, Reserved Stock, Damaged Stock.
   - Row 2 KPIs: Pending Receipts, Open Orders, Ready to Ship, Shipped.
   - Interactive `WarehouseOverview` tabs (Reno Warehouse vs Columbus Warehouse breakdown of On Hand, Reserved, Damaged, Open Receipts, Open Orders).
   - `Recent Activity` stream pulling top 5 items from `auditApi.list()`.
2. **Receiving Staff Layout (`RECEIVING_STAFF`)**:
   - KPIs: Active Receipts, Completed Receipts, Units Received, Damaged Units.
   - `Needs Attention` widget highlighting active/draft receipts & low stock alerts.
   - Quick action shortcut button: "New Receipt".
3. **Fulfillment Staff Layout (`FULFILLMENT_STAFF`)**:
   - KPIs: Orders to Pick (`RESERVED`), Picking (`PICKING`), Ready to Pack (`PICKED`), Ready to Ship (`READY_TO_SHIP`).
   - `Needs Attention` queue for pending picks and ready-to-ship orders.

Data calculation logic: Data is queried using TanStack Query hooks for `inventory`, `orders`, `receipts`, and `audit-logs` scoped by the selected warehouse filter.

---

## 9. Receiving Architecture

Components: `src/features/shared/resource-pages.tsx` (`ReceivingPage`, `NewReceiptPage`, `ReceiptDetailPage`)

- **Workflow**:
  1. **Receiving List (`/receiving`)**: Displays receipts filtered by warehouse scope and search text with columns: `Reference`, `Seller`, `Warehouse`, `Units`, `Status`, `Created`.
  2. **New Receipt Form (`/receiving/new`)**:
     - Form Fields: `seller_id` (Select), `warehouse_id` (Select), `tracking_number` (Input), `ticket_number` (Input).
     - Submits payload to `receiptsApi.create()`. On success, navigates to `/receiving/:receiptId`.
  3. **Receipt Workspace (`/receiving/:receiptId`)**:
     - Status: `DRAFT`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.
     - Scanning Form (when open): `Scan UPC` (autofocus text input), `Good` (number input), `Damaged` (number input).
     - Action: Submits `addItem` mutation.
     - Header Action: `Complete receipt` button triggers `receiptsApi.complete()`. Updates inventory automatically.

---

## 10. Inventory Architecture

Component: `src/features/shared/resource-pages.tsx` (`InventoryPage`)

- **Table Columns**: `Product` (Name + SKU), `Seller`, `Warehouse`, `On hand`, `Reserved`, `Available`, `Damaged`, `Actions`.
- **Filters**: Text search (matches Product Name, SKU, UPC, Seller Name) + global Warehouse Scope dropdown.
- **Stock Adjustment Modal / Inline Form**:
  - Triggered by clicking "Adjust" on any row.
  - Fields: `Quantity (+/-)` (integer input, e.g. `+5` or `-2`), `Reason` (text input).
  - Triggers `inventoryApi.adjust(inventoryId, { delta, reason })`.
  - Automatically invalidates `["inventory"]` query key.

---

## 11. Orders Architecture

Components: `src/features/shared/resource-pages.tsx` (`OrdersPage`, `NewOrderPage`, `OrderDetailPage`)

- **Order Creation (`/orders/new`)**:
  - Fields: `seller_id` (Select), `warehouse_id` (Select), Dynamic line items array (`product_id`, `quantity`).
  - Triggers `ordersApi.create()`.
- **Order Detail View (`/orders/:orderId`)**:
  - Table Columns: `Product`, `SKU`, `Ordered`, `Reserved`, `Picked`.
  - Timeline Component: Displays chronological log of status entries (`status`, `by`, `at`).
  - Shipment Section: Shows shipment details if created, or renders shipment form if status is `PACKED`.

---

## 12. Fulfillment Architecture

Components: `src/features/shared/resource-pages.tsx` (`OrdersPage` in `fulfillmentMode`, `OrderDetailPage`)

- **Fulfillment Queue (`/fulfillment`)**: Displays open orders excluding `NEW`, `SHIPPED`, and `CANCELLED`.
- **State Transition Actions**:
  - `NEW` → Button: **Reserve stock** (`transition("reserve")`) → Status: `RESERVED`
  - `RESERVED` → Button: **Start picking** (`transition("start-picking")`) → Status: `PICKING`
  - `PICKING` → Button: **Complete picking** (`transition("picked")`) → Status: `PICKED`
  - `PICKED` → Button: **Pack order** (`transition("packed")`) → Status: `PACKED`
  - `PACKED` → Render Shipment Form (`carrier`, `tracking_number`, `weight_kg`, `length_cm`, `width_cm`, `height_cm`) → Status: `READY_TO_SHIP`
  - `READY_TO_SHIP` → Button: **Mark shipped** (`transition("ship")`) → Status: `SHIPPED`

---

## 13. Shipment Architecture

Component: `src/features/shared/resource-pages.tsx` (`OrderDetailPage`)

- **Shipment Form Fields**:
  - `carrier` (Text, default `"UPS"`)
  - `tracking_number` (Text)
  - `weight_kg` (Number, default `"1"`)
  - `length_cm` (Number, default `"30"`)
  - `width_cm` (Number, default `"20"`)
  - `height_cm` (Number, default `"15"`)
- Form is rendered when order status reaches `PACKED`. Submitting calls `ordersApi.createShipment()`.

---

## 14. Sellers Architecture

Component: `src/features/shared/resource-pages.tsx` (`SellersPage`)

- Displays table of registered sellers/brands.
- Columns: `Seller` (Name), `Code`, `Email`, `Phone`, `Status`.
- Calls `sellersApi.list()`.

---

## 15. Products Architecture

Component: `src/features/shared/resource-pages.tsx` (`ProductsPage`)

- Displays global product catalog.
- Columns: `Product` (Name), `SKU`, `UPC`, `Seller`, `Status`.
- Filters: Search input matching Product Name, SKU, UPC, and Seller.
- Calls `productsApi.list()`.

---

## 16. Audit Architecture

Component: `src/features/shared/resource-pages.tsx` (`AuditPage`)

- Displays system audit trail for security and operational tracking.
- Columns: `Action`, `Entity` (Reference), `User`, `Warehouse`, `When`.
- Calls `auditApi.list()`.

---

## 17. Users / Warehouse Architecture

- **Users Page (`/users`)**: Displays team members, assigned roles (`OWNER`, `MANAGER`, etc.), email addresses, warehouse access counts, and active status.
- **Warehouse Scope Selector**: Located in `AppTopbar` (`src/components/layout/app-topbar.tsx`). Allows filtering data across "All Warehouses" or specific facilities (Reno / Columbus).

---

## 18. Data Source Classification

| Feature | Current Data Source Module | Underlying Mechanism | Backend Integration Required? |
| :--- | :--- | :--- | :--- |
| **Authentication** | `src/lib/api/auth.ts` | Axios `/v1/auth/*` fallback to `demo.login()` | YES (Point `VITE_API_BASE_URL` to FastAPI) |
| **Current User** | `src/lib/api/auth.ts` | Axios `/v1/auth/me` fallback to `demo.me()` | YES |
| **Warehouses** | `src/lib/api/warehouses.ts` | Axios `/v1/warehouses` fallback to `demo.warehouses()` | YES |
| **Sellers** | `src/lib/api/sellers.ts` | Axios `/v1/sellers` fallback to `demo.sellers()` | YES |
| **Products** | `src/lib/api/products.ts` | Axios `/v1/products` fallback to `demo.products()` | YES |
| **Receiving** | `src/lib/api/receipts.ts` | Axios `/v1/receipts/*` fallback to `demo.receipts()` | YES |
| **Inventory** | `src/lib/api/inventory.ts` | Axios `/v1/inventory/*` fallback to `demo.inventory()` | YES |
| **Orders** | `src/lib/api/orders.ts` | Axios `/v1/orders/*` fallback to `demo.orders()` | YES |
| **Audit Logs** | `src/lib/api/audit.ts` | Axios `/v1/audit-logs` fallback to `demo.auditLogs()` | YES |
| **Users** | `src/lib/api/users.ts` | Axios `/v1/users` fallback to `demo.users()` | YES |

---

## 19. Existing API / HTTP Layer

Centralized API client located at: `src/lib/api/client.ts`

Key mechanics:
```typescript
export const API_BASE_URL = (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "";
export const LIVE_API = API_BASE_URL.length > 0;

export const http = axios.create({
  baseURL: `${API_BASE_URL}/v1`,
  headers: { "Content-Type": "application/json" },
});

http.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

When `VITE_API_BASE_URL` is set (e.g. `http://localhost:8000`), `LIVE_API` becomes `true`, and all service functions automatically bypass `demo-backend.ts` and dispatch live HTTP REST calls to FastAPI.

---

## 20. TypeScript Domain Models

Location: `src/types/index.ts`

Exact definitions:

```typescript
export type Role = "OWNER" | "MANAGER" | "RECEIVING_STAFF" | "FULFILLMENT_STAFF";
export type EntityStatus = "ACTIVE" | "INACTIVE";

export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: Role;
  status: EntityStatus;
  warehouse_ids: string[];
}

export interface Warehouse {
  id: string;
  name: string;
  code: string;
  city: string;
  state: string;
  status: EntityStatus;
}

export interface Seller {
  id: string;
  name: string;
  code: string;
  email: string;
  phone: string;
  status: EntityStatus;
  created_at: string;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  upc: string;
  seller_id: string;
  seller_name: string;
  description?: string | undefined;
  status: EntityStatus;
  created_at: string;
}

export type ReceiptStatus = "DRAFT" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";

export interface ReceiptItem {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  upc: string;
  good_quantity: number;
  damaged_quantity: number;
}

export interface Receipt {
  id: string;
  reference: string;
  seller_id: string;
  seller_name: string;
  warehouse_id: string;
  warehouse_name: string;
  tracking_number?: string | undefined;
  ticket_number?: string | undefined;
  status: ReceiptStatus;
  items: ReceiptItem[];
  created_at: string;
  created_by: string;
}

export interface InventoryRecord {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  upc: string;
  seller_id: string;
  seller_name: string;
  warehouse_id: string;
  warehouse_name: string;
  on_hand: number;
  reserved: number;
  available: number;
  damaged: number;
}

export type MovementType =
  | "RECEIVED"
  | "ADJUSTMENT_INCREASE"
  | "ADJUSTMENT_DECREASE"
  | "RESERVED"
  | "RELEASED"
  | "SHIPPED"
  | "DAMAGED";

export interface Movement {
  id: string;
  inventory_id: string;
  type: MovementType;
  quantity: number;
  before: number;
  after: number;
  reference?: string | undefined;
  performed_by: string;
  reason?: string | undefined;
  created_at: string;
}

export type OrderStatus =
  | "NEW"
  | "RESERVED"
  | "PICKING"
  | "PICKED"
  | "PACKED"
  | "READY_TO_SHIP"
  | "SHIPPED"
  | "CANCELLED";

export interface OrderItem {
  product_id: string;
  product_name: string;
  sku: string;
  ordered_quantity: number;
  reserved_quantity: number;
  picked_quantity: number;
}

export interface Shipment {
  carrier: string;
  tracking_number: string;
  weight_kg: number;
  length_cm: number;
  width_cm: number;
  height_cm: number;
  label_reference?: string | undefined;
}

export interface Order {
  id: string;
  reference: string;
  seller_id: string;
  seller_name: string;
  warehouse_id: string;
  warehouse_name: string;
  status: OrderStatus;
  items: OrderItem[];
  shipment?: Shipment | undefined;
  created_at: string;
  updated_at: string;
  created_by: string;
  timeline: { status: OrderStatus | "CREATED"; at: string; by: string }[];
}

export interface AuditLog {
  id: string;
  action: string;
  entity: string;
  entity_reference: string;
  user_name: string;
  role: Role;
  warehouse_name: string;
  created_at: string;
  details: Record<string, string | number>;
}
```

---

## 21. Environment Variables

Expected frontend environment variable:
- `VITE_API_BASE_URL`: Base HTTP URL for the FastAPI backend (e.g. `http://localhost:8000`). If omitted or empty, frontend automatically runs in demo mode.

---

## 22. Supabase / Lovable Dependencies

- **Supabase**: **NONE** (No `@supabase/supabase-js` or Supabase configuration exists in the codebase).
- **Lovable**:
  - `@lovable.dev/vite-tanstack-config` (Dev dependency used in `vite.config.ts` for Vite plugin orchestration).
  - `src/lib/lovable-error-reporting.ts` (Lightweight helper to forward uncaught React boundary errors to the Lovable editor preview if present).

---

## 23. Build Problems

- **Status**: `PASS`
- **Build Errors**: **0 Errors**.
- **Warnings**: 1 minor Vite warning regarding `inlineDynamicImports` being ignored when code splitting is active (harmless build notice).

---

## 24. Frontend ↔ Backend Mismatch Matrix

| Frontend Feature | Current Frontend Expectation | Existing UI Types/Fields | Current Data Source | Likely FastAPI Backend Mapping | Mismatch / Notes | Integration Complexity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Auth / Login** | `POST /v1/auth/login` | `{ email, password }` → `{ access_token }` | `src/lib/api/auth.ts` | `/v1/auth/login` | None. Perfect match. | `LOW` |
| **Auth / Signup** | `POST /v1/auth/register` | `{ first_name, last_name, email, password }` → `{ access_token }` | `src/lib/api/auth.ts` | `/v1/auth/register` | Backend expects registration payload. Roles assigned server-side. | `LOW` |
| **Current User** | `GET /v1/auth/me` | `User` interface | `src/lib/api/auth.ts` | `/v1/auth/me` | None. Field mapping straightforward. | `LOW` |
| **Warehouses** | `GET /v1/warehouses` | `Warehouse[]` (`id`, `name`, `code`, `city`, `state`, `status`) | `src/lib/api/warehouses.ts` | `/v1/warehouses` | Check if backend returns `city`/`state` or location object. | `LOW` |
| **Sellers** | `GET /v1/sellers`, `POST /v1/sellers` | `Seller[]` (`id`, `name`, `code`, `email`, `phone`, `status`) | `src/lib/api/sellers.ts` | `/v1/sellers` | Check seller code/phone optionality. | `LOW` |
| **Products** | `GET /v1/products`, `POST /v1/products` | `Product[]` (`id`, `name`, `sku`, `upc`, `seller_id`, `seller_name`, `status`) | `src/lib/api/products.ts` | `/v1/products` | Frontend expects `seller_name` in product object or join required. | `MEDIUM` |
| **Receiving / List** | `GET /v1/receipts` | `Receipt[]` (`id`, `reference`, `seller_name`, `warehouse_name`, `status`, `items`) | `src/lib/api/receipts.ts` | `/v1/receipts` | Check receipt status enum names (DRAFT/IN_PROGRESS/COMPLETED). | `MEDIUM` |
| **Receiving / Add Item** | `POST /v1/receipts/{id}/items` | `{ product_id, good_quantity, damaged_quantity }` | `src/lib/api/receipts.ts` | `/v1/receipts/{id}/items` | Frontend accepts UPC string as `product_id` when scanning; API adapter must resolve UPC to `product_id` if backend expects MongoDB ObjectID. | `MEDIUM` |
| **Receiving / Complete** | `POST /v1/receipts/{id}/complete` | `{}` → updated `Receipt` | `src/lib/api/receipts.ts` | `/v1/receipts/{id}/complete` | Verify backend inventory update trigger upon completion. | `LOW` |
| **Inventory / List** | `GET /v1/inventory` | `InventoryRecord[]` (`on_hand`, `reserved`, `available`, `damaged`) | `src/lib/api/inventory.ts` | `/v1/inventory` | Check query parameter names (`warehouse_id`, `seller_id`). | `LOW` |
| **Inventory / Adjust** | `POST /v1/inventory/{id}/adjust` | `{ delta: number, reason: string }` | `src/lib/api/inventory.ts` | `/v1/inventory/{id}/adjust` | Verify delta payload structure vs backend expectation. | `LOW` |
| **Orders / List & Create**| `GET /v1/orders`, `POST /v1/orders` | `Order[]` & `{ seller_id, warehouse_id, items }` | `src/lib/api/orders.ts` | `/v1/orders` | Check status enum mapping (`NEW`, `RESERVED`, `PICKING`, `PICKED`, `PACKED`, `READY_TO_SHIP`, `SHIPPED`, `CANCELLED`). | `MEDIUM` |
| **Orders / Transitions** | `POST /v1/orders/{id}/{action}` | `action` in `["reserve", "start-picking", "picked", "packed", "ship", "cancel"]` | `src/lib/api/orders.ts` | `/v1/orders/{id}/...` or `PATCH /v1/orders/{id}/status` | Frontend currently calls action endpoints (`/reserve`, `/start-picking`). Adapter layer can normalize to backend route structure. | `MEDIUM` |
| **Orders / Shipment** | `POST /v1/orders/{id}/shipment` | `Shipment` (`carrier`, `tracking_number`, `weight_kg`, `length_cm`, `width_cm`, `height_cm`) | `src/lib/api/orders.ts` | `/v1/orders/{id}/shipment` | Verify shipment nested object vs flat fields. | `LOW` |
| **Audit Logs** | `GET /v1/audit-logs` | `AuditLog[]` | `src/lib/api/audit.ts` | `/v1/audit-logs` | Check backend audit log schema fields. | `LOW` |
| **Users** | `GET /v1/users` | `User[]` | `src/lib/api/users.ts` | `/v1/users` | Note: frontend only implements read-only list for users; role assignment is owned by backend. | `LOW` |

---

## 25. Integration Readiness

- **Authentication**: `READY`
- **Current User**: `READY`
- **Warehouses**: `READY`
- **Sellers**: `READY`
- **Products**: `READY`
- **Receiving**: `READY`
- **Inventory**: `READY`
- **Movements**: `READY`
- **Adjustments**: `READY`
- **Orders**: `READY`
- **Fulfillment**: `READY`
- **Shipments**: `READY`
- **Audit**: `READY`
- **Dashboard**: `READY`
- **Users**: `READY`

---

## 26. Recommended Connection Order

For the upcoming integration stage, connect modules in this order:

1. **Authentication** (`authApi.login` & `authApi.signup`)
2. **Current User** (`authApi.getCurrentUser` / `/v1/auth/me`)
3. **Warehouses** (`warehousesApi.list`)
4. **Sellers** (`sellersApi.list` & `create`)
5. **Products** (`productsApi.list`, `getByUpc`, & `create`)
6. **Inventory** (`inventoryApi.list`, `get`, `adjust`, & `movements`)
7. **Receiving** (`receiptsApi.list`, `create`, `addItem`, & `complete`)
8. **Orders** (`ordersApi.list`, `create`, & `get`)
9. **Fulfillment & Transitions** (`ordersApi.transition` & `createShipment`)
10. **Audit Logs** (`auditApi.list`)
11. **Dashboards** (Consolidated verification across all queries)
12. **Users** (`usersApi.list`)

---

## 27. Files That Will Need Modification During Integration

Because Lovable created a modular API service layer under `src/lib/api/`, **only the API adapter functions in `src/lib/api/` will need modification** if backend endpoint paths or payload formats differ slightly from the demo mock.

Primary files for integration adjustments:
- `src/lib/api/auth.ts`
- `src/lib/api/warehouses.ts`
- `src/lib/api/sellers.ts`
- `src/lib/api/products.ts`
- `src/lib/api/receipts.ts`
- `src/lib/api/inventory.ts`
- `src/lib/api/orders.ts`
- `src/lib/api/audit.ts`
- `src/lib/api/users.ts`
- `src/lib/api/client.ts`

---

## 28. Files That Should NOT Need Modification

The visual presentation, components, design system, layout, and routing logic do NOT need to be modified. They are already fully decoupled from backend concerns via TanStack Query and the API abstraction layer:

- All UI components under `src/components/ui/`
- Navigation and layout under `src/components/layout/` (`app-sidebar.tsx`, `app-topbar.tsx`, `brand.tsx`)
- All page components under `src/features/` (`dashboard-page.tsx`, `resource-pages.tsx`, `login-form.tsx`, `signup-form.tsx`)
- All route definitions under `src/routes/`
- Domain types under `src/types/index.ts`
- Theme and warehouse scope providers (`theme.tsx`, `warehouse-scope.tsx`)

---

## 29. Questions / Unknowns

1. **UPC vs Product ID in Scanning**: During receipt item scanning, frontend users input a UPC string. The frontend API module currently passes this string as `product_id`. We should verify whether the FastAPI `/v1/receipts/{id}/items` endpoint resolves UPCs server-side or expects the database `product_id`.
2. **Order Transition Endpoints**: The frontend service calls `POST /v1/orders/{order_id}/{action}` (where action is `reserve`, `start-picking`, etc.). We need to verify whether backend implements distinct action endpoints or a unified `PATCH /v1/orders/{order_id}/status` route.
