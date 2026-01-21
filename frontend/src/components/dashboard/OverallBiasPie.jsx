import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Tooltip, Legend, ResponsiveContainer } from "recharts";

const DEFAULT_COLORS = {
  Left: "#2563eb",
  Center: "#64748b",
  Right: "#ef4444",
};

const OverallBiasPie = ({ biasTotals, biasLabels }) => {
  const data = useMemo(() => {
    return (biasLabels || ["Left", "Center", "Right"]).map((l) => ({
      name: l,
      value: Number(biasTotals?.[l] || 0),
      fill: DEFAULT_COLORS[l] || "#8884d8",
    }));
  }, [biasTotals, biasLabels]);

  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Overall Bias Share</CardTitle>
      </CardHeader>
      <CardContent className="h-[360px]">
        {total === 0 ? (
          <p className="text-sm text-muted-foreground">No data to display.</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                outerRadius={120}
                label={(entry) => `${entry.name}`}
                isAnimationActive={false}
              />
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};

export default OverallBiasPie;
