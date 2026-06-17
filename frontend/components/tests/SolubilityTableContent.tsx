import {
  METAL_ACTIVITY_SERIES,
  SOLUBILITY_ANIONS,
  SOLUBILITY_CATIONS,
  SOLUBILITY_LEGEND,
  SOLUBILITY_MATRIX,
  type SolubilityCode,
} from "@/lib/chemistry/solubility-table";

const CELL_CLASS: Record<SolubilityCode, string> = {
  Р: "chem-solubility-p",
  М: "chem-solubility-m",
  Н: "chem-solubility-n",
  "—": "chem-solubility-d",
  "?": "chem-solubility-q",
};

export function SolubilityTableContent() {
  return (
    <div className="space-y-6 p-3 sm:p-4">
      <div>
        <h3 className="text-center text-xs font-semibold uppercase tracking-wide text-chem-teal sm:text-sm">
          Растворимость кислот, солей и оснований в воде
        </h3>

        <div className="mt-3 overflow-x-auto rounded-lg border border-chem-teal-soft">
          <table className="min-w-[56rem] border-collapse text-[10px] sm:text-xs">
            <thead>
              <tr>
                <th
                  scope="col"
                  className="sticky left-0 z-20 border border-chem-teal-soft bg-chem-teal-dark px-2 py-2 text-left font-semibold text-white"
                >
                  Анионы ↓ / Катионы →
                </th>
                {SOLUBILITY_CATIONS.map((cation) => (
                  <th
                    key={cation}
                    scope="col"
                    className="border border-chem-teal-soft bg-chem-teal px-1.5 py-2 text-center font-semibold whitespace-nowrap text-white"
                  >
                    {cation}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SOLUBILITY_ANIONS.map((anion, rowIndex) => (
                <tr key={anion}>
                  <th
                    scope="row"
                    className="sticky left-0 z-10 border border-chem-teal-soft bg-chem-teal-soft px-2 py-1.5 text-left font-semibold whitespace-nowrap text-chem-teal-dark"
                  >
                    {anion}
                  </th>
                  {SOLUBILITY_MATRIX[rowIndex].map((code, colIndex) => (
                    <td
                      key={`${anion}-${SOLUBILITY_CATIONS[colIndex]}`}
                      className={`border border-chem-teal-soft/60 px-1 py-1 text-center font-medium ${CELL_CLASS[code]}`}
                      title={SOLUBILITY_LEGEND.find((item) => item.code === code)?.title}
                    >
                      {code}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {SOLUBILITY_LEGEND.map((item) => (
            <li
              key={item.code}
              className={`flex items-start gap-2 rounded-md px-2 py-1.5 text-xs ${CELL_CLASS[item.code]}`}
            >
              <span className="min-w-[1.25rem] text-center font-bold">
                {item.code}
              </span>
              <span>
                <span className="font-semibold">{item.title}</span>
                <span className="text-zinc-600"> — {item.description}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-lg border border-chem-teal-soft bg-chem-surface-muted px-3 py-4 sm:px-4">
        <h3 className="text-center text-xs font-semibold uppercase tracking-wide text-chem-teal sm:text-sm">
          Ряд активности металлов / электрохимический ряд напряжений
        </h3>
        <div className="mt-3 overflow-x-auto">
          <div className="flex min-w-max flex-wrap justify-center gap-1.5 sm:gap-2">
            {METAL_ACTIVITY_SERIES.map((metal) => (
              <span
                key={metal}
                className={`rounded-md px-2 py-1 text-xs font-semibold sm:text-sm ${
                  metal === "(H₂)"
                    ? "bg-chem-band text-chem-teal-dark"
                    : "bg-white text-chem-navy shadow-sm"
                }`}
              >
                {metal}
              </span>
            ))}
          </div>
        </div>
        <p className="mt-3 text-center text-xs text-zinc-600">
          ← активность металлов уменьшается
        </p>
      </div>
    </div>
  );
}
