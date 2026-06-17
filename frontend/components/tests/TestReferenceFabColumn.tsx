import { PeriodicTableOverlay } from "@/components/tests/PeriodicTableOverlay";
import { SolubilityTableOverlay } from "@/components/tests/SolubilityTableOverlay";

/** Плавающие справочники на экране активной тест-сессии (SPEC §1.3.3 + растворимость). */
export function TestReferenceFabColumn() {
  return (
    <div className="fixed bottom-52 left-4 z-40 flex w-[min(100vw-2rem,16rem)] flex-col gap-2 sm:bottom-6 sm:left-6 sm:w-auto">
      <SolubilityTableOverlay />
      <PeriodicTableOverlay />
    </div>
  );
}
