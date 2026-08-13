import type { ReactNode } from "react";
import { BrandMark } from "@/components/layout/brand";

/** Two-panel auth composition: grainy atmosphere panel + form panel. */
export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      <section className="atmosphere relative hidden flex-col justify-between overflow-hidden p-12 lg:flex">
        <div className="grain-overlay" aria-hidden />
        <div className="relative flex items-center gap-2.5 text-white">
          <BrandMark />
          <span className="text-sm font-semibold tracking-tight">Whitfield Fulfillment</span>
        </div>

        <div className="relative max-w-lg">
          <h2 className="text-[42px] leading-[1.08] font-semibold tracking-tight text-white">
            Operations,
            <br />
            without the spreadsheet chaos.
          </h2>
          <p className="mt-5 max-w-md text-[15px] leading-relaxed text-white/70">
            Receive, reserve, fulfill and trace inventory across every warehouse from one workspace.
          </p>

          <div className="mt-10 grid max-w-md grid-cols-2 gap-3">
            {[
              { name: "Reno", detail: "Nevada" },
              { name: "Columbus", detail: "Ohio" },
            ].map((w) => (
              <div
                key={w.name}
                className="rounded-2xl border border-white/10 bg-white/[0.06] p-4 backdrop-blur-md"
              >
                <p className="text-sm font-medium text-white">{w.name}</p>
                <p className="mt-0.5 text-xs text-white/55">{w.detail}</p>
                <p className="mt-3 flex items-center gap-1.5 text-[11px] text-white/60">
                  <span className="size-1.5 rounded-full bg-emerald-400" aria-hidden />
                  Operational
                </p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-xs text-white/40">
          Audited, role-aware warehouse management for multi-seller fulfillment.
        </p>
      </section>

      <section className="flex items-center justify-center px-5 py-12 sm:px-10">
        <div className="w-full max-w-[400px]">{children}</div>
      </section>
    </div>
  );
}
