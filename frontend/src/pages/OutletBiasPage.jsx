import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const OutletBiasPage = () => {
  return (
    <div className="w-full max-w-5xl mx-auto p-4">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="checkmate-gradient text-3xl">
            News Outlet Bias Comparison
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-gray-700">
            Compare different news outlets across fact-checking, sentiment, emotion analysis and propaganda analysis.
          </p>

          {/* Example layout skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border rounded-lg p-3">
              <h3 className="font-semibold mb-2">Outlet A</h3>
              {/* Replace with your article card / fetch UI */}
              <p className="text-xs text-gray-600">
                Work in progress!
              </p>
            </div>
            <div className="border rounded-lg p-3">
              <h3 className="font-semibold mb-2">Outlet B</h3>
              <p className="text-xs text-gray-600">
                Work in progress!
              </p>
            </div>
          </div>

          <div className="border rounded-lg p-3 bg-gray-50">
            <h3 className="font-semibold mb-2">Bias Insights</h3>
            <p className="text-xs text-gray-600">
                Work in progress!
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OutletBiasPage;
