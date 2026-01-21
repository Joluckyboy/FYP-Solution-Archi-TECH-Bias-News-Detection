import axios from "axios";
import { useEffect, useMemo, useState } from "react";
import get_api from "@/config/config";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { HashLoader } from "react-spinners";

import DashboardFilters from "@/components/dashboard/DashboardFilters";
import KpiCards from "@/components/dashboard/KpiCards";
import BiasByOutletStackedBar from "@/components/dashboard/BiasByOutletStackedBar";
import OverallBiasPie from "@/components/dashboard/OverallBiasPie";

const DashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [data, setData] = useState(null);

  // Filters (Sprint 1 MVP)
  const [country, setCountry] = useState("ALL");
  const [outlet, setOutlet] = useState("ALL");

  useEffect(() => {
    const run = async () => {
      try {
        setLoading(true);
        setErrorMsg("");
        const api = await get_api();
        const res = await axios.get(`${api}/application/bias_dashboard`);
        setData(res.data);
      } catch (e) {
        const msg =
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load dashboard data";
        setErrorMsg(String(msg));
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  const countries = useMemo(() => {
    const list = data?.outlets?.map((o) => o.country) || [];
    const uniq = Array.from(new Set(list)).sort((a, b) => a.localeCompare(b));
    return ["ALL", ...uniq];
  }, [data]);

  const outlets = useMemo(() => {
    const list = data?.outlets?.map((o) => o.outlet) || [];
    const uniq = Array.from(new Set(list)).sort((a, b) => a.localeCompare(b));
    return ["ALL", ...uniq];
  }, [data]);

  const filteredOutlets = useMemo(() => {
    if (!data?.outlets) return [];
    return data.outlets.filter((o) => {
      if (country !== "ALL" && o.country !== country) return false;
      if (outlet !== "ALL" && o.outlet !== outlet) return false;
      return true;
    });
  }, [data, country, outlet]);

  const derivedKpis = useMemo(() => {
    const biasLabels = data?.biasLabels || ["Left", "Center", "Right"];
    const biasTotals = Object.fromEntries(biasLabels.map((l) => [l, 0]));
    let totalArticles = 0;
    const countriesSet = new Set();

    for (const o of filteredOutlets) {
      totalArticles += Number(o.totalArticles || 0);
      countriesSet.add(o.country);
      for (const label of biasLabels) {
        biasTotals[label] += Number(o.biasCounts?.[label] || 0);
      }
    }

    return {
      totalArticles,
      totalOutlets: filteredOutlets.length,
      countriesCovered: countriesSet.size,
      biasTotals,
      biasLabels,
    };
  }, [data, filteredOutlets]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <HashLoader />
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="max-w-5xl mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Dashboard failed to load</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-600">{errorMsg}</p>
            <p className="text-sm text-muted-foreground mt-2">
              Make sure your FastAPI application service is running on port 8010
              and the dataset file exists under <code>datasets/</code>.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold">Global Bias Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Aggregated bias insights across international news outlets (Sprint 1 MVP)
          </p>
        </div>

        <DashboardFilters
          countries={countries}
          outlets={outlets}
          country={country}
          outlet={outlet}
          setCountry={setCountry}
          setOutlet={setOutlet}
          onReset={() => {
            setCountry("ALL");
            setOutlet("ALL");
          }}
        />
      </div>

      <KpiCards kpis={derivedKpis} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BiasByOutletStackedBar
          outlets={filteredOutlets}
          biasLabels={derivedKpis.biasLabels}
          topN={10}
        />
        <OverallBiasPie
          biasTotals={derivedKpis.biasTotals}
          biasLabels={derivedKpis.biasLabels}
        />
      </div>
    </div>
  );
};

export default DashboardPage;
