import { Suspense } from "react";

import { LeadForm } from "@/components/marketing/LeadForm";

function FormFallback() {
  return (
    <div className="chem-card rounded-xl p-6 text-center text-sm text-zinc-500">
      Загрузка формы…
    </div>
  );
}

export function LeadFormSection({
  sourcePage,
  formId,
  showSocialLinks = true,
}: {
  sourcePage: string;
  formId?: string;
  showSocialLinks?: boolean;
}) {
  return (
    <Suspense fallback={<FormFallback />}>
      <LeadForm
        sourcePage={sourcePage}
        formId={formId}
        showSocialLinks={showSocialLinks}
      />
    </Suspense>
  );
}
