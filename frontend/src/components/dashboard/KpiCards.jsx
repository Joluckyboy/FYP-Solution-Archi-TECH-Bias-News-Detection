import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const fmt = (n) => {
  const x = Number(n || 0);
  return x.toLocaleString();
};

const BiasPills = ({ biasTotals, biasLabels }) => {
  return (
    <div className="flex gap-2 flex-wrap">
      {biasLabels.map((l) => (
        <span
          key={l}
          className="px-2 py-1 rounded-full text-xs bg-muted text-muted-foreground"
          title={`${l} articles`}
        >
          {l}: {fmt(biasTotals?.[l] || 0)}
        </span>
      ))}
    </div>
  );
};

const KpiCards = ({ kpis }) => {
  const {
    totalArticles,
    totalOutlets,
    countriesCovered,
    biasTotals,
    biasLabels,
  } = kpis || {};

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Articles
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-semibold">{fmt(totalArticles)}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            News Outlets
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-semibold">{fmt(totalOutlets)}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Countries Covered
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-semibold">{fmt(countriesCovered)}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Bias Distribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <BiasPills
            biasTotals={biasTotals}
            biasLabels={biasLabels || ["Left", "Center", "Right"]}
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default KpiCards;
