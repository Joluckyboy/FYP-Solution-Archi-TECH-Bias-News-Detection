import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const DEFAULT_COLORS = {
  Left: "#2563eb",
  Center: "#64748b",
  Right: "#ef4444",
};

const BiasByOutletStackedBar = ({ outlets, biasLabels, topN = 10 }) => {
  const data = useMemo(() => {
    const rows = (outlets || []).map((o) => {
      const row = { outlet: o.outlet };
      for (const label of biasLabels || ["Left", "Center", "Right"]) {
        row[label] = Number(o.biasCounts?.[label] || 0);
      }
      row.total = Number(o.totalArticles || 0);
      return row;
    });

    rows.sort((a, b) => b.total - a.total);
    return rows.slice(0, topN);
  }, [outlets, biasLabels, topN]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Bias Distribution by Outlet (Top {topN})</CardTitle>
      </CardHeader>
      <CardContent className="h-[360px]">
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground">No data to display.</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 10, right: 10, left: 0, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="outlet"
                interval={0}
                angle={-35}
                textAnchor="end"
                height={80}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              {(biasLabels || ["Left", "Center", "Right"]).map((label) => (
                <Bar
                  key={label}
                  dataKey={label}
                  stackId="bias"
                  fill={DEFAULT_COLORS[label] || "#8884d8"}
                  isAnimationActive={false}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};

export default BiasByOutletStackedBar;
